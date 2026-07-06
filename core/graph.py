"""LangGraph state graph for multi-agent disposal workflow.

State machine:
  START -> supervisor_judge -> event_analysis -> regulation_search
       -> [conditional: HIGH -> emergency_linkage] -> dispatch_order
       -> final_summary -> END
"""

from __future__ import annotations

import json
import logging
logger = logging.getLogger(__name__)
import uuid
from datetime import datetime
from typing import TypedDict

from core.agents import (
    supervisor_validate,
    run_analysis,
    run_regulation_search,
    run_dispatch,
    run_final_summary,
)
from core.db import insert_work_order, insert_disposal_log
from core.mock import send_wechat_notification, emergency_linkage_mock


# ===========================================================================
# State definition
# ===========================================================================

class DisposalState(TypedDict, total=False):
    alarm_data: dict
    supervisor_result: dict
    analysis: str
    regulations: dict
    dispatch_result: str
    emergency_result: str
    final_report: str
    order_id: str
    notification_sent: bool
    current_step: str
    error_msg: str
    steps_log: list[dict]


def _log_step(state: DisposalState, step_name: str, content: str) -> None:
    """Record a step in the disposal log."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state.setdefault("steps_log", []).append({
        "step": step_name,
        "content": content[:500],
        "timestamp": ts,
    })
    state["current_step"] = step_name

    event_id = state.get("alarm_data", {}).get("event_id", "unknown")
    try:
        insert_disposal_log(event_id, step_name, content[:1000], ts)
    except Exception:
        pass  # DB write failure is non-fatal


# ===========================================================================
# Node functions
# ===========================================================================

def supervisor_judge(state: DisposalState) -> DisposalState:
    """Validate input and decide routing."""
    alarm_data = state.get("alarm_data", {})
    result = supervisor_validate(alarm_data)
    state["supervisor_result"] = result

    if not result["valid"]:
        state["error_msg"] = result["summary_instruction"]
        state["final_report"] = f"## 处置失败\n\n**原因**：{result['summary_instruction']}"
        _log_step(state, "supervisor_judge", f"校验失败: {result['missing_fields']}")
        return state

    _log_step(state, "supervisor_judge",
              f"校验通过，等级={result['alarm_level']}，路由={result['route']}")
    return state


def event_analysis(state: DisposalState) -> DisposalState:
    """Run event analysis."""
    if state.get("error_msg"):
        return state

    alarm_data = state.get("alarm_data", {})
    analysis = run_analysis(alarm_data)
    state["analysis"] = analysis
    _log_step(state, "event_analysis", analysis[:200])
    return state


def regulation_search(state: DisposalState) -> DisposalState:
    """Search knowledge base for matching regulations."""
    if state.get("error_msg"):
        return state

    alarm_data = state.get("alarm_data", {})
    regulations = run_regulation_search(alarm_data)
    state["regulations"] = regulations
    source_count = len(regulations.get("source_files", []))
    _log_step(state, "regulation_search",
              f"检索完成，匹配 {source_count} 个来源: {regulations.get('source_files', [])}")
    return state


def emergency_linkage(state: DisposalState) -> DisposalState:
    """Mock emergency linkage (only for HIGH level)."""
    if state.get("error_msg"):
        return state

    alarm_data = state.get("alarm_data", {})
    result = emergency_linkage_mock(alarm_data)
    state["emergency_result"] = result
    _log_step(state, "emergency_linkage", f"紧急联动完成: {result}")
    return state


def dispatch_order(state: DisposalState) -> DisposalState:
    """Generate dispatch instructions, push notification, write work order."""
    if state.get("error_msg"):
        return state

    alarm_data = state.get("alarm_data", {})
    analysis = state.get("analysis", "")
    regulations = state.get("regulations", {})

    # Generate dispatch instructions
    dispatch = run_dispatch(alarm_data, analysis, regulations)
    state["dispatch_result"] = dispatch

    # Generate work order ID
    order_id = f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    state["order_id"] = order_id

    # Push WeChat notification
    event_type = alarm_data.get("event_type", "unknown")
    alarm_level = alarm_data.get("alarm_level", "LOW")
    location = alarm_data.get("location", "未知位置")
    analysis_short = analysis[:200] if analysis else "无分析数据"

    notification_sent = send_wechat_notification(
        event_type=event_type,
        alarm_level=alarm_level,
        location=location,
        summary=analysis_short,
    )
    state["notification_sent"] = notification_sent

    # Write work order to database
    try:
        insert_work_order(
            order_id=order_id,
            event_id=alarm_data.get("event_id", "unknown"),
            event_type=event_type,
            alarm_level=alarm_level,
            location=location,
            analysis=analysis,
            regulations=json.dumps(regulations.get("source_files", []), ensure_ascii=False),
            dispatch=dispatch,
            final_report="",  # Will be updated after final_summary
            status="dispatched",
        )
    except Exception as e:
        _log_step(state, "dispatch_order", f"工单写入失败(非致命): {e}")

    _log_step(state, "dispatch_order",
              f"派发完成, 工单={order_id}, 通知={'已发送' if notification_sent else '未发送'}")
    return state


def final_summary(state: DisposalState) -> DisposalState:
    """Generate final disposal report."""
    if state.get("error_msg"):
        return state

    alarm_data = state.get("alarm_data", {})
    analysis = state.get("analysis", "")
    regulations = state.get("regulations", {})
    dispatch = state.get("dispatch_result", "")
    order_id = state.get("order_id", "N/A")
    notification_sent = state.get("notification_sent", False)

    report = run_final_summary(
        alarm_data=alarm_data,
        analysis=analysis,
        regulations=regulations,
        dispatch=dispatch,
        order_id=order_id,
        notification_sent=notification_sent,
    )
    state["final_report"] = report

    # Update work order with final report
    if order_id and order_id != "N/A":
        try:
            from core.db import _get_conn
            conn = _get_conn()
            conn.execute(
                "UPDATE work_order SET final_report = ?, status = 'completed' WHERE order_id = ?",
                (report, order_id),
            )
            conn.commit()
        except Exception:
            pass

    _log_step(state, "final_summary", "处置报告生成完成")
    return state


# ===========================================================================
# Conditional edge: should we run emergency linkage?
# ===========================================================================

def should_emergency_linkage(state: DisposalState) -> str:
    """Decide whether to route to emergency_linkage based on alarm_level."""
    if state.get("error_msg"):
        return "final_summary"

    alarm_level = state.get("alarm_data", {}).get("alarm_level", "LOW").upper()
    if alarm_level == "HIGH":
        return "emergency_linkage"
    return "dispatch_order"


def should_skip_on_error(state: DisposalState) -> str:
    """If error_msg is set, skip to final_summary."""
    if state.get("error_msg"):
        return "final_summary"
    return "continue"


# ===========================================================================
# Main entry point: run the disposal workflow
# ===========================================================================

def run_disposal(alarm_json: dict | str) -> dict:
    """Execute the full multi-agent disposal workflow.

    Args:
        alarm_json: Alarm JSON dict or JSON string.

    Returns:
        dict with keys:
            - report:       str   (Markdown final report)
            - order_id:     str   (work order ID)
            - steps:        list  (step-by-step log)
            - notification: bool  (whether WeChat was pushed)
            - error:        str   (error message if any)
    """
    # Parse input if string
    if isinstance(alarm_json, str):
        try:
            alarm_data = json.loads(alarm_json)
        except json.JSONDecodeError as e:
            return {
                "report": f"## JSON解析失败\n\n**错误**: {e}",
                "order_id": "",
                "steps": [],
                "notification": False,
                "error": str(e),
            }
    else:
        alarm_data = alarm_json

    # Initialize state
    state: DisposalState = {
        "alarm_data": alarm_data,
        "supervisor_result": {},
        "analysis": "",
        "regulations": {},
        "dispatch_result": "",
        "emergency_result": "",
        "final_report": "",
        "order_id": "",
        "notification_sent": False,
        "current_step": "start",
        "error_msg": "",
        "steps_log": [],
    }

    # Execute the pipeline step by step
    # Step 1: Supervisor
    state = supervisor_judge(state)
    if state.get("error_msg"):
        return _build_result(state)

    # Step 2: Event Analysis
    state = event_analysis(state)

    # Step 3: Regulation Search
    state = regulation_search(state)

    # Step 4: Emergency Linkage (only HIGH)
    if state["alarm_data"].get("alarm_level", "").upper() == "HIGH":
        state = emergency_linkage(state)

    # Step 5: Dispatch
    state = dispatch_order(state)

    # Step 6: Final Summary
    state = final_summary(state)

    return _build_result(state)


def _build_result(state: DisposalState) -> dict:
    """Build the final result dict from state."""
    return {
        "report": state.get("final_report", ""),
        "order_id": state.get("order_id", ""),
        "steps": state.get("steps_log", []),
        "notification": state.get("notification_sent", False),
        "error": state.get("error_msg", ""),
    }

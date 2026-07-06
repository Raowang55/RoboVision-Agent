"""Multi-Agent system prompts and LLM call wrappers.

Agents:
  1. SupervisorAgent  – validate input, route by alarm_level, aggregate final report
  2. AnalysisAgent    – profile the event (no disposal advice)
  3. RegulationAgent  – search knowledge base for matching SOPs
  4. DispatchAgent    – generate role-based instructions, push WeChat, write DB

All agents use the existing `app.llm.deepseek_client.chat()` interface.
"""

from __future__ import annotations

import json
from app.llm.deepseek_client import chat


# ===========================================================================
# 1. Supervisor Agent
# ===========================================================================

SUPERVISOR_SYSTEM = """你是工业安全事件处置的调度主管（Supervisor Agent）。

你的职责：
1. 校验输入报警JSON的必填字段：event_id, event_type, alarm_level
2. 根据 alarm_level 决定处置流程等级
3. 汇总后续各Agent的输出，生成最终的处置报告

调度规则：
- HIGH   → 全面处置：事件分析 → 预案检索 → 紧急联动 → 指令派发 → 最终报告
- MEDIUM → 标准处置：事件分析 → 预案检索 → 指令派发 → 最终报告
- LOW    → 简化处置：事件分析 → 指令派发 → 最终报告

输出格式（严格JSON）：
{
  "valid": true/false,
  "missing_fields": ["field1", "field2"],
  "alarm_level": "HIGH/MEDIUM/LOW",
  "route": "full/standard/simplified",
  "summary_instruction": "一句话处置指引"
}

如字段缺失，valid=false，直接返回 missing_fields，不进入后续流程。"""


def supervisor_validate(alarm_data: dict, previous_results: dict | None = None) -> dict:
    """Validate alarm JSON and decide routing.

    Returns dict with keys: valid, missing_fields, alarm_level, route, summary_instruction.
    """
    required = ["event_id", "event_type", "alarm_level"]
    missing = [f for f in required if f not in alarm_data or not alarm_data[f]]

    if missing:
        return {
            "valid": False,
            "missing_fields": missing,
            "alarm_level": alarm_data.get("alarm_level", "UNKNOWN"),
            "route": "none",
            "summary_instruction": f"输入JSON缺少必填字段: {', '.join(missing)}",
        }

    level = alarm_data.get("alarm_level", "LOW").upper()
    if level == "HIGH":
        route = "full"
    elif level == "MEDIUM":
        route = "standard"
    else:
        route = "simplified"

    # Build context-aware summary from available data
    location = alarm_data.get("location", "未知位置")
    event_type = alarm_data.get("event_type", "unknown")
    summary = f"{location} 发生 {event_type} 事件，等级 {level}，启动{route}处置流程"

    return {
        "valid": True,
        "missing_fields": [],
        "alarm_level": level,
        "route": route,
        "summary_instruction": summary,
    }


# ===========================================================================
# 2. Event Analysis Agent
# ===========================================================================

ANALYSIS_SYSTEM = """你是工业安全事件分析专家（Analysis Agent）。

你的唯一职责是对报警事件进行画像分析，**禁止给出任何处置方案或建议**。

分析维度（必须全部覆盖）：
1. 事件概况（1句话描述）
2. 风险等级确认（基于 alarm_level 和 confidence）
3. 影响范围评估（结合 location、bbox 位置推导）
4. 周边危险源提示（结合 event_type 推导，如火灾→易燃物、电气设备）

约束：
- 必须基于输入JSON中的实际字段推导，禁止编造不存在的信息
- 如果 location 为"未知位置"，则标注"位置信息缺失，影响范围无法精确评估"
- bbox 坐标仅用于说明检测目标在画面中的位置，不用于计算实际距离

输出格式（纯文本，中文，分点但不使用markdown标题）：
事件概况：...
风险等级：...
影响范围：...
危险源提示：..."""


def run_analysis(alarm_data: dict) -> str:
    """Run event analysis via LLM. Returns analysis text."""
    user_content = json.dumps(alarm_data, ensure_ascii=False, indent=2)

    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM},
        {"role": "user", "content": f"请分析以下报警事件：\n```json\n{user_content}\n```"},
    ]

    result = chat(messages, temperature=0.2, max_tokens=800)
    if result["success"]:
        return result["content"]
    return f"[分析失败] {result.get('error', '未知错误')}\n\n基于原始数据：{alarm_data.get('event_type', '?')} @ {alarm_data.get('location', '?')}，等级 {alarm_data.get('alarm_level', '?')}"


# ===========================================================================
# 3. Regulation Search Agent
# ===========================================================================

REGULATION_SEARCH_PROMPT_TEMPLATE = "{location} {event_type} {alarm_level} 处置预案 安全规范"


def run_regulation_search(alarm_data: dict, top_k: int = 3) -> dict:
    """Search knowledge base for matching regulations.

    Returns dict with keys: query, results (list), source_files (list).
    """
    from app.rag.rag_tool import rag_query

    location = alarm_data.get("location", "")
    event_type = alarm_data.get("event_type", "unknown")
    alarm_level = alarm_data.get("alarm_level", "LOW")

    query = REGULATION_SEARCH_PROMPT_TEMPLATE.format(
        location=location,
        event_type=event_type,
        alarm_level=alarm_level,
    )

    try:
        result = rag_query(query, top_k=top_k, use_llm=False)
    except Exception as e:
        print(f'  [RAG] Search failed (non-fatal): {e}')
        result = {'retrieved_chunks': [], 'source_files': [], 'answer': ''}

    return {
        "query": query,
        "results": result.get("retrieved_chunks", []),
        "source_files": result.get("source_files", []),
        "answer": result.get("answer", ""),
    }


# ===========================================================================
# 4. Dispatch Agent
# ===========================================================================

DISPATCH_SYSTEM = """你是工业安全事件指令派发专家（Dispatch Agent）。

你的职责：
1. 基于事件分析结果和预案，生成面向不同角色的执行指令
2. 每条指令必须包含：执行对象（角色）、具体动作、优先级、完成时限

四个固定派发角色：
- 现场安全员：负责现场确认、人员疏散、初期处置
- 值班经理：负责协调资源、上报情况、启动应急预案
- 消防中控室：负责监控联动、报警确认、消防系统操作
- 对应生产班组：负责停工检查、设备断电、配合处置

输出格式（纯文本，中文）：
【现场安全员】动作内容 | 优先级：高/中/低 | 时限：X分钟
【值班经理】动作内容 | 优先级：高/中/低 | 时限：X分钟
【消防中控室】动作内容 | 优先级：高/中/低 | 时限：X分钟
【生产班组】动作内容 | 优先级：高/中/低 | 时限：X分钟

约束：
- 优先级必须与 alarm_level 对应：HIGH→高，MEDIUM→中，LOW→低
- 时限必须合理：HIGH→5分钟，MEDIUM→15分钟，LOW→30分钟
- 如果事件类型为 fire/smoke，消防中控室指令必须包含"确认火警并启动消防联动"
- 如果事件类型为 no_helmet/no_vest，现场安全员指令必须包含"责令违规人员立即整改" """


def run_dispatch(alarm_data: dict, analysis: str, regulations: dict) -> str:
    """Generate dispatch instructions via LLM. Returns dispatch text."""
    reg_text = ""
    if regulations.get("results"):
        chunks = regulations["results"][:3]
        reg_text = "\n".join(
            f"[{c.get('source', '?')}] {c.get('text', '')[:200]}"
            for c in chunks
        )

    user_content = f"""事件信息：
{json.dumps(alarm_data, ensure_ascii=False, indent=2)}

事件分析：
{analysis}

匹配预案：
{reg_text or '（无匹配预案）'}

请生成派发指令。"""

    messages = [
        {"role": "system", "content": DISPATCH_SYSTEM},
        {"role": "user", "content": user_content},
    ]

    result = chat(messages, temperature=0.2, max_tokens=1000)
    if result["success"]:
        return result["content"]
    return f"[派发失败] {result.get('error', '未知错误')}"


# ===========================================================================
# 5. Final Summary (called by Supervisor)
# ===========================================================================

SUMMARY_SYSTEM = """你是工业安全事件处置报告生成专家。

基于以下各Agent的输出，生成一份结构化的最终处置报告。

报告格式（Markdown）：

## 事件处置报告
**事件ID**：{event_id}
**时间**：{timestamp}
**地点**：{location}
**等级**：{alarm_level}

### 事件分析
{analysis_summary}

### 匹配预案
{regulation_summary}

### 派发指令
{dispatch_instructions}

### 处置状态
- 工单ID：{order_id}
- 通知状态：{notification_status}
- 生成时间：{report_time}
"""


def run_final_summary(
    alarm_data: dict,
    analysis: str,
    regulations: dict,
    dispatch: str,
    order_id: str,
    notification_sent: bool,
) -> str:
    """Generate final Markdown disposal report."""
    from datetime import datetime

    event_id = alarm_data.get("event_id", "N/A")
    timestamp = alarm_data.get("timestamp", "N/A")
    location = alarm_data.get("location", "未知")
    alarm_level = alarm_data.get("alarm_level", "N/A")

    # Truncate analysis for summary
    analysis_short = analysis[:300] + ("..." if len(analysis) > 300 else "")

    # Regulation summary
    sources = regulations.get("source_files", [])
    reg_summary = ", ".join(sources[:3]) if sources else "无匹配预案"

    # Notification status
    notif_status = "已推送" if notification_sent else "未推送（Mock模式/推送失败）"

    report = f"""## 事件处置报告

**事件ID**：{event_id}
**时间**：{timestamp}
**地点**：{location}
**等级**：{alarm_level}

### 事件分析
{analysis_short}

### 匹配预案
{reg_summary}

### 派发指令
{dispatch}

### 处置状态
- 工单ID：{order_id}
- 通知状态：{notif_status}
- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    return report

# -*- coding: utf-8 -*-
"""Shared agent helpers used by agent.py and dispatch.py.

Contains image saving and result formatting utilities that are
imported by both modules, avoiding circular dependencies.
"""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.utils.file_utils import get_output_path


def save_numpy_as_rgb(image: np.ndarray) -> str:
    """Save a Gradio RGB numpy image to a temp file and return the path."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = "data/outputs"
    path = get_output_path(prefix=f"input_{ts}", ext=".jpg", directory=out_dir)
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), bgr)
    return str(path)


def format_agent_result(output: dict) -> str:
    """Turn agent output dict into a Markdown summary string.

    Args:
        output: dict with keys intent, error, result.

    Returns:
        Markdown-formatted summary string.
    """
    intent = output.get("intent", "unknown")
    error = output.get("error", "")
    result = output.get("result", {})

    if error:
        return f"**Error**: {error}"

    lines = [f"**Intent**: {intent}"]

    if intent == "object_detection":
        det = result.get("detection", {})
        count = det.get("total_detections", 0)
        lines.append(f"- 检测到 **{count}** 个目标")
        classes = det.get("class_counts", {})
        if classes:
            for cls, cnt in classes.items():
                lines.append(f"  - {cls}: {cnt}")

    elif intent == "fire_alarm":
        det = result.get("detection", {})
        count = det.get("total_detections", 0)
        lines.append(f"- 火灾预警检测到 **{count}** 个目标")
        if result.get("alarm_level"):
            lines.append(f"- 报警等级: **{result['alarm_level']}**")

    elif intent == "ppe_check":
        det = result.get("detection", {})
        count = det.get("total_detections", 0)
        lines.append(f"- PPE 检测到 **{count}** 个目标")
        violations = result.get("violations", [])
        if violations:
            lines.append(f"- 违规项: {', '.join(violations)}")

    elif intent == "inspection_report":
        if result.get("report"):
            lines.append("- 报告已生成")
            lines.append(f"  - 路径: {result.get('report_path', '')}")

    elif intent == "event_log":
        logs = result.get("logs", [])
        lines.append(f"- 查询到 **{len(logs)}** 条日志")

    elif intent == "fire_log":
        logs = result.get("logs", [])
        lines.append(f"- 查询到 **{len(logs)}** 条火灾日志")

    elif intent == "rag_query":
        if result.get("answer"):
            lines.append("- RAG 回答已生成")

    elif intent == "unknown":
        lines.append("- 无法判断意图，请提供更明确的指令")

    return "\n".join(lines)


def build_summary_lines(intent: str, result: dict) -> list:
    """Build a short text summary overlay for the annotated image."""
    tool_name = result.get("tool", intent)
    lines = [f"Tool: {tool_name}"]
    mp = result.get("model_path")
    if mp:
        from pathlib import Path as _P
        lines.append(f"Model: {_P(mp).name}")

    if intent == "detect":
        msg = result.get("message", "")
        if msg:
            lines.append(msg)
    elif intent in ("log", "event_log"):
        lines.append(f"Total detections: {result.get('total', 0)}")
        classes = result.get("class_distribution", {})
        if classes:
            lines.append("Per class:")
            for name, cnt in list(classes.items())[:6]:
                lines.append(f"  {name}: {cnt}")
            if len(classes) > 6:
                lines.append(f"  ... +{len(classes) - 6} more")
        lc = result.get("low_confidence_count", 0)
        th = result.get("threshold", 0.3)
        lines.append(f"Low-confidence (< {th}): {lc} sample(s)")
    elif intent == "detect_open":
        phrases = result.get("phrases", [])
        lines.append(f"Query: '{result.get('prompt', 'N/A')}'")
        lines.append(f"Matched: {', '.join(phrases) if phrases else 'none'}")
    elif intent == "segment":
        n = result.get("num_masks", 0)
        lines.append(f"Segmented {n} region(s)")
    elif intent == "report":
        if isinstance(result.get("summary"), str):
            lines.extend(result["summary"].split("\n")[:5])

    return lines

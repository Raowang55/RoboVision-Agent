"""RoboVision's small, observable multi-tool agent orchestrator.

Routing is deterministic by default so the application works without an LLM.
An OpenAI-compatible model can optionally parse ambiguous requests, while the
actual tool execution and the detect-to-RAG chain remain explicit and testable.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np

from app.config import DEFAULT_CONFIDENCE, GROUNDING_BOX_THRESHOLD, LLM_ENABLED
from app.contracts import AgentResponse, ToolResult, tool_error, tool_success
from app.utils.agent_utils import build_summary_lines as _summary_lines
from app.utils.agent_utils import save_numpy_as_rgb

Media = str | Path | np.ndarray | int | None
ToolHandler = Callable[[Media, str, dict[str, Any]], tuple[ToolResult, np.ndarray | None]]

CHAIN_CONNECTORS = ("并", "然后", "接着", "随后", "and", "then")
CHAIN_DETECT_KEYWORDS = ("检测", "识别", "查找", "发现", "detect", "find", "identify")
CHAIN_RAG_KEYWORDS = (
    "规范",
    "标准",
    "指南",
    "规定",
    "安全",
    "如何处理",
    "处置",
    "regulation",
    "standard",
    "guideline",
    "safety",
)


def _is_chain_query(text: str) -> bool:
    """Return whether a request explicitly asks for detection then knowledge."""
    lowered = (text or "").lower()
    return (
        any(word in lowered for word in CHAIN_CONNECTORS)
        and any(word in lowered for word in CHAIN_DETECT_KEYWORDS)
        and any(word in lowered for word in CHAIN_RAG_KEYWORDS)
    )


def parse_intent(text: str) -> str:
    """Fast offline intent parser used as the reliable default planner."""
    lowered = (text or "").strip().lower()
    if _is_chain_query(lowered):
        return "chain"
    if any(word in lowered for word in ("open vocabulary", "开放词汇", "自定义类别", "detect_open")):
        return "detect_open"
    if any(word in lowered for word in ("巡检报告", "生成报告", "inspection report", "summary report")):
        return "inspection_report"
    if any(word in lowered for word in ("事件处置", "处置工单", "disposal", "work order")):
        return "disposal"
    if any(
        word in lowered
        for word in ("event_log", "event log", "事件日志", "查看日志", "查询事件", "报警记录")
    ):
        return "event_log"
    if any(word in lowered for word in ("fire log", "fire alarm log", "火灾日志", "火警记录")):
        return "fire_log"
    if any(word in lowered for word in ("日志", "log history", "alarm log history")):
        return "event_log"
    if any(
        word in lowered
        for word in (
            "规范",
            "标准",
            "规定",
            "指南",
            "手册",
            "安全要求",
            "如何",
            "怎么",
            "为什么",
            "regulation",
            "standard",
            "guideline",
            "what safety",
            "how to",
        )
    ):
        return "rag"
    if any(word in lowered for word in ("火灾", "火焰", "烟雾", "火警", "fire", "smoke")):
        return "fire_log"
    return "detect"


_PLANNER_PROMPT = """You route requests for an industrial safety application.
Return only one JSON object with keys intent, confidence, params.
Valid intents: detect, detect_open, rag, chain, event_log, fire_log,
inspection_report, disposal. Do not invent another intent.
"""


def parse_intent_with_llm(text_prompt: str, use_llm: bool | None = None) -> dict[str, Any]:
    """Optionally use an LLM planner, then fall back immediately to rules."""
    enabled = LLM_ENABLED if use_llm is None else use_llm
    if enabled:
        try:
            from app.llm.llm_client import chat

            response = chat(
                [
                    {"role": "system", "content": _PLANNER_PROMPT},
                    {"role": "user", "content": text_prompt},
                ],
                temperature=0.0,
                max_tokens=200,
            )
            if response.get("success"):
                match = re.search(r"\{.*\}", response.get("content", ""), re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    valid = set(TOOL_REGISTRY) | {"chain"}
                    intent = str(parsed.get("intent", ""))
                    confidence = float(parsed.get("confidence", 0.0))
                    if intent in valid and confidence >= 0.5:
                        return {
                            "intent": intent,
                            "confidence": confidence,
                            "params": parsed.get("params", {}),
                            "source": "llm",
                        }
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    return {
        "intent": parse_intent(text_prompt),
        "confidence": 1.0,
        "params": {},
        "source": "rule",
    }


def _media_path(media: Media) -> str | int | None:
    if media is None:
        return None
    if isinstance(media, np.ndarray):
        return save_numpy_as_rgb(media)
    if isinstance(media, Path):
        return str(media)
    return media


def _read_rgb(path: str | None) -> np.ndarray | None:
    if not path or not Path(path).exists():
        return None
    image = cv2.imread(path)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image is not None else None


def _tool_detect(media: Media, prompt: str, params: dict[str, Any]) -> tuple[ToolResult, np.ndarray | None]:
    source = _media_path(media)
    if source is None:
        return tool_error("detect", "No image or video source was provided."), None

    from app.runtime.unified_pipeline import _detect_image, _detect_video

    task = str(params.get("task", "general"))
    confidence = float(params.get("confidence", params.get("conf", DEFAULT_CONFIDENCE)))
    source_text = str(source)
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    if isinstance(source, str) and Path(source).suffix.lower() in image_extensions:
        result = _detect_image(source, confidence, task)
        output_image = result.get("output_image")
        artifacts = {"output_image": output_image} if output_image else {}
        return (
            tool_success("detect", result.get("message", "Detection complete."), result, artifacts),
            _read_rgb(output_image),
        )

    video_source: str | int = int(source_text) if source_text.isdigit() else source_text
    result = _detect_video(
        video_source,
        confidence,
        int(params.get("frame_stride", 5)),
        int(params.get("max_frames", 300)),
        task,
    )
    if result.get("video_path") is None:
        return tool_error("detect", result.get("summary_md", "Could not open video source.")), None
    artifacts = {
        "video_path": result.get("video_path"),
        "log_path": result.get("log_path"),
        "alarm_images": result.get("alarm_images", []),
    }
    return tool_success("detect", result["summary_md"], result, artifacts), None


def _tool_detect_open(
    media: Media, prompt: str, params: dict[str, Any]
) -> tuple[ToolResult, np.ndarray | None]:
    if media is None:
        return tool_error("detect_open", "No image was provided."), None
    from app.tools.grounding_tool import detect_open
    from app.utils.vis_utils import draw_boxes

    if isinstance(media, np.ndarray):
        image = media
    else:
        path = Path(str(_media_path(media)))
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}:
            return tool_error("detect_open", "Open-vocabulary detection currently supports image input only."), None
        image = cv2.imread(str(path))
        if image is None:
            return tool_error("detect_open", "The image could not be read."), None
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = detect_open(
        image,
        prompt,
        box_threshold=float(params.get("confidence", GROUNDING_BOX_THRESHOLD)),
        classes=params.get("classes"),
    )
    annotated = draw_boxes(
        image.copy(),
        result.get("boxes", []),
        labels=result.get("phrases", []),
        scores=result.get("scores", []),
    )
    return tool_success("detect_open", result.get("message", "Detection complete."), result), annotated


def _tool_rag(media: Media, prompt: str, params: dict[str, Any]) -> tuple[ToolResult, None]:
    from app.rag.rag_tool import rag_query

    result = rag_query(
        question=params.get("question", prompt),
        top_k=int(params.get("top_k", 4)),
        use_llm=bool(params.get("use_llm", False)),
        history=params.get("history"),
    )
    return tool_success("rag", result.get("answer", ""), result), None


def _tool_event_log(media: Media, prompt: str, params: dict[str, Any]) -> tuple[ToolResult, None]:
    from app.tools.event_log_tool import query_event_log

    result = query_event_log()
    return tool_success("event_log", "Event log query complete.", result), None


def _tool_fire_log(media: Media, prompt: str, params: dict[str, Any]) -> tuple[ToolResult, None]:
    from app.tools.fire_log_tool import query_fire_log

    result = query_fire_log()
    return tool_success("fire_log", "Fire alarm log query complete.", result), None


def _tool_report(media: Media, prompt: str, params: dict[str, Any]) -> tuple[ToolResult, None]:
    from app.tools.event_log_tool import generate_inspection_report

    result = generate_inspection_report()
    artifacts = {"report_path": result.get("report_path")} if result.get("report_path") else {}
    return tool_success("inspection_report", "Inspection report generated.", result, artifacts), None


def _tool_disposal(media: Media, prompt: str, params: dict[str, Any]) -> tuple[ToolResult, None]:
    from app.agents.graph import run_disposal

    alarm_data = params.get("alarm_data", prompt)
    result = run_disposal(alarm_data)
    if result.get("error"):
        return tool_error("disposal", result["error"]), None
    return tool_success("disposal", "Disposal workflow complete.", result), None


TOOL_REGISTRY: dict[str, ToolHandler] = {
    "detect": _tool_detect,
    "detect_open": _tool_detect_open,
    "rag": _tool_rag,
    "event_log": _tool_event_log,
    "fire_log": _tool_fire_log,
    "inspection_report": _tool_report,
    "disposal": _tool_disposal,
}


def planned_tools(intent: str) -> list[str]:
    """Return the deterministic tool sequence for an intent."""
    if intent == "chain":
        return ["detect", "rag"]
    if intent in TOOL_REGISTRY:
        return [intent]
    return []


def _execute_tool(
    tool_name: str,
    media: Media,
    prompt: str,
    params: dict[str, Any],
) -> tuple[ToolResult, np.ndarray | None, dict[str, Any]]:
    started = time.perf_counter()
    handler = TOOL_REGISTRY.get(tool_name)
    if handler is None:
        result = tool_error(tool_name, f"Unknown tool '{tool_name}'.")
        annotated = None
    else:
        try:
            result, annotated = handler(media, prompt, params)
        except Exception as exc:
            result, annotated = tool_error(tool_name, str(exc)), None
    step = {
        "tool": tool_name,
        "status": "ok" if result["ok"] else "error",
        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        "summary": result["summary"][:300],
    }
    return result, annotated, step


def _chain_question(detections: list[dict[str, Any]]) -> str:
    translations = {
        "person": "人员",
        "fire": "火焰",
        "smoke": "烟雾",
        "helmet": "安全帽",
        "no-helmet": "未佩戴安全帽",
        "vest": "反光衣",
        "no-vest": "未穿反光衣",
    }
    classes = sorted({str(item.get("class_name", "")) for item in detections if item.get("class_name")})
    names = "、".join(translations.get(name, name) for name in classes)
    return f"检测到 {names or '相关目标'}，请给出对应的工业安全规范和处置建议。"


def _run_chain(
    media: Media,
    text_prompt: str,
    params: dict[str, Any],
) -> tuple[ToolResult, np.ndarray | None, list[dict[str, Any]]]:
    detect_result, annotated, detect_step = _execute_tool("detect", media, text_prompt, params)
    trace = [detect_step]
    if not detect_result["ok"]:
        return detect_result, annotated, trace

    data = detect_result["data"]
    detections = data.get("detections", data.get("detections_json", {}).get("detections", []))
    question = _chain_question(detections)
    rag_params = {
        "question": question,
        "top_k": params.get("top_k", 4),
        "use_llm": params.get("use_llm", False),
    }
    rag_result, _, rag_step = _execute_tool("rag", None, question, rag_params)
    trace.append(rag_step)
    merged = {
        "detection": data,
        "rag": rag_result["data"],
        "answer": rag_result["summary"],
        "question": question,
    }
    artifacts = dict(detect_result["artifacts"])
    result = tool_success("chain", rag_result["summary"], merged, artifacts)
    if not rag_result["ok"]:
        result = tool_error("chain", rag_result["error"] or "RAG query failed.")
        result["data"] = merged
        result["artifacts"] = artifacts
    return result, annotated, trace


def run_agent(
    image: Media = None,
    text_prompt: str = "",
    **kwargs: Any,
) -> AgentResponse:
    """Plan and execute one request through the registered real tools."""
    explicit_task = str(kwargs.get("task", "auto") or "auto").lower()
    use_llm = bool(kwargs.get("use_llm", LLM_ENABLED))

    if explicit_task == "auto" and image is not None and not _is_chain_query(text_prompt):
        lowered = text_prompt.lower()
        if any(word in lowered for word in ("fire", "smoke", "火灾", "火焰", "烟雾")):
            explicit_task = "fire"
        elif any(word in lowered for word in ("ppe", "helmet", "vest", "安全帽", "反光衣")):
            explicit_task = "ppe"
        else:
            explicit_task = "general"

    if explicit_task == "open":
        intent_info = {
            "intent": "detect_open",
            "confidence": 1.0,
            "params": {},
            "source": "explicit",
        }
    elif (
        explicit_task in {"general", "fire", "ppe"}
        and image is not None
        and not _is_chain_query(text_prompt)
    ):
        intent_info = {
            "intent": "detect",
            "confidence": 1.0,
            "params": {"task": explicit_task},
            "source": "explicit",
        }
    else:
        intent_info = parse_intent_with_llm(text_prompt, use_llm=use_llm)

    intent = intent_info["intent"]
    params = dict(intent_info.get("params", {}))
    params.update({key: value for key, value in kwargs.items() if key not in {"task", "use_llm"}})
    if explicit_task in {"general", "fire", "ppe"}:
        params["task"] = explicit_task
    elif intent == "detect":
        params.setdefault("task", "general")
    params["use_llm"] = use_llm

    if intent == "chain":
        tool_result, annotated, trace = _run_chain(image, text_prompt, params)
    else:
        tool_result, annotated, step = _execute_tool(intent, image, text_prompt, params)
        trace = [step]

    result_data = dict(tool_result["data"])
    if tool_result["summary"] and "answer" not in result_data:
        result_data.setdefault("message", tool_result["summary"])

    planner_source = intent_info.get("source", "rule")
    return {
        "ok": tool_result["ok"],
        "intent": intent,
        "result": result_data,
        "error": tool_result["error"],
        "artifacts": tool_result["artifacts"],
        "trace": trace,
        "planner_source": planner_source,
        "intent_info": intent_info,
        "annotated_image": annotated,
    }


def run_agent_with_react(text_prompt: str, media: Media = None, max_steps: int = 2) -> AgentResponse:
    """Backward-compatible entry point for the removed free-form ReAct loop.

    The bounded orchestrator is deliberately used instead; ``max_steps`` is
    retained only to avoid breaking callers from the earlier prototype.
    """
    del max_steps
    return run_agent(image=media, text_prompt=text_prompt, use_llm=LLM_ENABLED)


_save_numpy_as_rgb = save_numpy_as_rgb
_build_summary_lines = _summary_lines

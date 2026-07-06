"""Agent scheduler -- routes user requests to the right tools.

Supports single-tool dispatch and multi-step chain: detect -> RAG.
"""

import json
import re
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.tools import (
    detect_open, segment, analyze,
    generate_report, deploy, query_log,
    query_fire_log, build_markdown_summary,
    query_event_log, build_summary_markdown,
    generate_inspection_report,
)
from app.rag.rag_tool import rag_query
from app.utils.file_utils import get_output_path


# Map of command keywords to (tool function, description)
TOOL_REGISTRY = {
    "detect_open": (detect_open, "Find objects by text description (open vocabulary)"),
    "segment": (segment, "Segment objects with SAM"),
    "analyze": (analyze, "Analyze dataset statistics"),
    "report": (generate_report, "Generate a visual report"),
    "deploy": (deploy, "Export model to ONNX / TensorRT"),
    "log": (query_log, "Analyze detection logs"),
    "fire_log": (query_fire_log, "Analyze fire alarm logs"),
    "event_log": (query_event_log, "Analyze unified event log"),
    "inspection_report": (generate_inspection_report, "Generate inspection report and save to file"),
    "rag": (rag_query, "RAG knowledge base Q&A with Qwen3-VL"),
}

# ---------------------------------------------------------------------------
# chain detection -- multi-step: detect -> RAG
# ---------------------------------------------------------------------------

# Connector words that signal a multi-step request
CHAIN_CONNECTORS = ("?", "??", "??", "??", "?", "??", "??", "and", "then")

# Keywords that suggest the FIRST step is detection
CHAIN_DETECT_KEYWORDS = (
    "??", "??", "??", "detect", "find", "identify",
    "??", "??", "??", "??", "??",
)

# Keywords that suggest the SECOND step is RAG / knowledge query
CHAIN_RAG_KEYWORDS = (
    "??", "??", "??", "??", "??", "??", "??",
    "????", "????", "????", "???",
    "??", "??", "??", "??",
    "regulation", "standard", "guideline", "safety",
)


def _is_chain_query(text: str) -> bool:
    """Return True if *text* looks like a multi-step detect-then-RAG request."""
    text_lower = text.lower()

    # Must contain a connector
    has_connector = any(c in text_lower for c in CHAIN_CONNECTORS)
    if not has_connector:
        return False

    # Must contain at least one detect keyword AND one RAG keyword
    has_detect = any(w in text_lower for w in CHAIN_DETECT_KEYWORDS)
    has_rag = any(w in text_lower for w in CHAIN_RAG_KEYWORDS)

    return has_detect and has_rag


# ---------------------------------------------------------------------------
# intent parser (keyword-based)
# ---------------------------------------------------------------------------

def parse_intent(text: str) -> str:
    """Naive intent parser -- looks for tool keywords in the user's message."""
    text_lower = text.lower()

    # Priority 0: multi-step chain (detect + RAG)
    if _is_chain_query(text_lower):
        return "chain"

    # Priority 1: explicit open-vocabulary keywords
    if any(w in text_lower for w in ("open vocabulary", "grounding", "detect_open")):
        return "detect_open"

    # Priority 2: segmentation
    if any(w in text_lower for w in ("segment", "mask", "sam")):
        return "segment"

    # Priority 3: dataset analysis
    if any(w in text_lower for w in ("analyze", "dataset", "statistics", "stats")):
        return "analyze"

    # Priority 4: report / visual report
    if any(w in text_lower for w in ("report", "visualize")):
        return "report"

    # Priority 5.5: RAG knowledge base Q&A (direct questions)
    if any(w in text_lower for w in (
        "???", "????", "????", "??",
        "??", "??", "???", "??",
        "??", "??", "??", "??",
    )):
        return "rag"

    if any(w in text_lower for w in ("deploy", "export", "onnx", "tensorrt")):
        return "deploy"

    # Priority 6: inspection report (report generation keywords)
    if any(w in text_lower for w in ("????", "????", "??", "??", "summary")):
        return "inspection_report"

    # Priority 7: unified event log -- Chinese keywords (??/??/??/??/????/??)
    if any(w in text_lower for w in ("??", "??", "??", "??", "????", "??")):
        return "event_log"

    # Priority 8: fire alarm log (specific fire/smoke queries)
    if any(w in text_lower for w in ("fire", "smoke")):
        return "fire_log"

    # Priority 9: unified event log (general English keywords)
    if any(w in text_lower for w in ("log", "event_log")):
        return "event_log"

    # Priority 10: legacy keywords -> event_log for backward compat
    if any(w in text_lower for w in ("alarm",)):
        return "event_log"

    # Priority 11: YOLO detection (default for common vision keywords)
    if any(w in text_lower for w in (
        "detect", "yolo", "object", "objects",
        "find", "identify",
        "people", "person", "persons",
        "vehicle", "vehicles", "car", "cars",
        "truck", "trucks", "bus", "buses",
    )):
        return "detect"

    # Default: YOLO detection
    return "detect"


# ---------------------------------------------------------------------------
# LLM intent router
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "??????AI Agent???????\n"
    "?????JSON??????????????????????\n"
    "\n"
    "??intent?????\n"
    "- detect: ????????????????\n"
    "- chain: ????????????????????\n"
    "  ????????\"?\"?\"??\"?\"??\"?\"??\"?????\n"
    "   ????????????????\n"
    "- rag: ??????????????\n"
    "- inspection_report: ??????\n"
    "- event_log: ??????\n"
    "- fire_log: ????????\n"
    "- deploy: ????????\n"
    "\n"
    "??task_subtype??fire | ppe | general\n"
    "\n"
    "chain?????\n"
    '- \"??????????\" ??chain\n'
    '- \"????????????????????\" ??chain\n'
    '- \"???????????????????\" ??chain\n'
    "\n"
    "?????\n"
    "{\n"
    '  "intent": "string",\n'
    '  "confidence": 0.0-1.0,\n'
    '  "params": {\n'
    '    "need_rag": true/false,\n'
    '    "media_type": "image/video/text",\n'
    '    "task_subtype": "fire/ppe/general"\n'
    "  }\n"
    "}"
)


def parse_intent_with_llm(text_prompt: str) -> dict:
    """Use Qwen3-VL LLM to parse user intent from natural language.

    Returns a dict with intent, confidence, and params.
    Falls back to keyword-based parse_intent() on failure.

    Args:
        text_prompt: The user's raw input text.

    Returns:
        dict: {"intent": str, "confidence": float, "params": {...}}
    """
    try:
        from app.llm.deepseek_client import chat

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text_prompt},
        ]

        llm_result = chat(messages, temperature=0.0, max_tokens=300)

        if not llm_result.get("success"):
            raise ValueError(f"LLM call failed: {llm_result.get('error')}")

        raw = llm_result["content"]

        # ---- Clean JSON: remove markdown fences and surrounding noise ----
        # Strip ```json ... ``` wrappers
        cleaned = re.sub(r"```(?:json)?\s*", "", raw)
        cleaned = re.sub(r"```", "", cleaned)
        # Strip any text before the first { and after the last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object found in LLM response: {raw}")
        cleaned = cleaned[start:end + 1]

        parsed = json.loads(cleaned)

        intent = parsed.get("intent", "")
        confidence = float(parsed.get("confidence", 0))

        # Validate intent value
        valid_intents = {
            "detect", "rag", "chain", "inspection_report",
            "event_log", "fire_log", "deploy",
        }
        if intent not in valid_intents:
            raise ValueError(f"Unknown intent: {intent}")

        # ---- Fallback if confidence too low ----
        if confidence < 0.5:
            raise ValueError(f"Low confidence: {confidence}")

        return {
            "intent": intent,
            "confidence": confidence,
            "params": parsed.get("params", {}),
            "source": "llm",
        }

    except Exception:
        # Fallback to keyword-based parser
        keyword_intent = parse_intent(text_prompt)
        return {
            "intent": keyword_intent,
            "confidence": 0.0,
            "params": {},
            "source": "keyword_fallback",
        }


# ---------------------------------------------------------------------------
# image helpers
# ---------------------------------------------------------------------------

def _save_numpy_as_rgb(image: np.ndarray) -> str:
    """Save a Gradio RGB numpy image to a temp file and return the path."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = "data/outputs"
    path = get_output_path(prefix=f"input_{ts}", ext=".jpg", directory=out_dir)
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), bgr)
    return str(path)


# ---------------------------------------------------------------------------
# multi-step chain: detect -> RAG
# ---------------------------------------------------------------------------

def _run_chain(
    image: np.ndarray | None,
    text_prompt: str,
    **kwargs: Any,
) -> tuple[dict, np.ndarray | None]:
    """Execute detect then RAG query in sequence.

    Steps:
        1. Run YOLO detection on the image.
        2. Extract unique detected class names.
        3. Build a RAG query: "[class_names] ???????"
        4. Call rag_query with the constructed question.
        5. Return merged result.

    Returns:
        (result_dict, annotated_image_array)
    """
    trace = []

    # ---- Step 1: detect ----
    if image is None:
        return {
            "answer": "??????????????????????",
            "detections": [],
            "rag_answer": None,
            "used_chain": True,
            "decision_trace": ["chain: no image provided -> abort"],
        }, None

    temp_path = _save_numpy_as_rgb(image)
    trace.append(f"detect(image={Path(temp_path).name})")

    detect_result = detect(image_path=temp_path, conf=kwargs.get("conf", 0.25))
    detections = detect_result.get("detections", [])
    trace.append(f"detect -> {len(detections)} objects found")

    # ---- Step 2: extract unique class names ----
    class_names = list({d["class_name"] for d in detections})
    if not class_names:
        return {
            "answer": "???????????????????????????",
            "detections": detections,
            "rag_answer": None,
            "used_chain": True,
            "decision_trace": trace,
        }, _read_annotated_image(detect_result)

    trace.append(f"classes: {class_names}")

    # ---- Step 3: build RAG question ----
    # Translate common English class names to Chinese for better RAG retrieval
    _class_translation = {
        "person": "??", "car": "??", "truck": "??",
        "bus": "??", "bicycle": "???", "motorcycle": "???",
        "fire": "??", "smoke": "??",
        "helmet": "???", "vest": "???",
    }
    chinese_names = [_class_translation.get(cn, cn) for cn in class_names]
    names_str = "?".join(chinese_names)

    question = f"??? {names_str}????????????????"
    trace.append(f"rag_query(question={question!r})")

    # ---- Step 4: RAG query ----
    rag_result = rag_query(question=question)
    trace.append(f"rag -> used_llm={rag_result.get('used_llm')}, model={rag_result.get('model')}")

    # ---- Step 5: merge ----
    answer_parts = [
        f"**????**??? {len(detections)} ?????? {len(class_names)} ??{names_str}?",
        "",
        f"**????**?{rag_result.get('answer', '????????')}",
    ]

    if rag_result.get("source_files"):
        answer_parts.append("")
        answer_parts.append("**????**?")
        for src in rag_result["source_files"]:
            answer_parts.append(f"  - `{src}`")

    merged = {
        "answer": "\n".join(answer_parts),
        "detections": detections,
        "rag_answer": rag_result.get("answer"),
        "rag_source_files": rag_result.get("source_files", []),
        "rag_used_llm": rag_result.get("used_llm", False),
        "rag_model": rag_result.get("model"),
        "used_chain": True,
        "decision_trace": trace,
    }

    # Read annotated image from detect
    annotated = _read_annotated_image(detect_result)

    return merged, annotated


def _read_annotated_image(detect_result: dict) -> np.ndarray | None:
    """Read the output_image from a detect result as RGB numpy array."""
    out_img = detect_result.get("output_image")
    if out_img and Path(out_img).exists():
        img = cv2.imread(out_img)
        if img is not None:
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return None



# ---------------------------------------------------------------------------
# ReAct loop -- lightweight agentic reasoning
# ---------------------------------------------------------------------------

# Keywords that trigger the ReAct path (more complex reasoning needed)
_REACT_KEYWORDS = (
    "分析", "评估", "为什么", "怎么办", "接着", "然后", "原因",
    "analyze", "assess", "why", "how", "then", "next",
)


_REACT_SYSTEM_PROMPT = """You are an industrial vision AI agent. You have access to these tools:

- detect: Run YOLO object detection on an image. Params: {"conf": float} (optional, default 0.25)
- rag: Query the safety knowledge base. Params: {"question": "string"} (required)
- event_log: Query unified event/detection logs and statistics. Params: {} (none)
- fire_log: Query fire alarm log. Params: {} (none)
- inspection_report: Generate an inspection report from logs. Params: {} (none)
- finish: Return the final answer and stop. Params: {"answer": "string"} (required)

You MUST respond in exactly this format each round:
思考：<1-2 sentences describing your reasoning and next step, in Chinese>
行动：valid JSON object with "tool" and "params" keys>

Example:
思考：用户的问题涉及安全规范，我需要先查询知识库。
行动：{"tool": "rag", "params": {"question": "安全帽的佩戴规范是什么？"}}

When you have enough information to answer the user, call finish:
思考：我已经获得足够的信息，可以给出最终回答。
行动：{"tool": "finish", "params": {"answer": "根据知识库.."}}

Important rules:
- Output ONLY one "思考：" and one "行动： per round, nothing else.
- The "行动： must be a single line of valid JSON.
- Never make up information. If you don't know, say so.
"""


def _parse_react_output(text: str):
    """Parse LLM ReAct output: extract '思考：' and '行动： sections.

    Returns (thought, action_dict, error).
    """
    # Extract thought
    thought_match = re.search(r"思考[：]\s*(.+?)(?:\n|行动|$)", text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else None

    # Extract action JSON
    action_match = re.search(r"行动[：]\s*(.+?)(?:$)", text, re.DOTALL)
    if not action_match:
        return thought, None, "Could not find '行动： in LLM response"

    raw_action = action_match.group(1).strip()

    # Clean JSON: remove markdown fences and surrounding noise
    cleaned = re.sub(r"```(?:json)?\s*", "", raw_action)
    cleaned = re.sub(r"```", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return thought, None, f"No JSON object found in action: {raw_action[:100]}"
    cleaned = cleaned[start:end + 1]

    try:
        action = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return thought, None, f"JSON parse error: {e} | raw: {cleaned[:100]}"

    if "tool" not in action:
        return thought, None, "Action JSON missing 'tool' key"

    return thought, action, None


def _format_observation(tool_name: str, result: dict) -> str:
    """Format a tool result as a concise observation string for the LLM."""
    if result.get("_finish"):
        return "[finish] task complete"

    if "error" in result:
        return f"[error] {tool_name}: {result['error']}"

    if tool_name == "detect":
        dets = result.get("detections", [])
        msg = result.get("message", "")
        classes = list({d["class_name"] for d in dets})
        return json.dumps({
            "tool": "detect",
            "objects_found": len(dets),
            "classes": classes,
            "summary": msg,
        }, ensure_ascii=False)

    if tool_name == "rag":
        answer = result.get("answer", "")
        return json.dumps({
            "tool": "rag",
            "answer_preview": answer[:300],
            "sources": result.get("source_files", []),
        }, ensure_ascii=False)

    if tool_name == "event_log":
        return json.dumps({
            "tool": "event_log",
            "log_exists": result.get("log_exists", False),
            "total_events": result.get("total_events", 0),
            "total_alarms": result.get("total_alarms", 0),
            "by_alarm_level": result.get("by_alarm_level", {}),
            "recent_alarm_count": result.get("recent_alarm_count", 0),
        }, ensure_ascii=False)

    if tool_name == "fire_log":
        return json.dumps({
            "tool": "fire_log",
            "log_exists": result.get("log_exists", False),
            "total_alarms": result.get("total_alarms", 0),
            "by_level": result.get("by_level", {}),
        }, ensure_ascii=False)

    if tool_name == "inspection_report":
        return json.dumps({
            "tool": "inspection_report",
            "log_exists": result.get("log_exists", False),
            "total_events": result.get("total_events", 0),
            "total_alarms": result.get("total_alarms", 0),
            "report_path": result.get("report_path"),
        }, ensure_ascii=False)

    # Default: return a compact summary
    return json.dumps({"tool": tool_name, "result": str(result)[:200]}, ensure_ascii=False)


def _call_tool_react(tool_name: str, params: dict, media=None):
    """Execute a tool from TOOL_REGISTRY with given params and media."""
    if tool_name == "finish":
        return {"answer": params.get("answer", ""), "_finish": True}

    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool '{tool_name}'. Available: {list(TOOL_REGISTRY.keys())}"}

    tool_fn, _ = TOOL_REGISTRY[tool_name]

    try:
        if tool_name == "detect":
            if media is None:
                return {"tool": "detect", "error": "No image provided. Please upload an image first."}
            if isinstance(media, np.ndarray):
                temp_path = _save_numpy_as_rgb(media)
                return tool_fn(image_path=temp_path, conf=params.get("conf", 0.25))
            if isinstance(media, str):
                return tool_fn(image_path=media, conf=params.get("conf", 0.25))
            return {"tool": "detect", "error": f"Unsupported media type: {type(media)}"}

        if tool_name == "rag":
            question = params.get("question", "")
            if not question:
                return {"tool": "rag", "error": "No question provided for RAG query."}
            return tool_fn(question=question)

        if tool_name in ("event_log", "fire_log", "inspection_report", "log", "deploy", "analyze"):
            return tool_fn()

        # Fallback for other tools
        return tool_fn()

    except Exception as exc:
        return {"tool": tool_name, "error": str(exc)}


def run_agent_with_react(
    text_prompt: str,
    media=None,
    max_steps: int = 2,
) -> dict:
    """Lightweight ReAct loop: think, act, observe, repeat.

    The LLM decides which tool to call each round, sees the result,
    and either continues or calls 'finish' to return the final answer.

    Returns the same format as run_agent(), plus a "steps" field.
    """
    from app.llm.deepseek_client import chat

    steps: list[dict] = []

    # ---- Build initial messages ----
    media_hint = "" if media is None else " [An image is available for detection]"
    messages = [
        {"role": "system", "content": _REACT_SYSTEM_PROMPT},
        {"role": "user", "content": f"User request: {text_prompt}{media_hint}"},
    ]

    final_answer = ""

    for step_idx in range(max_steps):
        # ---- Call LLM ----
        llm_result = chat(messages, temperature=0.0, max_tokens=600)

        if not llm_result.get("success"):
            steps.append({
                "step": step_idx + 1,
                "thought": "", "action": None, "observation": "",
                "error": f"LLM call failed: {llm_result.get('error')}",
            })
            final_answer = "Sorry, the LLM service is currently unavailable. Please try again later."
            break

        raw_response = llm_result["content"]

        # ---- Parse ----
        thought, action, parse_error = _parse_react_output(raw_response)

        if parse_error:
            steps.append({
                "step": step_idx + 1,
                "thought": thought or "", "action": None, "observation": "",
                "error": parse_error, "raw_response": raw_response[:200],
            })
            final_answer = "Sorry, I encountered an issue processing your request. Please try again."
            break

        tool_name = action.get("tool", "")
        tool_params = action.get("params", {})

        # ---- Execute tool ----
        tool_result = _call_tool_react(tool_name, tool_params, media)
        observation = _format_observation(tool_name, tool_result)

        steps.append({
            "step": step_idx + 1,
            "thought": thought or "",
            "tool": tool_name,
            "params": tool_params,
            "observation": observation,
        })

        # ---- Check if finish ----
        if tool_result.get("_finish"):
            final_answer = tool_result.get("answer", "")
            break

        # ---- Append to conversation for next round ----
        messages.append({"role": "assistant", "content": raw_response})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    # ---- If loop finished without calling finish, ask LLM to summarize ----
    if not final_answer and steps:
        summary_prompt = f"Based on the observations above, write a concise answer to the user's request: '{text_prompt}'"
        messages.append({"role": "user", "content": summary_prompt})
        summary_result = chat(messages, temperature=0.2, max_tokens=500)
        if summary_result.get("success"):
            final_answer = summary_result["content"]
        else:
            final_answer = "Sorry, I was unable to complete the analysis. Please try again."

    # ---- Build unified result ----
    return {
        "intent": "react",
        "result": {
            "answer": final_answer,
            "steps": steps,
        },
        "error": None,
        "annotated_image": None,
        "intent_info": {"intent": "react", "confidence": 1.0, "params": {}, "source": "react"},
    }


# ---------------------------------------------------------------------------
# main agent loop
# ---------------------------------------------------------------------------


def run_agent(
    image: np.ndarray | None,
    text_prompt: str,
    **kwargs: Any,
) -> dict:
    """Main agent loop -- parse intent, call the right tool, return results.

    Supports:
    - Single-tool dispatch (detect, rag, event_log, etc.)
    - Multi-step chain: detect -> RAG (when text contains "??...?...??")

    Returns:
        dict with keys:
            intent, result (tool output dict),
            error (str or None), annotated_image (RGB numpy or None),
            intent_info (dict with LLM parse details).
    """
    # ---- Intent parsing: LLM first, keyword fallback ----
    intent_info = parse_intent_with_llm(text_prompt)

    # ---- ReAct routing: complex queries that need multi-step reasoning ----
    should_use_react = (
        intent_info["intent"] == "chain"
        or any(kw in text_prompt for kw in _REACT_KEYWORDS)
    )
    if should_use_react:
        try:
            return run_agent_with_react(text_prompt, media=image, max_steps=2)
        except Exception as exc:
            return {
                "intent": "react",
                "result": {"answer": f"ReAct failed: {exc}", "steps": []},
                "error": str(exc),
                "annotated_image": None,
                "intent_info": intent_info,
            }

    # Auto-convert detect+need_rag to chain when media is available
    if (
        intent_info["intent"] == "detect"
        and intent_info.get("params", {}).get("need_rag", False)
        and image is not None
    ):
        intent_info["intent"] = "chain"
        intent_info["confidence"] = max(intent_info.get("confidence", 0), 0.8)

    intent = intent_info["intent"]

    # ---- Multi-step chain: detect -> RAG ----
    if intent == "chain":
        try:
            chain_result, annotated = _run_chain(image, text_prompt, **kwargs)
            return {
                "intent": "chain",
                "result": chain_result,
                "error": None,
                "annotated_image": annotated,
                "intent_info": intent_info,
            }
        except Exception as exc:
            return {
                "intent": "chain",
                "result": {
                    "answer": f"???????{exc}",
                    "detections": [],
                    "rag_answer": None,
                    "used_chain": True,
                    "decision_trace": [f"chain error: {exc}"],
                },
                "error": str(exc),
                "annotated_image": None,
                "intent_info": intent_info,
            }

    # ---- Single-tool dispatch ----
    if intent not in TOOL_REGISTRY:
        return {
            "intent": intent,
            "result": None,
            "error": f"Unknown tool '{intent}'. Available: {list(TOOL_REGISTRY.keys())}",
            "annotated_image": None,
            "intent_info": intent_info,
        }

    tool_fn, _ = TOOL_REGISTRY[intent]

    try:
        # ---- YOLO detect ----
        if intent == "detect":
            if image is None:
                result = {
                    "tool": "yolo_detect",
                    "message": "[Error] No image provided. Please upload an image first.",
                }
            else:
                temp_path = _save_numpy_as_rgb(image)
                from app.runtime.unified_pipeline import _detect_image
                result = _detect_image(temp_path, conf=kwargs.get("conf", 0.25))

        # ---- Open-vocabulary detect (mock) ----
        elif intent == "detect_open":
            result = tool_fn(image, text_prompt, **kwargs) if image is not None else {"error": "No image provided"}

        # ---- Segment (mock) ----
        elif intent == "segment":
            result = tool_fn(image, **kwargs) if image is not None else {"error": "No image provided"}

        # ---- Analyze dataset (no image needed) ----
        elif intent == "analyze":
            result = tool_fn(**kwargs)

        # ---- Log analysis (no image needed) ----
        elif intent == "log":
            result = tool_fn()

        # ---- Fire alarm log analysis (no image needed) ----
        elif intent == "fire_log":
            result = tool_fn()

        # ---- Unified event log analysis (no image needed) ----
        elif intent == "event_log":
            result = tool_fn()

        # ---- Inspection report (no image needed) ----
        elif intent == "inspection_report":
            result = tool_fn()

        # ---- RAG knowledge base Q&A ----
        elif intent == "rag":
            # Check if the query also references logs/alarms
            log_keywords = ("??", "????", "high", "??", "??", "??")
            log_context = None
            if any(w in text_prompt for w in log_keywords):
                log_context = query_event_log()
            result = rag_query(question=text_prompt, log_context=log_context)

        # ---- Report (uses detect internally) ----
        elif intent == "report":
            if image is not None:
                temp_path = _save_numpy_as_rgb(image)
                detections = detect(image_path=temp_path)
                mask_result = segment(image)
                result = tool_fn(image, detections=detections, masks=mask_result, **kwargs)
            else:
                result = {"error": "No image provided for report"}

        elif intent == "deploy":
            result = tool_fn(**kwargs)

        else:
            result = {"error": f"Unknown intent: {intent}"}

        # ---- Build annotated image for display ----
        annotated = None

        if intent == "detect":
            out_img = result.get("output_image")
            if out_img and Path(out_img).exists():
                annotated = cv2.imread(out_img)
                annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        elif intent == "log":
            pass

        elif intent == "fire_log":
            recent = result.get("recent", [])
            if recent:
                newest = recent[0]
                img_path = newest.get("alarm_image", "")
                if img_path and Path(img_path).exists():
                    annotated = cv2.imread(str(img_path))
                    annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        elif intent == "event_log":
            recent = result.get("recent_alarms", [])
            if recent:
                newest = recent[0]
                img_path = newest.get("alarm_image", "")
                if img_path and Path(img_path).exists():
                    annotated = cv2.imread(str(img_path))
                    annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        elif intent == "inspection_report":
            alarm_imgs = result.get("alarm_images", [])
            if alarm_imgs:
                img_path = alarm_imgs[0]
                if img_path and Path(img_path).exists():
                    annotated = cv2.imread(str(img_path))
                    annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        elif intent == "rag":
            log_ctx = result.get("log_context", {})
            if log_ctx and log_ctx.get("log_exists"):
                recent = log_ctx.get("recent_alarms", [])
                if recent:
                    img_path = recent[0].get("alarm_image", "")
                    if img_path and Path(img_path).exists():
                        annotated = cv2.imread(str(img_path))
                        annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        elif image is not None and intent in ("detect_open", "segment", "report"):
            from app.utils.vis_utils import draw_boxes, draw_masks, draw_labels
            annotated = image.copy()

            if intent == "detect_open" and "boxes" in result:
                annotated = draw_boxes(annotated, result["boxes"],
                                       labels=result.get("phrases"),
                                       scores=result.get("scores"))

            if intent == "segment" and "masks" in result:
                annotated = draw_masks(annotated, result["masks"])

            if intent == "report" and "boxes" in result:
                annotated = draw_boxes(annotated, result["boxes"],
                                       labels=result.get("labels"),
                                       scores=result.get("scores"))

            summary_lines = _build_summary_lines(intent, result)
            annotated = draw_labels(annotated, summary_lines)

        return {
            "intent": intent,
            "result": result,
            "error": None,
            "annotated_image": annotated,
            "intent_info": intent_info,
        }

    except Exception as exc:
        return {
            "intent": intent,
            "result": None,
            "error": str(exc),
            "annotated_image": None,
            "intent_info": intent_info,
        }


# ---------------------------------------------------------------------------
# summary helpers
# ---------------------------------------------------------------------------

def _build_summary_lines(intent: str, result: dict) -> list:
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

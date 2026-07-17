# -*- coding: utf-8 -*-
"""RoboVision Agent -- Unified Industrial Vision Alert Console.

Complete UI redesign: industrial console dark theme, 4 tabs with consistent layout.
"""

from __future__ import annotations

import atexit
import logging
import os
import socket
import sys
from pathlib import Path

import gradio as gr

from app.agent import run_agent
from app.config import SERVER_HOST, SERVER_PORT, ensure_runtime_dirs
from app.constants import UI_TEXTS
from app.ui.detection_tab import build_detection_tab
from app.ui.disposal_tab import build_disposal_tab
from app.ui.log_tab import build_log_tab
from app.ui.rag_tab import build_rag_tab
from app.ui.theme import CUSTOM_CSS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# environment
# ---------------------------------------------------------------------------
os.environ.setdefault("GRADIO_SERVER_NAME", SERVER_HOST)
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"


# ===========================================================================
# Build UI
# ===========================================================================

def build_ui(lang: str = "zh"):
    texts = UI_TEXTS.get(lang, UI_TEXTS["zh"])

    with gr.Blocks(title=texts["title"], css=CUSTOM_CSS) as demo:

        # ━━━ Header ━━━
        gr.HTML(f"""<div class=\"header-banner\">
            <div class=\"header-content\">
                <div class=\"header-icon\">&#128065;</div>
                <div class=\"header-brand\">
                    <h1>{texts["title"]}</h1>
                    <p class=\"subtitle\">{texts["subtitle"]}</p>
                </div>
                <div class=\"web-ready-badge\">
                    <div class=\"web-ready-dot\"></div>
                    <span>Web Ready</span>
                </div>
            </div>
        </div>""")

        with gr.Tabs():
            # TAB 1: Vision Detection
            detect_comps = build_detection_tab(texts)
            file_input = detect_comps["file_input"]
            source_input = detect_comps["source_input"]
            task_dropdown = detect_comps["task_dropdown"]
            text_input = detect_comps["text_input"]
            conf_slider = detect_comps["conf_slider"]
            stride_slider = detect_comps["stride_slider"]
            max_frames_slider = detect_comps["max_frames_slider"]
            run_btn = detect_comps["run_btn"]
            summary_md = detect_comps["summary_md"]
            alarm_gallery = detect_comps["alarm_gallery"]
            annotated_image = detect_comps["annotated_image"]
            video_output = detect_comps["video_output"]
            json_output = detect_comps["json_output"]
            status_msg = detect_comps["status_msg"]
            trace_table = detect_comps["trace_table"]
            agent_chatbot = detect_comps["agent_chatbot"]
            clear_btn = detect_comps["clear_btn"]
            agent_chat_history = detect_comps["agent_chat_history"]
            log_path_output = detect_comps["log_path_output"]

            # TAB 2: RAG Knowledge Q&A
            rag_comps = build_rag_tab(texts)
            rag_question = rag_comps["rag_question"]
            rag_top_k = rag_comps["rag_top_k"]
            rag_use_llm = rag_comps["rag_use_llm"]
            rag_btn = rag_comps["rag_btn"]
            rag_answer_md = rag_comps["rag_answer_md"]
            rag_model_info = rag_comps["rag_model_info"]
            rag_sources_md = rag_comps["rag_sources_md"]
            rag_chunks_md = rag_comps["rag_chunks_md"]
            rag_chat_history = rag_comps["rag_chat_history"]

            # TAB 3: Logs & Reports
            log_comps = build_log_tab(texts)
            log_query_input = log_comps["log_query_input"]
            log_query_btn = log_comps["log_query_btn"]
            log_result_md = log_comps["log_result_md"]
            log_alarm_gallery = log_comps["log_alarm_gallery"]
            log_report_path = log_comps["log_report_path"]

            # TAB 4: Rule-based event disposal workflow
            build_disposal_tab(texts)

        # ━━━ Footer ━━━
        gr.HTML(f"<footer>{texts['footer']}</footer>")

        # ━━━ Bind events ━━━
        run_btn.click(
            fn=process,
            inputs=[file_input, text_input, task_dropdown, source_input, conf_slider, stride_slider, max_frames_slider, agent_chat_history],
            outputs=[summary_md, annotated_image, video_output, alarm_gallery, json_output, log_path_output, status_msg, trace_table, agent_chatbot, agent_chat_history],
        )

        clear_btn.click(
            fn=lambda: ([], []),
            inputs=[],
            outputs=[agent_chatbot, agent_chat_history],
        )

        rag_btn.click(
            fn=rag_chat,
            inputs=[rag_question, rag_top_k, rag_use_llm, rag_chat_history],
            outputs=[rag_answer_md, rag_model_info, rag_sources_md, rag_chunks_md, rag_chat_history],
        )

        log_query_btn.click(
            fn=log_query_handler,
            inputs=[log_query_input],
            outputs=[log_result_md, log_alarm_gallery, log_report_path],
        )

    return demo


# ===========================================================================
# Gradio event handlers (with error boundaries)
# ===========================================================================

def process(file_path, text_prompt, task, source, confidence, stride, max_frames, chat_history):
    """Run detection pipeline with error boundary."""
    try:
        return _process_impl(file_path, text_prompt, task, source, confidence, stride, max_frames, chat_history)
    except Exception as exc:
        logger.error("process() crashed: %s", exc, exc_info=True)
        return f"**Internal error**: {exc}", None, None, [], {}, "", f"Error: {exc}", [], [], (chat_history or [])


def _process_impl(file_path, text_prompt, task, source, confidence, stride, max_frames, chat_history):
    prompt = text_prompt or ""
    task_map = {
        "自动判断": "auto", "Auto Detect": "auto",
        "通用物品检测": "general", "General Object Detection": "general",
        "开放词汇检测（图片）": "open", "Open Vocabulary (Image)": "open",
        "火灾烟雾预警": "fire", "Fire & Smoke Warning": "fire",
        "安全帽反光衣工检": "ppe", "PPE Safety Helmet & Reflective Vest Check": "ppe",
    }
    task_name = task_map.get(task, "auto")

    media = None
    if file_path:
        media = file_path if isinstance(file_path, str) else str(file_path)
    elif source and source.strip():
        media = source.strip()

    output = run_agent(
        image=media,
        text_prompt=prompt,
        task=task_name,
        confidence=confidence,
        frame_stride=stride,
        max_frames=max_frames,
        use_llm=False,
    )

    error = output.get("error", "")
    if error:
        chatbot = _history_to_chatbot(chat_history or [])
        return f"**Error**: {error}", None, None, [], {}, "", f"Error: {error}", _format_trace_rows(output), chatbot, chat_history

    result = output.get("result", {}) or {}
    artifacts = output.get("artifacts", {}) or {}
    summary = result.get("summary_md") or result.get("message") or result.get("answer") or _format_agent_result(output)
    annotated_path = output.get("annotated_image")
    video_path = artifacts.get("video_path")
    alarm_images = artifacts.get("alarm_images", [])[:4]
    json_data = result.get("detections_json") or result.get("detections") or result
    log_path = artifacts.get("log_path", "") or artifacts.get("report_path", "")

    chat_history = chat_history or []
    chat_history.append({"role": "user", "content": prompt or f"[{task_name}]"})
    chat_history.append({"role": "assistant", "content": summary})

    chatbot = _history_to_chatbot(chat_history)
    trace_rows = _format_trace_rows(output)
    status = f"完成 · planner={output.get('planner_source', 'rule')} · steps={len(trace_rows)}"
    return summary, annotated_path, video_path, alarm_images, json_data, log_path, status, trace_rows, chatbot, chat_history


def log_query_handler(query_text: str) -> tuple:
    """Log query with error boundary."""
    try:
        return _log_query_handler_impl(query_text)
    except Exception as e:
        logger.error("log_query_handler() crashed: %s", e, exc_info=True)
        return f"**Internal error**: {e}", [], ""


def _log_query_handler_impl(query_text: str) -> tuple:
    if not query_text.strip():
        return "*Enter a query.*", [], ""

    output = run_agent(image=None, text_prompt=query_text.strip())
    if output["error"]:
        return f"**Error**: {output['error']}", [], ""

    md = _format_agent_result(output)
    alarm_imgs = []
    report_path = ""

    if output.get("intent") in ("inspection_report", "event_log", "fire_log"):
        result = output.get("result", {})
        raw_imgs = result.get("alarm_images", []) or result.get("recent_alarms", [])
        if raw_imgs and isinstance(raw_imgs[0], dict):
            alarm_imgs = [a.get("alarm_image", "") for a in raw_imgs[:4]]
        report_path = result.get("report_path", "")

    return md, alarm_imgs, report_path


def rag_chat(question, top_k, use_llm, history):
    """RAG chat with error boundary."""
    try:
        return _rag_chat_impl(question, top_k, use_llm, history)
    except Exception as e:
        logger.error("rag_chat() crashed: %s", e, exc_info=True)
        return f"**Internal error**: {e}", "", "", "", (history or [])


def _rag_chat_impl(question, top_k, use_llm, history):
    if not question or not question.strip():
        return "*请输入问题*", "", "*来源将在此显示...*", "*检索片段将在此显示...*", history

    from app.config import LLM_MODEL
    from app.rag.rag_tool import rag_query

    result = rag_query(question.strip(), top_k=top_k, use_llm=use_llm, history=history)
    answer = result.get("answer", "*无回答*")
    sources = result.get("source_files", [])
    chunks = result.get("retrieved_chunks", [])

    llm_status = "已使用" if result.get("used_llm") else "未使用"
    model_info = f"**模型**: {LLM_MODEL} | **LLM**: {llm_status} | **Top-K**: {top_k}"
    sources_md = "\n".join(f"- {s}" for s in sources) if sources else "*无匹配来源*"
    chunks_md = "\n\n".join(
        f"**{c.get('source', '?')}** ({c.get('chunk_id', '?')})\n{c.get('text', '')[:200]}..."
        for c in chunks[:3]
    ) if chunks else "*无检索片段*"

    history = history or []
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})

    return answer, model_info, sources_md, chunks_md, history


# ===========================================================================
# Helpers
# ===========================================================================

def _history_to_chatbot(history: list) -> list:
    """Convert [{role, content}, ...] to [{"role": "user", "content": ...}, ...] for gr.Chatbot."""
    pairs = []
    for i in range(0, len(history) - 1, 2):
        user = history[i].get("content", "") if i < len(history) else ""
        bot = history[i + 1].get("content", "") if i + 1 < len(history) else ""
        pairs.append({"role": "user", "content": str(user)})
        pairs.append({"role": "assistant", "content": str(bot)})
    return pairs


def annotate_and_save(image_path, detection_result):
    import cv2
    img = cv2.imread(image_path)
    if img is None:
        return None
    detections = detection_result.get("detections", []) or detection_result.get("objects", [])
    for det in detections:
        bbox = det.get("bbox", [])
        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(img, (x1, y1), (x2, y2), (37, 99, 235), 2)
            label = f"{det.get('class_name', det.get('class', '?'))} {det.get('confidence', 0):.2f}"
            cv2.putText(img, label, (x1, max(y1 - 8, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    out_path = str(Path(image_path).parent / f"annotated_{Path(image_path).name}")
    cv2.imwrite(out_path, img)
    return out_path


def _format_agent_result(output: dict) -> str:
    """Format the normalized orchestrator response for human-readable UI output."""
    intent = output.get("intent", "unknown")
    error = output.get("error", "")
    result = output.get("result", {})

    if error:
        return f"**Error**: {error}"

    planner = output.get("planner_source", "rule")
    lines = [f"**Intent**：{intent}", f"- Planner：`{planner}`"]

    if intent in {"detect", "detect_open"}:
        detections = result.get("detections", [])
        if not detections:
            detections = result.get("detections_json", {}).get("detections", [])
        lines.append(f"- 检测到 **{len(detections)}** 个目标")
        class_counts: dict[str, int] = {}
        for item in detections:
            name = str(item.get("class_name", item.get("class", "unknown")))
            class_counts[name] = class_counts.get(name, 0) + 1
        if class_counts:
            lines.append("- 类别统计：" + "，".join(f"{name} × {count}" for name, count in class_counts.items()))

    elif intent == "chain":
        detection = result.get("detection", {})
        detections = detection.get("detections", detection.get("detections_json", {}).get("detections", []))
        sources = result.get("rag", {}).get("source_files", [])
        lines.append(f"- 视觉检测：**{len(detections)}** 个目标")
        lines.append(f"- RAG 引用：**{len(sources)}** 个来源")
        if result.get("question"):
            lines.append(f"- 自动生成问题：{result['question']}")

    elif intent == "rag":
        sources = result.get("source_files", [])
        lines.append(f"- 检索来源：**{len(sources)}** 个")
        if result.get("answer"):
            lines.append(result["answer"])

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

    elif intent == "disposal":
        order_id = result.get("order_id", "")
        lines.append(f"- 工单：`{order_id or '未生成'}`")
        lines.append(f"- 企业微信通知：{'已发送' if result.get('notification') else '未发送'}")

    elif intent == "unknown":
        lines.append("- 无法判断意图，请提供更明确的指令")

    return "\n".join(lines)


def _format_trace_rows(output: dict) -> list[list]:
    """Convert observable tool steps into a compact table without chain-of-thought."""
    planner = output.get("planner_source", "rule")
    rows = []
    for index, step in enumerate(output.get("trace", []), 1):
        rows.append(
            [
                index,
                planner,
                step.get("tool", "unknown"),
                step.get("status", "unknown"),
                float(step.get("duration_ms", 0.0)),
                step.get("summary", ""),
            ]
        )
    return rows


# ===========================================================================
# Port finder
# ===========================================================================

def _find_free_port(start: int = SERVER_PORT):
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


# ===========================================================================
# Cleanup
# ===========================================================================

def _cleanup_on_exit():
    try:
        from app.rag.vector_store import _close_chroma_client
        _close_chroma_client()
    except Exception:
        pass


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    atexit.register(_cleanup_on_exit)
    ensure_runtime_dirs()
    from app.utils.logging_config import setup_logging
    setup_logging()

    logger.info("=" * 60)
    logger.info("RoboVision Agent starting")
    logger.info("=" * 60)

    port = _find_free_port(SERVER_PORT)
    logger.info(f"Starting on http://{SERVER_HOST}:{port}")

    try:
        demo = build_ui()
    except Exception:
        logger.critical("Failed to build UI", exc_info=True)
        sys.exit(1)

    try:
        demo.launch(
            server_name=SERVER_HOST, server_port=port,
            inbrowser=True, share=False, show_error=True,
        )
    except (SystemExit, KeyboardInterrupt):
        pass
    except Exception:
        logger.critical("Failed to launch Gradio server", exc_info=True)
        sys.exit(1)

# -*- coding: utf-8 -*-
"""Tests for app/ui/detection_tab.py — component structure."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

pytestmark = pytest.mark.ui


class TestBuildDetectionTab:
    """Verify build_detection_tab() returns the correct component dict."""

    @pytest.fixture
    def texts(self):
        return {
            "tab_detect": "\u89c6\u89c9\u68c0\u6d4b",
            "detect_desc": "\u4e0a\u4f20\u56fe\u7247/\u89c6\u9891\u6216\u8f93\u5165\u6444\u50cf\u5934\u5730\u5740",
            "file_label": "\u4e0a\u4f20\u6587\u4ef6\uff08\u56fe\u7247 / \u89c6\u9891\uff09",
            "source_label": "\u89c6\u9891\u6e90 / \u6444\u50cf\u5934 / RTSP",
            "source_placeholder": "\u4f8b\u5982\uff1a0\uff08\u6444\u50cf\u5934\uff09| D:/video.mp4 | rtsp://...",
            "task_label": "\u68c0\u6d4b\u4efb\u52a1",
            "task_choices": ["\u81ea\u52a8\u5224\u65ad", "\u901a\u7528\u7269\u54c1\u68c0\u6d4b", "\u706b\u707e\u70df\u96fe\u9884\u8b66", "\u5b89\u5168\u5e3d\u53cd\u5149\u8863\u5de5\u68c0"],
            "text_label": "\u6587\u672c\u6307\u4ee4",
            "text_placeholder": "\u4f8b\u5982\uff1a\u68c0\u6d4b\u56fe\u4e2d\u6240\u6709\u76ee\u6807",
            "advanced_label": "\u9ad8\u7ea7\u53c2\u6570",
            "conf_label": "\u7f6e\u4fe1\u9608\u503c",
            "stride_label": "\u5e27\u95f4\u9694",
            "max_frames_label": "\u6700\u5927\u5e27\u6570",
            "run_btn": "\u25b6 \u5f00\u59cb\u68c0\u6d4b",
            "summary_heading": "\u68c0\u6d4b\u7ed3\u679c\u6458\u8981",
            "waiting_text": "\u7b49\u5f85\u68c0\u6d4b...",
            "alarm_heading": "\u544a\u8b66\u56fe\u5e93",
            "annotated_label": "\u6ce8\u91ca\u56fe\u50cf",
            "video_label": "\u89c6\u9891\u7ed3\u679c",
            "json_label": "JSON \u7ed3\u679c",
            "log_path_label": "\u65e5\u5fd7\u8def\u5f84",
        }

    def test_returns_dict_with_expected_keys(self, texts):
        import gradio as gr

        from app.ui.detection_tab import build_detection_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_detection_tab(texts)

        assert isinstance(comps, dict)
        expected_keys = {
            "file_input", "source_input", "task_dropdown", "text_input",
            "conf_slider", "stride_slider", "max_frames_slider",
            "run_btn", "summary_md", "alarm_gallery",
            "annotated_image", "video_output", "json_output",
        "log_path_output", "agent_chat_history",
        "status_msg", "trace_table", "agent_chatbot", "clear_btn",
    }
        assert comps.keys() == expected_keys

    def test_component_types(self, texts):
        import gradio as gr

        from app.ui.detection_tab import build_detection_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_detection_tab(texts)

        assert isinstance(comps["file_input"], gr.File)
        assert isinstance(comps["source_input"], gr.Textbox)
        assert isinstance(comps["task_dropdown"], gr.Dropdown)
        assert isinstance(comps["text_input"], gr.Textbox)
        assert isinstance(comps["conf_slider"], gr.Slider)
        assert isinstance(comps["stride_slider"], gr.Slider)
        assert isinstance(comps["max_frames_slider"], gr.Slider)
        assert isinstance(comps["run_btn"], gr.Button)
        assert isinstance(comps["summary_md"], gr.Markdown)
        assert isinstance(comps["alarm_gallery"], gr.Gallery)
        assert isinstance(comps["annotated_image"], gr.Image)
        assert isinstance(comps["video_output"], gr.Video)
        assert isinstance(comps["json_output"], gr.JSON)
        assert isinstance(comps["log_path_output"], gr.Textbox)
        assert isinstance(comps["trace_table"], gr.Dataframe)
        assert isinstance(comps["agent_chat_history"], gr.State)

    def test_slider_ranges(self, texts):
        import gradio as gr

        from app.ui.detection_tab import build_detection_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_detection_tab(texts)

        assert comps["conf_slider"].minimum == 0.1
        assert comps["conf_slider"].maximum == 0.95
        assert comps["conf_slider"].value == 0.4
        assert comps["stride_slider"].minimum == 1
        assert comps["stride_slider"].maximum == 30
        assert comps["stride_slider"].value == 5
        assert comps["max_frames_slider"].minimum == 10
        assert comps["max_frames_slider"].maximum == 500
        assert comps["max_frames_slider"].value == 30

    def test_dropdown_choices(self, texts):
        import gradio as gr

        from app.ui.detection_tab import build_detection_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_detection_tab(texts)

        # Gradio wraps string choices into (label, value) tuples
        choice_labels = [c[0] for c in comps["task_dropdown"].choices]
        assert choice_labels == texts["task_choices"]
        assert comps["task_dropdown"].value == texts["task_choices"][0]


def test_ui_brand_uses_provider_neutral_gemma_name():
    from app.constants import UI_TEXTS

    assert "Ollama Gemma" in UI_TEXTS["zh"]["subtitle"]
    assert "Gemma3" not in UI_TEXTS["zh"]["subtitle"]
    assert "switch_btn" not in UI_TEXTS["zh"]


def test_detection_tasks_expose_open_vocabulary_image_mode():
    from app.constants import UI_TEXTS

    assert "开放词汇检测（图片）" in UI_TEXTS["zh"]["task_choices"]
    assert "Open Vocabulary (Image)" in UI_TEXTS["en"]["task_choices"]


def test_trace_rows_expose_tools_without_chain_of_thought():
    from app.main import _format_trace_rows

    rows = _format_trace_rows(
        {
            "planner_source": "rule",
            "trace": [
                {"tool": "detect", "status": "ok", "duration_ms": 12.5, "summary": "2 objects"},
                {"tool": "rag", "status": "ok", "duration_ms": 3.2, "summary": "1 source"},
            ],
        }
    )
    assert rows == [
        [1, "rule", "detect", "ok", 12.5, "2 objects"],
        [2, "rule", "rag", "ok", 3.2, "1 source"],
    ]


def test_agent_formatter_uses_current_intent_names():
    from app.main import _format_agent_result

    output = {
        "intent": "chain",
        "planner_source": "rule",
        "error": None,
        "result": {
            "detection": {"detections": [{"class_name": "person"}]},
            "rag": {"source_files": ["ppe_rules.md"]},
            "question": "PPE requirements",
        },
    }
    rendered = _format_agent_result(output)
    assert "视觉检测：**1**" in rendered
    assert "RAG 引用：**1**" in rendered

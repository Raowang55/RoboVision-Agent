# -*- coding: utf-8 -*-
"""Tests for app/ui/log_tab.py — component structure."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

pytestmark = pytest.mark.ui


class TestBuildLogTab:
    """Verify build_log_tab() returns the correct component dict."""

    @pytest.fixture
    def texts(self):
        return {
            "tab_logs": "\u65e5\u5fd7\u4e0e\u62a5\u544a",
            "logs_desc": "\u67e5\u8be2\u65e5\u5fd7\u4e0e\u751f\u6210\u62a5\u544a",
            "log_query_label": "\u67e5\u8be2\u5185\u5bb9",
            "log_query_placeholder": "\u8f93\u5165\u67e5\u8be2\u5173\u952e\u8bcd...",
            "log_query_btn": "\u67e5\u8be2",
            "log_result_heading": "\u67e5\u8be2\u7ed3\u679c",
            "log_result_default": "\u7b49\u5f85\u67e5\u8be2...",
            "log_alarm_heading": "\u544a\u8b66\u56fe\u5e93",
            "log_report_label": "\u62a5\u544a\u8def\u5f84",
        }

    def test_returns_dict_with_expected_keys(self, texts):
        import gradio as gr

        from app.ui.log_tab import build_log_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_log_tab(texts)

        assert isinstance(comps, dict)
        expected_keys = {
            "log_query_input", "log_query_btn", "log_result_md",
            "log_alarm_gallery", "log_report_path",
        }
        assert comps.keys() == expected_keys

    def test_component_types(self, texts):
        import gradio as gr

        from app.ui.log_tab import build_log_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_log_tab(texts)

        assert isinstance(comps["log_query_input"], gr.Textbox)
        assert isinstance(comps["log_query_btn"], gr.Button)
        assert isinstance(comps["log_result_md"], gr.Markdown)
        assert isinstance(comps["log_alarm_gallery"], gr.Gallery)
        assert isinstance(comps["log_report_path"], gr.Textbox)

    def test_button_variant(self, texts):
        import gradio as gr

        from app.ui.log_tab import build_log_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_log_tab(texts)

        assert comps["log_query_btn"].variant == "primary"

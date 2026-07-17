# -*- coding: utf-8 -*-
"""Tests for app/ui/rag_tab.py — component structure."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

pytestmark = pytest.mark.ui


class TestBuildRagTab:
    """Verify build_rag_tab() returns the correct component dict."""

    @pytest.fixture
    def texts(self):
        return {
            "tab_rag": "RAG \u77e5\u8bc6\u95ee\u7b54",
            "rag_desc": "\u57fa\u4e8e\u77e5\u8bc6\u5e93\u7684\u667a\u80fd\u95ee\u7b54",
            "rag_question_label": "\u8f93\u5165\u95ee\u9898",
            "rag_question_placeholder": "\u8bf7\u8f93\u5165\u60a8\u7684\u95ee\u9898...",
            "rag_topk_label": "\u76f8\u5173\u6587\u6863\u6570",
            "rag_llm_label": "\u4f7f\u7528 LLM \u603b\u7ed3",
            "rag_btn": "\u67e5\u8be2",
            "rag_answer_title": "\u56de\u7b54",
            "rag_answer_default": "\u7b49\u5f85\u67e5\u8be2...",
            "rag_details_heading": "\u8be6\u60c5",
            "rag_model_label": "\u6a21\u578b\u4fe1\u606f",
            "rag_sources_label": "\u6765\u6e90\u6587\u6863",
            "rag_sources_default": "*\u65e0*",
            "rag_chunks_label": "\u76f8\u5173\u6bb5\u843d",
            "rag_chunks_default": "*\u65e0*",
            "rag_examples_label": "\u793a\u4f8b\u95ee\u9898",
            "rag_examples_text": "\u2022 \u706b\u707e\u9884\u9632\u89c4\u8303\u6709\u54ea\u4e9b\uff1f\n\u2022 \u5b89\u5168\u5e3d\u68c0\u6d4b\u6807\u51c6",
        }

    def test_returns_dict_with_expected_keys(self, texts):
        import gradio as gr

        from app.ui.rag_tab import build_rag_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_rag_tab(texts)

        assert isinstance(comps, dict)
        expected_keys = {
            "rag_question", "rag_top_k", "rag_use_llm", "rag_btn",
            "rag_answer_md", "rag_model_info", "rag_sources_md",
            "rag_chunks_md", "rag_chat_history",
        }
        assert comps.keys() == expected_keys

    def test_component_types(self, texts):
        import gradio as gr

        from app.ui.rag_tab import build_rag_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_rag_tab(texts)

        assert isinstance(comps["rag_question"], gr.Textbox)
        assert isinstance(comps["rag_top_k"], gr.Slider)
        assert isinstance(comps["rag_use_llm"], gr.Checkbox)
        assert isinstance(comps["rag_btn"], gr.Button)
        assert isinstance(comps["rag_answer_md"], gr.Markdown)
        assert isinstance(comps["rag_model_info"], gr.Markdown)
        assert isinstance(comps["rag_sources_md"], gr.Markdown)
        assert isinstance(comps["rag_chunks_md"], gr.Markdown)
        assert isinstance(comps["rag_chat_history"], gr.State)

    def test_slider_defaults(self, texts):
        import gradio as gr

        from app.ui.rag_tab import build_rag_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_rag_tab(texts)

        assert comps["rag_top_k"].minimum == 1
        assert comps["rag_top_k"].maximum == 10
        assert comps["rag_top_k"].value == 4
        assert comps["rag_top_k"].step == 1

    def test_checkbox_default(self, texts):
        import gradio as gr

        from app.config import LLM_ENABLED
        from app.ui.rag_tab import build_rag_tab

        with gr.Blocks():
            with gr.Tabs():
                comps = build_rag_tab(texts)

        assert comps["rag_use_llm"].value is LLM_ENABLED

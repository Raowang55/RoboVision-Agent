# -*- coding: utf-8 -*-
"""RAG Knowledge Q&A tab for the Gradio UI.

Exports build_rag_tab(texts) -> dict of component references
for embedding into the existing gr.Tabs() in app/main.py.
"""

from __future__ import annotations

import gradio as gr

from app.config import LLM_ENABLED


def build_rag_tab(texts: dict) -> dict:
    """Build the RAG tab UI.  Must be called inside a gr.Tabs() context.

    Returns a dict with all Gradio component references.
    """
    with gr.TabItem(texts["tab_rag"], id="rag"):

        gr.Markdown(texts["rag_desc"], elem_classes="tab-desc")

        # Question input
        with gr.Row():
            with gr.Column(scale=6):
                rag_question = gr.Textbox(
                    label=texts["rag_question_label"],
                    placeholder=texts["rag_question_placeholder"], lines=4,
                )
            with gr.Column(scale=1, min_width=180):
                rag_top_k = gr.Slider(1, 10, value=4, step=1,
                                      label=texts["rag_topk_label"])
                rag_use_llm = gr.Checkbox(label=texts["rag_llm_label"],
                                          value=LLM_ENABLED)
                rag_btn = gr.Button(texts["rag_btn"], variant="primary",
                                    elem_classes="primary-btn")

        # Answer + Details
        with gr.Row(equal_height=True):
            with gr.Column(scale=5, elem_classes="section-card"):
                gr.Markdown(f"**{texts['rag_answer_title']}**",
                            elem_classes="section-heading")
                rag_answer_md = gr.Markdown(
                    value=texts["rag_answer_default"],
                    elem_classes="rag-answer",
                )
            with gr.Column(scale=2, min_width=300,
                           elem_classes="section-card-alt"):
                gr.Markdown(f"**{texts['rag_details_heading']}**",
                            elem_classes="section-heading")
                rag_model_info = gr.Markdown(
                    value="", elem_classes="rag-details",
                    label=texts["rag_model_label"],
                )
                rag_sources_md = gr.Markdown(
                    value=texts["rag_sources_default"],
                    elem_classes="rag-details",
                    label=texts["rag_sources_label"],
                )
                rag_chunks_md = gr.Markdown(
                    value=texts["rag_chunks_default"],
                    elem_classes="rag-details",
                    label=texts["rag_chunks_label"],
                )

        # Example questions
        with gr.Accordion(texts["rag_examples_label"], open=False):
            gr.Markdown(texts["rag_examples_text"])

        rag_chat_history = gr.State([])

    return {
        "rag_question": rag_question,
        "rag_top_k": rag_top_k,
        "rag_use_llm": rag_use_llm,
        "rag_btn": rag_btn,
        "rag_answer_md": rag_answer_md,
        "rag_model_info": rag_model_info,
        "rag_sources_md": rag_sources_md,
        "rag_chunks_md": rag_chunks_md,
        "rag_chat_history": rag_chat_history,
    }

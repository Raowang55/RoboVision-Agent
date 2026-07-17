# -*- coding: utf-8 -*-
"""Logs & Reports tab for the Gradio UI.

Exports build_log_tab(texts) -> dict of component references
for embedding into the existing gr.Tabs() in app/main.py.
"""

from __future__ import annotations

import gradio as gr


def build_log_tab(texts: dict) -> dict:
    """Build the Logs tab UI.  Must be called inside a gr.Tabs() context.

    Returns a dict with all Gradio component references.
    """
    with gr.TabItem(texts["tab_logs"], id="logs"):

        gr.Markdown(texts["logs_desc"], elem_classes="tab-desc")

        # Query bar
        with gr.Row():
            log_query_input = gr.Textbox(
                label=texts["log_query_label"],
                placeholder=texts["log_query_placeholder"],
                lines=3, scale=5,
            )
            log_query_btn = gr.Button(
                texts["log_query_btn"], variant="primary",
                elem_classes="primary-btn", scale=1, min_width=160,
            )

        # Results + Gallery
        with gr.Row(equal_height=True):
            with gr.Column(scale=5, elem_classes="section-card"):
                gr.Markdown(f"**{texts['log_result_heading']}**",
                            elem_classes="section-heading")
                log_result_md = gr.Markdown(
                    value=texts["log_result_default"],
                    elem_classes="result-summary",
                )
            with gr.Column(scale=2, min_width=300,
                           elem_classes="section-card-alt"):
                gr.Markdown(f"**{texts['log_alarm_heading']}**",
                            elem_classes="section-heading")
                log_alarm_gallery = gr.Gallery(
                    label="", columns=3, rows=2, height=360,
                )

        log_report_path = gr.Textbox(label=texts["log_report_label"],
                                     interactive=False)

    return {
        "log_query_input": log_query_input,
        "log_query_btn": log_query_btn,
        "log_result_md": log_result_md,
        "log_alarm_gallery": log_alarm_gallery,
        "log_report_path": log_report_path,
    }
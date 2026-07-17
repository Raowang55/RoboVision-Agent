# -*- coding: utf-8 -*-
"""Detection & Agent tab for the Gradio UI.

Exports build_detection_tab(texts) -> dict of component references
for embedding into the existing gr.Tabs() in app/main.py.
"""

from __future__ import annotations

import gradio as gr


def build_detection_tab(texts: dict) -> dict:
    """Build the Detection tab UI.  Must be called inside a gr.Tabs() context.

    Returns a dict with all Gradio component references so the caller
    can wire up event handlers.
    """
    with gr.TabItem(texts["tab_detect"], id="detect"):

        gr.Markdown(texts["detect_desc"], elem_classes="tab-desc")

        # Input Area
        with gr.Row():
            file_input = gr.File(
                label=texts["file_label"], type="filepath",
                file_types=["image", "video"], file_count="single", scale=1,
            )
            source_input = gr.Textbox(
                label=texts["source_label"],
                placeholder=texts["source_placeholder"], lines=2, scale=1,
            )

        with gr.Row():
            task_dropdown = gr.Dropdown(
                choices=texts["task_choices"],
                value=texts["task_choices"][0],
                label=texts["task_label"], scale=1,
            )
            text_input = gr.Textbox(
                label=texts["text_label"],
                placeholder=texts["text_placeholder"], lines=3, scale=1,
            )

        with gr.Accordion(texts["advanced_label"], open=False):
            with gr.Row():
                conf_slider = gr.Slider(0.1, 0.95, value=0.4, step=0.05,
                                        label=texts["conf_label"])
                stride_slider = gr.Slider(1, 30, value=5, step=1,
                                          label=texts["stride_label"])
                max_frames_slider = gr.Slider(10, 500, value=30, step=10,
                                              label=texts["max_frames_label"])

        run_btn = gr.Button(texts["run_btn"], variant="primary",
                            elem_classes="primary-btn")

        # Results
        with gr.Row(equal_height=True):
            with gr.Column(scale=5, elem_classes="section-card"):
                gr.Markdown(f"**{texts['summary_heading']}**",
                            elem_classes="section-heading")
                summary_md = gr.Markdown(value=texts["waiting_text"],
                                         elem_classes="result-summary")
            with gr.Column(scale=2, min_width=300,
                           elem_classes="section-card-alt"):
                gr.Markdown(f"**{texts['alarm_heading']}**",
                            elem_classes="section-heading")
                alarm_gallery = gr.Gallery(
                    label="", columns=3, rows=2, height=360,
                    elem_classes="alarm-gallery",
                )

        with gr.Row():
            annotated_image = gr.Image(label=texts["annotated_label"],
                                       height=480)

        video_output = gr.Video(label=texts["video_label"])

        # Secondary diagnostics stay available without dominating the demo flow.
        detail_label = texts.get("detail_label", "运行详情（JSON / 日志 / Agent 轨迹）")
        with gr.Accordion(detail_label, open=False, elem_classes="run-details"):
            trace_table = gr.Dataframe(
                headers=["步骤", "Planner", "Tool", "状态", "耗时 (ms)", "摘要"],
                datatype=["number", "str", "str", "str", "number", "str"],
                value=[],
                interactive=False,
                wrap=True,
                elem_classes="agent-trace-table",
                label=texts.get("trace_label", "Agent 执行轨迹"),
            )

            status_msg = gr.Textbox(
                label="运行状态",
                value="",
                interactive=False,
                visible=True,
                placeholder="Ready",
                elem_classes="status-message",
                max_lines=1,
            )

            with gr.Row():
                with gr.Column(scale=3, elem_classes="section-card-alt"):
                    gr.Markdown(f"**{texts['json_label']}**",
                                elem_classes="section-heading")
                    json_output = gr.JSON(label="", elem_classes="json-output")
                with gr.Column(scale=1, min_width=240,
                               elem_classes="section-card-alt"):
                    gr.Markdown(f"**{texts['log_path_label']}**",
                                elem_classes="section-heading")
                    log_path_output = gr.Textbox(label="", interactive=False)

            with gr.Row():
                with gr.Column(scale=10):
                    agent_chatbot = gr.Chatbot(
                        label=texts.get("trace_label", "Agent 执行轨迹"),
                        height=260,
                        elem_classes="agent-chatbot",
                        show_label=True,
                    )
                with gr.Column(scale=1, min_width=80):
                    clear_btn = gr.Button(
                        texts.get("clear_label", "清空"),
                        size="sm",
                        elem_classes="secondary-btn",
                    )

        agent_chat_history = gr.State([])

    return {
        "file_input": file_input,
        "source_input": source_input,
        "task_dropdown": task_dropdown,
        "text_input": text_input,
        "conf_slider": conf_slider,
        "stride_slider": stride_slider,
        "max_frames_slider": max_frames_slider,
        "run_btn": run_btn,
        "summary_md": summary_md,
        "alarm_gallery": alarm_gallery,
        "annotated_image": annotated_image,
        "video_output": video_output,
        "json_output": json_output,
        "log_path_output": log_path_output,
        "status_msg": status_msg,
        "trace_table": trace_table,
        "agent_chatbot": agent_chatbot,
        "clear_btn": clear_btn,
        "agent_chat_history": agent_chat_history,
    }

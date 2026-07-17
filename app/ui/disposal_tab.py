# -*- coding: utf-8 -*-
"""Event Disposal tab for Gradio UI.


Exports build_disposal_tab(texts) -> gr.TabItem for embedding into

the existing gr.Tabs() in app/main.py.


Layout: professional industrial console, dark blue theme,

left-right split with input on left, results on right.

"""


from __future__ import annotations

import json

import gradio as gr

from app.agents.samples import SAMPLE_ALARM, SAMPLE_ALARM_LOW, SAMPLE_ALARM_MEDIUM


def load_alarm_sample(alarm_level: str) -> tuple[str, str]:
    """Return one validated sample JSON string and its level badge."""
    samples = {
        "HIGH": SAMPLE_ALARM,
        "MEDIUM": SAMPLE_ALARM_MEDIUM,
        "LOW": SAMPLE_ALARM_LOW,
    }
    data = json.loads(samples.get(alarm_level, SAMPLE_ALARM))
    level = str(data.get("alarm_level", "?"))
    badge_class = {
        "HIGH": "level-badge-high",
        "MEDIUM": "level-badge-medium",
        "LOW": "level-badge-low",
    }.get(level, "")
    emoji = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢"}.get(level, "⚠")
    level_html = f'<span class="{badge_class}">{emoji} {level} 级</span>'
    return json.dumps(data, ensure_ascii=False, indent=2), level_html


def build_disposal_tab(texts: dict) -> gr.TabItem:

    """Build the 'Event Disposal' tab.


    Args:

        texts: UI translation dict (zh/en keys), same format as app/main.py UI_TEXTS.


    Returns:

        gr.TabItem ready to be added to gr.Tabs().

    """

    lang = texts.get("_lang", "zh")


    if lang == "en":

        t = {

            "tab_name": "Event Disposal",

            "desc": "Input alarm JSON to trigger the rule-based disposal workflow. "

                     "Supports HIGH/MEDIUM/LOW routing with enterprise WeChat notification.",

            "input_label": "Alarm JSON Input",

            "input_placeholder": "Paste alarm JSON here...",

            "load_sample_btn": "Load Sample",

            "level_label": "Alarm Level",

            "level_placeholder": "Detection result will appear here...",

            "run_btn": "Start Disposal",

            "steps_heading": "Disposal Workflow",

            "step1": "1. Event Analysis",

            "step2": "2. Regulation Search",

            "step3": "3. Emergency Linkage",

            "step4": "4. Dispatch Orders",

            "step5": "5. Final Report",

            "report_heading": "Final Report",

            "report_default": "*Disposal report will appear here...*",

            "order_heading": "Work Order",

            "notification_label": "Notification Status",

            "sample_high": "HIGH - Fire",

            "sample_medium": "MEDIUM - Smoke",

            "sample_low": "LOW - PPE Violation",

        }

    else:

        t = {

            "tab_name": "事件处置",

            "desc": "输入告警 JSON 触发规则化处置工作流，支持 HIGH/MEDIUM/LOW 分级路由与企业微信通知。",

            "input_label": "告警 JSON 输入",

            "input_placeholder": "粘贴告警 JSON 数据...",

            "load_sample_btn": "加载示例",

            "level_label": "告警级别",

            "level_placeholder": "检测结果将在此显示...",

            "run_btn": "启动处置",

            "steps_heading": "处置工作流",

            "step1": "1. 事件分析",

            "step2": "2. 法规检索",

            "step3": "3. 应急联动",

            "step4": "4. 派工单下发",

            "step5": "5. 最终报告",

            "report_heading": "最终报告",

            "report_default": "*处置报告将在此显示...*",

            "order_heading": "工单信息",

            "notification_label": "通知状态",

            "sample_high": "高级 - 火灾",

            "sample_medium": "中级 - 烟雾",

            "sample_low": "低级 - PPE 违规",

            "input_header": "告警输入",

            "input_subtitle": "粘贴告警 JSON 或加载示例告警",

            "sample_label": "示例告警：",

            "execute_title": "执行处置",

            "execute_desc": "触发规则化事件处置工作流",

            "workflow_header": "处置工作流",

            "workflow_subtitle": "按步骤展示处置执行结果",

            "waiting_input": "*等待输入...*",

            "pending": "*等待执行...*",

            "high_trigger": "*HIGH 级告警时触发*",

            "notification_waiting": "等待处置...",

            "work_order_label": "工单详情",

        }


    # Default sample JSON

    default_alarm = SAMPLE_ALARM


    with gr.TabItem(t["tab_name"], id="disposal") as tab:

        # Description banner

        gr.Markdown(

            f'<div class="tab-desc">{t["desc"]}</div>',

        )


        with gr.Row(equal_height=True):

            # ===== LEFT COLUMN: Input Panel =====

            with gr.Column(scale=5, elem_classes="section-card"):

                # Input header

                gr.HTML(f"""

                <div class="alarm-section-header">

                    <div class="alarm-section-icon">&#9888;</div>

                    <div>

                        <div class="alarm-section-title">{t.get("input_header", "ALARM INPUT")}</div>

                        <div class="alarm-section-subtitle">{t.get("input_subtitle", "Paste or load a sample alarm JSON")}</div>


                    </div>

                </div>

                """)


                # JSON input area

                alarm_input = gr.Code(

                    label=t["input_label"],

                    language="json",

                    lines=14,

                    value=default_alarm,

                )


                # Sample buttons - styled as pills

                gr.HTML(f"""

                <div style="display:flex;gap:10px;margin:12px 0 8px;flex-wrap:wrap;">

                    <span class="sample-label">{t.get("sample_label", "Samples:")}</span>

                </div>

                """)

                with gr.Row():

                    sample_high_btn = gr.Button(

                        t["sample_high"], size="sm", variant="secondary",

                        elem_classes="secondary-btn",

                    )

                    sample_medium_btn = gr.Button(

                        t["sample_medium"], size="sm", variant="secondary",

                        elem_classes="secondary-btn",

                    )

                    sample_low_btn = gr.Button(

                        t["sample_low"], size="sm", variant="secondary",

                        elem_classes="secondary-btn",

                    )


                # Level display

                alarm_level_display = gr.Textbox(

                    label=t["level_label"],

                    value=t["level_placeholder"],

                    interactive=False,

                    elem_classes="level-display",

                )


                # Run button

                gr.HTML(f"""

                <div class="execute-info-box">

                    <div class="execute-info-title">{t.get("execute_title", "Execute")}</div>

                    <div style="font-size:0.76rem;color:#94a3b8;">{t.get("execute_desc", "Trigger the disposal workflow")}</div>

                </div>

                """)

                run_btn = gr.Button(

                    t["run_btn"],

                    variant="primary",

                    elem_classes="primary-btn",

                    size="lg",

                )


                # Notification status

                notification_status = gr.Textbox(

                    label=t["notification_label"],

                    value=t.get("notification_waiting", "Awaiting disposal..."),

                    interactive=False,

                    elem_classes="notification-status",

                )


            # ===== RIGHT COLUMN: Results Panel =====

            with gr.Column(scale=7, elem_classes="section-card"):

                # Results header

                gr.HTML(f"""

                <div class="alarm-section-header">

                    <div class="alarm-section-icon alarm-section-icon-alt">&#9776;</div>

                    <div>

                        <div class="alarm-section-title">{t.get("workflow_header", "DISPOSAL WORKFLOW")}</div>

                        <div class="alarm-section-subtitle">{t.get("workflow_subtitle", "Step-by-step workflow execution")}</div>

                    </div>

                </div>

                """)


                # Step-by-step accordions with visual step indicators

                with gr.Accordion(t["step1"], open=True, elem_classes="disposal-accordion"):

                    step1_output = gr.Markdown(value=t.get("waiting_input", "*Awaiting input...*"))


                with gr.Accordion(t["step2"], open=False, elem_classes="disposal-accordion"):

                    step2_output = gr.Markdown(value=t.get("pending", "*Pending...*"))


                with gr.Accordion(t["step3"], open=False, elem_classes="disposal-accordion"):

                    step3_output = gr.Markdown(value=t.get("high_trigger", "*Triggered for HIGH level...*"))


                with gr.Accordion(t["step4"], open=False, elem_classes="disposal-accordion"):

                    step4_output = gr.Markdown(value=t.get("pending", "*Pending...*"))


                with gr.Accordion(t["step5"], open=False, elem_classes="disposal-accordion"):

                    step5_output = gr.Markdown(value=t.get("pending", "*Pending...*"))


                # Final report

                gr.Markdown(f"**{t['report_heading']}**", elem_classes="section-heading")

                final_report = gr.Markdown(

                    value=t["report_default"],

                    elem_classes="result-summary",

                )


                # Work order JSON

                gr.Markdown(f"**{t['order_heading']}**", elem_classes="section-heading")

                work_order_display = gr.JSON(

                    label=t.get("work_order_label", "Work Order"),

                    value=None,

                )


        # ===== Event handlers =====


        sample_high_btn.click(

            fn=lambda: load_alarm_sample("HIGH"),

            inputs=[],

            outputs=[alarm_input, alarm_level_display],

        )

        sample_medium_btn.click(

            fn=lambda: load_alarm_sample("MEDIUM"),

            inputs=[],

            outputs=[alarm_input, alarm_level_display],

        )

        sample_low_btn.click(

            fn=lambda: load_alarm_sample("LOW"),

            inputs=[],

            outputs=[alarm_input, alarm_level_display],

        )


        def run_disposal_handler(alarm_json_str: str) -> tuple:

            """Execute the full disposal workflow and return step results.

            Note: Error boundary wrapper. Any exception from the inner dispatch is
            caught and returned as structured error outputs so the UI never crashes.
            """
            try:
                return _run_disposal_handler_impl(alarm_json_str)
            except Exception as e:
                import traceback
                traceback.print_exc()
                err_msg = f"**处置流程错误**：{e}"
                empty = "*内部错误导致处置失败*"
                return (err_msg, empty, empty, empty, empty, empty, None,
                        f'<span style="color:#ef4444;">❌ 处置流程错误：{e}</span>')


        def _run_disposal_handler_impl(alarm_json_str: str) -> tuple:

            """Inner disposal handler implementation."""

            if not alarm_json_str or not alarm_json_str.strip():

                empty = "*请输入告警 JSON*"

                return (empty, empty, empty, empty, empty, empty, None, "未执行")


            from app.agents.graph import run_disposal


            try:
                result = run_disposal(alarm_json_str)
            except Exception as e:
                import traceback
                traceback.print_exc()
                err_msg = f"**处置流程错误**：{e}"
                empty = "*内部错误导致处置失败*"
                return (err_msg, empty, empty, empty, empty, empty, None,
                        f'<span style="color:#ef4444;">\u274c 处置流程错误：{e}</span>')


            report = result.get("report", "*处置失败*")

            steps = result.get("steps", [])

            order_id = result.get("order_id", "")

            notification = result.get("notification", False)

            notification_status = result.get("notification_status", "")

            notification_detail = result.get("notification_detail", "")

            error = result.get("error", "")


            # Map steps to accordion outputs

            step_texts = {

                "supervisor_judge": "",

                "event_analysis": "",

                "regulation_search": "",

                "emergency_linkage": "",

                "dispatch_order": "",

                "final_summary": "",

            }


            for s in steps:

                name = s.get("step", "")

                content = s.get("content", "")

                ts = s.get("timestamp", "")

                if name in step_texts:

                    step_texts[name] = f"*{ts}*\n\n{content}"


            s1 = step_texts.get("supervisor_judge", "") or step_texts.get("event_analysis", "") or "*暂无数据*"

            s2 = step_texts.get("regulation_search", "") or "*未找到匹配的安全规范*"

            s3 = step_texts.get("emergency_linkage", "") or "*未触发应急联动*"

            s4 = step_texts.get("dispatch_order", "") or "*派工单尚未完成*"

            s5 = step_texts.get("final_summary", "") or "*最终报告尚未生成*"


            if error:

                s1 = f"**错误**：{error}"


            # Notification status with visual indicator

            if notification:

                notif_text = "✅ 已推送至企业微信：接口已确认接收"

            elif notification_status in {"disabled", "missing_webhook", "not_requested"}:

                notif_text = f"⚪ 未推送：{notification_detail or '企业微信通知未启用'}"

            else:

                notif_text = f"⚠ 推送失败：{notification_detail or '请查看应用日志'}"


            order_info = {

                "order_id": order_id,

                "notification": notification,

                "steps_count": len(steps),

                "error": error,

            } if order_id else None


            return s1, s2, s3, s4, s5, report, order_info, notif_text


        run_btn.click(

            fn=run_disposal_handler,

            inputs=[alarm_input],

            outputs=[

                step1_output,

                step2_output,

                step3_output,

                step4_output,

                step5_output,

                final_report,

                work_order_display,

                notification_status,

            ],

        )


    return tab

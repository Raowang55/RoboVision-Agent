"""Event Disposal tab for Gradio UI.

Exports build_disposal_tab(texts) -> gr.TabItem for embedding into
the existing gr.Tabs() in app/main.py.

Layout: professional industrial console, dark blue theme,
left-right split with input on left, results on right.
"""

from __future__ import annotations

import json
import gradio as gr


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
            "desc": "Input alarm JSON to trigger multi-agent collaborative disposal. "
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
            "desc": "输入告警 JSON 触发多 Agent 协同处置，支持 HIGH/MEDIUM/LOW 分级路由与企业微信通知。",
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
        }

    # Default sample JSON
    DEFAULT_ALARM = json.dumps({
        "event_id": "ALARM20260624001",
        "event_type": "fire",
        "alarm_level": "HIGH",
        "confidence": 0.92,
        "location": "Factory 3 Welding Area",
        "timestamp": "2026-06-24 14:30:25",
        "image_path": "data/alarms/fire/alarm_HIGH_20260624_121834.jpg",
        "bbox": [320.5, 180.2, 540.8, 420.1],
        "reason": "Fire detected for 3 consecutive frames",
    }, ensure_ascii=False, indent=2)

    with gr.TabItem(t["tab_name"], id="disposal") as tab:
        # Description banner
        gr.Markdown(
            f'<div class="tab-desc">{t["desc"]}</div>',
        )

        with gr.Row(equal_height=True):
            # ===== LEFT COLUMN: Input Panel =====
            with gr.Column(scale=5, elem_classes="section-card"):
                # Input header
                gr.HTML("""
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;padding-bottom:10px;border-bottom:2px solid #1e293b;">
                    <div style="width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#2563eb,#3b82f6);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;flex-shrink:0;">&#9888;</div>
                    <div>
                        <div style="font-weight:700;font-size:0.92rem;color:#f1f5f9;letter-spacing:.03em;">ALARM INPUT</div>
                        <div style="font-size:0.78rem;color:#94a3b8;">Paste or load a sample alarm JSON</div>
                    </div>
                </div>
                """)

                # JSON input area
                alarm_input = gr.Code(
                    label=t["input_label"],
                    language="json",
                    lines=14,
                    value=DEFAULT_ALARM,
                )

                # Sample buttons - styled as pills
                gr.HTML("""
                <div style="display:flex;gap:10px;margin:12px 0 8px;flex-wrap:wrap;">
                    <span style="font-size:0.78rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;font-weight:600;align-self:center;">Samples:</span>
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
                gr.HTML("""
                <div style="margin:16px 0 4px;padding:10px 14px;background:rgba(59,130,246,.08);border-radius:8px;border:1px solid rgba(59,130,246,.15);">
                    <div style="font-size:0.78rem;color:#60a5fa;text-transform:uppercase;letter-spacing:.05em;font-weight:600;margin-bottom:4px;">Execute</div>
                    <div style="font-size:0.76rem;color:#94a3b8;">Trigger the multi-agent disposal pipeline</div>
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
                    value="Awaiting disposal...",
                    interactive=False,
                    elem_classes="notification-status",
                )

            # ===== RIGHT COLUMN: Results Panel =====
            with gr.Column(scale=7, elem_classes="section-card"):
                # Results header
                gr.HTML("""
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;padding-bottom:10px;border-bottom:2px solid #1e293b;">
                    <div style="width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#1e40af,#3b82f6);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;flex-shrink:0;">&#9776;</div>
                    <div>
                        <div style="font-weight:700;font-size:0.92rem;color:#f1f5f9;letter-spacing:.03em;">DISPOSAL WORKFLOW</div>
                        <div style="font-size:0.78rem;color:#94a3b8;">Step-by-step multi-agent execution</div>
                    </div>
                </div>
                """)

                # Step-by-step accordions with visual step indicators
                with gr.Accordion(t["step1"], open=True, elem_classes="disposal-accordion"):
                    step1_output = gr.Markdown(value="*Awaiting input...*")

                with gr.Accordion(t["step2"], open=False, elem_classes="disposal-accordion"):
                    step2_output = gr.Markdown(value="*Pending...*")

                with gr.Accordion(t["step3"], open=False, elem_classes="disposal-accordion"):
                    step3_output = gr.Markdown(value="*Triggered for HIGH level...*")

                with gr.Accordion(t["step4"], open=False, elem_classes="disposal-accordion"):
                    step4_output = gr.Markdown(value="*Pending...*")

                with gr.Accordion(t["step5"], open=False, elem_classes="disposal-accordion"):
                    step5_output = gr.Markdown(value="*Pending...*")

                # Final report
                gr.Markdown(f"**{t['report_heading']}**", elem_classes="section-heading")
                final_report = gr.Markdown(
                    value=t["report_default"],
                    elem_classes="result-summary",
                )

                # Work order JSON
                gr.Markdown(f"**{t['order_heading']}**", elem_classes="section-heading")
                work_order_display = gr.JSON(
                    label="Work Order",
                    value=None,
                )

        # ===== Event handlers =====

        def load_sample(alarm_level: str) -> tuple:
            """Load sample alarm JSON by level."""
            from core.mock import SAMPLE_ALARM, SAMPLE_ALARM_MEDIUM, SAMPLE_ALARM_LOW

            samples = {
                "HIGH": SAMPLE_ALARM,
                "MEDIUM": SAMPLE_ALARM_MEDIUM,
                "LOW": SAMPLE_ALARM_LOW,
            }
            data = samples.get(alarm_level, SAMPLE_ALARM)
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            level = data.get("alarm_level", "?")
            badge_class = {"HIGH": "level-badge-high", "MEDIUM": "level-badge-medium", "LOW": "level-badge-low"}.get(level, "")
            emoji = {"HIGH": "\U0001F534", "MEDIUM": "\U0001F7E0", "LOW": "\U0001F7E2"}.get(level, "\u26A0")
            level_html = f'<span class="{badge_class}">{emoji} {level} LEVEL</span>'
            return json_str, level_html

        sample_high_btn.click(
            fn=lambda: load_sample("HIGH"),
            inputs=[],
            outputs=[alarm_input, alarm_level_display],
        )
        sample_medium_btn.click(
            fn=lambda: load_sample("MEDIUM"),
            inputs=[],
            outputs=[alarm_input, alarm_level_display],
        )
        sample_low_btn.click(
            fn=lambda: load_sample("LOW"),
            inputs=[],
            outputs=[alarm_input, alarm_level_display],
        )

        def run_disposal_handler(alarm_json_str: str) -> tuple:
            """Execute the full disposal workflow and return step results."""
            if not alarm_json_str or not alarm_json_str.strip():
                empty = "*Please enter alarm JSON*"
                return (empty, empty, empty, empty, empty, empty, None, "Not executed")

            from core.graph import run_disposal

            result = run_disposal(alarm_json_str)

            report = result.get("report", "*Disposal failed*")
            steps = result.get("steps", [])
            order_id = result.get("order_id", "")
            notification = result.get("notification", False)
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

            s1 = step_texts.get("supervisor_judge", "") or step_texts.get("event_analysis", "") or "*No data*"
            s2 = step_texts.get("regulation_search", "") or "*No matching regulation found*"
            s3 = step_texts.get("emergency_linkage", "") or "*Emergency linkage not triggered*"
            s4 = step_texts.get("dispatch_order", "") or "*Dispatch not completed*"
            s5 = step_texts.get("final_summary", "") or "*Report not generated*"

            if error:
                s1 = f"**Error**: {error}"

            # Notification status with visual indicator
            if notification:
                notif_text = '<span style="color:#22c55e;">\u2705 Pushed to enterprise WeChat</span>'
            else:
                notif_text = '<span style="color:#f59e0b;">\u26A0 Not pushed (Mock mode or push failed)</span>'

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

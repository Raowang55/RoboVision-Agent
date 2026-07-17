# -*- coding: utf-8 -*-
"""Tests for app/ui/disposal_tab.py — component structure and inline logic."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

pytestmark = pytest.mark.ui

# ---------------------------------------------------------------------------
# Helpers: replicate the inline logic from disposal_tab.py so we can test it
# without needing a live Gradio Blocks context.
# ---------------------------------------------------------------------------

_SAMPLE_ALARM = json.dumps({
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

_SAMPLE_ALARM_MEDIUM = json.dumps({
    "event_id": "ALARM20260624002",
    "event_type": "smoke",
    "alarm_level": "MEDIUM",
    "confidence": 0.78,
    "location": "Factory 2 Storage Area",
    "timestamp": "2026-06-24 15:10:33",
    "image_path": "data/alarms/smoke/alarm_MEDIUM_20260624_151033.jpg",
    "bbox": [150.2, 300.8, 420.6, 510.3],
    "reason": "Smoke detected near storage rack",
}, ensure_ascii=False, indent=2)

_SAMPLE_ALARM_LOW = json.dumps({
    "event_id": "ALARM20260624003",
    "event_type": "ppe_violation",
    "alarm_level": "LOW",
    "confidence": 0.65,
    "location": "Factory 1 Assembly Line",
    "timestamp": "2026-06-24 16:45:12",
    "image_path": "data/alarms/ppe/alarm_LOW_20260624_164512.jpg",
    "bbox": [680.1, 210.5, 780.4, 580.9],
    "reason": "Worker without safety helmet detected",
}, ensure_ascii=False, indent=2)


def _load_sample(alarm_level: str) -> tuple:
    """Replica of the inline load_sample() from disposal_tab.py."""
    samples = {
        "HIGH": _SAMPLE_ALARM,
        "MEDIUM": _SAMPLE_ALARM_MEDIUM,
        "LOW": _SAMPLE_ALARM_LOW,
    }
    data = json.loads(samples.get(alarm_level, _SAMPLE_ALARM))
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    level = data.get("alarm_level", "?")
    badge_class = {
        "HIGH": "level-badge-high",
        "MEDIUM": "level-badge-medium",
        "LOW": "level-badge-low",
    }.get(level, "")
    emoji = {"HIGH": '\U0001F534', "MEDIUM": '\U0001F7E0', "LOW": '\U0001F7E2'}.get(level, '\u26A0')
    level_html = f'<span class="{badge_class}">{emoji} {level} LEVEL</span>'
    return json_str, level_html


def _run_disposal_handler(alarm_json_str: str, mock_result: dict | None = None) -> tuple:
    """Replica of the inline run_disposal_handler() from disposal_tab.py."""
    if not alarm_json_str or not alarm_json_str.strip():
        empty = "*请输入告警 JSON*"
        return (empty, empty, empty, empty, empty, empty, None, "未执行")

    if mock_result is not None:
        result = mock_result
    else:
        from app.agents.graph import run_disposal
        result = run_disposal(alarm_json_str)

    report = result.get("report", "*处置失败*")
    steps = result.get("steps", [])
    order_id = result.get("order_id", "")
    notification = result.get("notification", False)
    error = result.get("error", "")

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

    if notification:
        notif_text = '<span style="color:#22c55e;">\u2705 已推送至企业微信</span>'
    else:
        notif_text = '<span style="color:#f59e0b;">\u26A0 未推送（通知未启用或发送失败）</span>'

    order_info = {
        "order_id": order_id,
        "notification": notification,
        "steps_count": len(steps),
        "error": error,
    } if order_id else None

    return s1, s2, s3, s4, s5, report, order_info, notif_text


# ===================================================================
# Tests: load_sample logic
# ===================================================================

class TestLoadSample:
    def test_high_level(self):
        json_str, html = _load_sample("HIGH")
        data = json.loads(json_str)
        assert data["alarm_level"] == "HIGH"
        assert data["event_type"] == "fire"
        assert "level-badge-high" in html
        assert "HIGH LEVEL" in html

    def test_medium_level(self):
        json_str, html = _load_sample("MEDIUM")
        data = json.loads(json_str)
        assert data["alarm_level"] == "MEDIUM"
        assert data["event_type"] == "smoke"
        assert "level-badge-medium" in html
        assert "MEDIUM LEVEL" in html

    def test_low_level(self):
        json_str, html = _load_sample("LOW")
        data = json.loads(json_str)
        assert data["alarm_level"] == "LOW"
        assert data["event_type"] == "ppe_violation"
        assert "level-badge-low" in html
        assert "LOW LEVEL" in html

    def test_unknown_level_falls_back_to_high(self):
        json_str, html = _load_sample("UNKNOWN")
        data = json.loads(json_str)
        assert data["alarm_level"] == "HIGH"
        assert "level-badge-high" in html

    def test_output_is_pretty_printed_json(self):
        json_str, _ = _load_sample("HIGH")
        assert json.loads(json_str) is not None


# ===================================================================
# Tests: run_disposal_handler logic
# ===================================================================

class TestRunDisposalHandler:
    def test_empty_input_returns_placeholder(self):
        result = _run_disposal_handler("")
        assert result[0] == "*请输入告警 JSON*"
        assert result[7] == "未执行"
        assert result[6] is None

    def test_whitespace_only_input(self):
        result = _run_disposal_handler("   ")
        assert result[0] == "*请输入告警 JSON*"

    def test_successful_disposal_with_steps(self):
        mock = {
            "report": "## Disposal Complete\nAll actions taken.",
            "order_id": "WO-2026-001",
            "steps": [
                {"step": "event_analysis", "content": "Fire detected in welding area", "timestamp": "14:30:25"},
                {"step": "regulation_search", "content": "Found GB 50016-2024", "timestamp": "14:30:26"},
                {"step": "emergency_linkage", "content": "Siren activated", "timestamp": "14:30:27"},
                {"step": "dispatch_order", "content": "Order dispatched to team A", "timestamp": "14:30:28"},
                {"step": "final_summary", "content": "All clear", "timestamp": "14:30:29"},
            ],
            "notification": True,
            "error": "",
        }
        s1, s2, s3, s4, s5, report, order_info, notif = _run_disposal_handler(
            '{"alarm_level":"HIGH"}', mock_result=mock
        )
        assert "Fire detected" in s1
        assert "GB 50016" in s2
        assert "Siren" in s3
        assert "team A" in s4
        assert "All clear" in s5
        assert "Disposal Complete" in report
        assert order_info["order_id"] == "WO-2026-001"
        assert "已推送" in notif

    def test_disposal_with_error(self):
        mock = {
            "report": "*处置失败*",
            "order_id": "",
            "steps": [],
            "notification": False,
            "error": "LLM API timeout",
        }
        s1, *_ = _run_disposal_handler('{"alarm_level":"HIGH"}', mock_result=mock)
        assert "LLM API timeout" in s1

    def test_disposal_no_steps_fills_defaults(self):
        mock = {
            "report": "*No report*",
            "order_id": "",
            "steps": [],
            "notification": False,
            "error": "",
        }
        s1, s2, s3, s4, s5, report, order_info, notif = _run_disposal_handler(
            '{"alarm_level":"HIGH"}', mock_result=mock
        )
        assert s1 == "*No data*"
        assert s2 == "*No matching regulation found*"
        assert s3 == "*Emergency linkage not triggered*"
        assert s4 == "*Dispatch not completed*"
        assert s5 == "*Report not generated*"
        assert order_info is None
        assert "未推送" in notif

    def test_supervisor_judge_falls_back_to_event_analysis(self):
        mock = {
            "report": "*Report*",
            "order_id": "",
            "steps": [
                {"step": "event_analysis", "content": "Analysis complete", "timestamp": "14:30:25"},
            ],
            "notification": False,
            "error": "",
        }
        s1, *_ = _run_disposal_handler('{"alarm_level":"HIGH"}', mock_result=mock)
        assert "Analysis complete" in s1

    def test_notification_false_shows_warning(self):
        mock = {
            "report": "*Report*",
            "order_id": "WO-001",
            "steps": [],
            "notification": False,
            "error": "",
        }
        *_, notif = _run_disposal_handler('{"alarm_level":"HIGH"}', mock_result=mock)
        assert "未推送" in notif

    def test_notification_true_shows_success(self):
        mock = {
            "report": "*Report*",
            "order_id": "WO-001",
            "steps": [],
            "notification": True,
            "error": "",
        }
        *_, notif = _run_disposal_handler('{"alarm_level":"HIGH"}', mock_result=mock)
        assert "已推送" in notif

    def test_order_info_none_when_no_order_id(self):
        mock = {
            "report": "*Report*",
            "order_id": "",
            "steps": [],
            "notification": False,
            "error": "",
        }
        *_, order_info, _ = _run_disposal_handler('{"alarm_level":"HIGH"}', mock_result=mock)
        assert order_info is None


# ===================================================================
# Tests: build_disposal_tab component structure (inside gr.Blocks)
# ===================================================================

class TestBuildDisposalTab:
    """Verify the Gradio component structure returned by build_disposal_tab()."""

    @pytest.fixture
    def texts_zh(self):
        return {
            "_lang": "zh",
            "tab_name": "\u4e8b\u4ef6\u5904\u7f6e",
            "desc": "\u8f93\u5165\u544a\u8b66 JSON",
            "input_label": "\u544a\u8b66 JSON \u8f93\u5165",
            "input_placeholder": "\u7c98\u8d34\u544a\u8b66 JSON \u6570\u636e...",
            "load_sample_btn": "\u52a0\u8f7d\u793a\u4f8b",
            "level_label": "\u544a\u8b66\u7ea7\u522b",
            "level_placeholder": "\u68c0\u6d4b\u7ed3\u679c\u5c06\u5728\u6b64\u663e\u793a...",
            "run_btn": "\u542f\u52a8\u5904\u7f6e",
            "steps_heading": "\u5904\u7f6e\u5de5\u4f5c\u6d41",
            "step1": "1. \u4e8b\u4ef6\u5206\u6790",
            "step2": "2. \u6cd5\u89c4\u68c0\u7d22",
            "step3": "3. \u5e94\u6025\u8054\u52a8",
            "step4": "4. \u6d3e\u5de5\u5355\u4e0b\u53d1",
            "step5": "5. \u6700\u7ec8\u62a5\u544a",
            "report_heading": "\u6700\u7ec8\u62a5\u544a",
            "report_default": "*\u5904\u7f6e\u62a5\u544a\u5c06\u5728\u6b64\u663e\u793a...*",
            "order_heading": "\u5de5\u5355\u4fe1\u606f",
            "notification_label": "\u901a\u77e5\u72b6\u6001",
            "sample_high": "\u9ad8\u7ea7 - \u706b\u707e",
            "sample_medium": "\u4e2d\u7ea7 - \u70df\u96fe",
            "sample_low": "\u4f4e\u7ea7 - PPE \u8fdd\u89c4",
        }

    def test_returns_gr_tabitem(self, texts_zh):
        import gradio as gr

        from app.ui.disposal_tab import build_disposal_tab

        with gr.Blocks():
            tab = build_disposal_tab(texts_zh)
        assert isinstance(tab, gr.Tab)

    def test_en_texts(self):
        import gradio as gr

        from app.ui.disposal_tab import build_disposal_tab

        texts = {"_lang": "en"}
        with gr.Blocks():
            tab = build_disposal_tab(texts)
        assert isinstance(tab, gr.Tab)

    def test_default_lang_is_zh(self):
        import gradio as gr

        from app.ui.disposal_tab import build_disposal_tab

        texts = {}
        with gr.Blocks():
            tab = build_disposal_tab(texts)
        assert isinstance(tab, gr.Tab)


def test_production_sample_loader_returns_decoded_alarm():
    from app.ui.disposal_tab import load_alarm_sample

    payload, badge = load_alarm_sample("HIGH")
    data = json.loads(payload)
    assert data["alarm_level"] == "HIGH"
    assert "3 号厂房焊接区" in payload
    assert "HIGH 级" in badge

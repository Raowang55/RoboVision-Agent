# -*- coding: utf-8 -*-
"""Tests for alarm samples, linkage rules, and notification adapters."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestAlarmSamples:
    def test_sample_alarm_high_structure(self):
        from app.agents.samples import SAMPLE_ALARM
        data = json.loads(SAMPLE_ALARM)
        assert data["alarm_level"] == "HIGH"
        assert data["event_type"] == "fire"

    def test_sample_alarm_medium_structure(self):
        from app.agents.samples import SAMPLE_ALARM_MEDIUM
        data = json.loads(SAMPLE_ALARM_MEDIUM)
        assert data["alarm_level"] == "MEDIUM"
        assert data["event_type"] == "smoke"

    def test_sample_alarm_low_structure(self):
        from app.agents.samples import SAMPLE_ALARM_LOW
        data = json.loads(SAMPLE_ALARM_LOW)
        assert data["alarm_level"] == "LOW"
        assert data["event_type"] == "ppe_violation"

    def test_emergency_linkage_plan(self):
        from app.agents.linkage import build_emergency_linkage_plan

        result = build_emergency_linkage_plan({"event_type": "fire", "location": "Factory A"})
        assert "规则化应急联动方案" in result
        assert "Factory A" in result
        assert "确认执行" in result

    def test_emergency_linkage_plan_no_location(self):
        from app.agents.linkage import build_emergency_linkage_plan

        result = build_emergency_linkage_plan({"event_type": "smoke"})
        assert "未知位置" in result

    def test_send_wechat_notification_disabled(self):
        from app.agents.notifications import send_wechat_notification
        result = send_wechat_notification(
            event_type="fire", alarm_level="HIGH",
            location="Factory", summary="Test",
        )
        assert result is False

    def test_wechat_readiness_reports_disabled_reason(self):
        from app.agents.notifications import notification_readiness

        result = notification_readiness()
        assert result.ok is False
        assert result.status in {"disabled", "missing_webhook"}

    def test_wechat_detail_returns_api_confirmation(self, monkeypatch):
        import app.agents.notifications as notifications

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"errcode": 0, "errmsg": "ok"}'

        monkeypatch.setattr(notifications, "WECHAT_ENABLED", True)
        monkeypatch.setattr(notifications, "WECHAT_WEBHOOK_KEY", "test-key")
        monkeypatch.setattr(notifications.urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse())
        result = notifications.send_wechat_notification_detail("fire", "HIGH", "Factory", "Test")
        assert result.ok is True
        assert result.status == "sent"

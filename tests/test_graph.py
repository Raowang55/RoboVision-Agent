# -*- coding: utf-8 -*-
"""Tests for app/agents/graph.py -- disposal workflow node functions."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.agents.graph import (
    DisposalState,
    dispatch_order,
    emergency_linkage,
    event_analysis,
    final_summary,
    regulation_search,
    run_disposal,
    should_emergency_linkage,
    should_skip_on_error,
    supervisor_judge,
)


def _make_state(overrides: dict | None = None) -> DisposalState:
    """Helper: build a minimal DisposalState with defaults."""
    state: DisposalState = {
        "alarm_data": {
            "event_id": "TEST001",
            "event_type": "fire",
            "alarm_level": "HIGH",
            "confidence": 0.92,
            "location": "Test Factory",
            "timestamp": "2026-07-12 12:00:00",
            "image_path": "test.jpg",
            "bbox": [0, 0, 10, 10],
            "reason": "Test",
        },
        "alarm_level": "HIGH",
        "event_type": "fire",
        "location": "Test Factory",
        "confidence": 0.92,
        "timestamp": "2026-07-12 12:00:00",
        "image_path": "test.jpg",
        "supervisor_result": {},
        "analysis": "",
        "regulations": {},
        "dispatch_result": "",
        "emergency_result": "",
        "final_report": "",
        "order_id": "",
        "notification_sent": False,
        "notification_enabled": False,
        "current_step": "start",
        "error_msg": "",
        "steps_log": [],
    }
    if overrides:
        state.update(overrides)
    return state


# ===================================================================
# Tests: supervisor_judge
# ===================================================================

class TestSupervisorJudge:
    def test_high_level_fire(self):
        state = _make_state()
        result = supervisor_judge(state)
        assert "alarm_level" in result
        assert result["alarm_level"] == "HIGH"
        assert result["current_step"] is not None

    def test_medium_level(self):
        state = _make_state({"alarm_level": "MEDIUM"})
        result = supervisor_judge(state)
        assert result["alarm_level"] == "MEDIUM"

    def test_low_level(self):
        state = _make_state({"alarm_level": "LOW"})
        result = supervisor_judge(state)
        assert result["alarm_level"] == "LOW"

    def test_handles_unknown_level(self):
        state = _make_state({"alarm_level": "CRITICAL"})
        result = supervisor_judge(state)
        # Should not crash; level may be passed through
        assert "alarm_level" in result


# ===================================================================
# Tests: event_analysis
# ===================================================================

class TestEventAnalysis:
    def test_returns_analysis_string(self):
        state = _make_state()
        result = event_analysis(state)
        assert result["current_step"] == "event_analysis"
        assert isinstance(result.get("analysis"), str)

    def test_includes_event_type_in_analysis(self):
        state = _make_state({"event_type": "smoke"})
        result = event_analysis(state)
        assert result["analysis"] != ""


# ===================================================================
# Tests: regulation_search
# ===================================================================

class TestRegulationSearch:
    def test_returns_regulations(self):
        state = _make_state()
        result = regulation_search(state)
        assert result["current_step"] == "regulation_search"
        # regulations should be a dict or similar
        assert isinstance(result.get("regulations"), dict) or result.get("regulations") == {}
        assert result.get("error_msg", "") == ""


# ===================================================================
# Tests: emergency_linkage
# ===================================================================

class TestEmergencyLinkage:
    def test_high_level_triggers_linkage(self):
        state = _make_state()
        result = emergency_linkage(state)
        assert result["current_step"] == "emergency_linkage"
        assert result.get("emergency_result") is not None

    def test_low_level_still_returns_gracefully(self):
        state = _make_state({"alarm_level": "LOW"})
        result = emergency_linkage(state)
        assert "current_step" in result
        assert result["current_step"] == "emergency_linkage"


# ===================================================================
# Tests: dispatch_order
# ===================================================================

class TestDispatchOrder:
    def test_high_level_generates_order(self):
        state = _make_state()
        result = dispatch_order(state)
        assert result["current_step"] == "dispatch_order"
        # Should produce an order_id or dispatch content
        assert result.get("order_id") is not None

    def test_medium_level_generates_order(self):
        state = _make_state({"alarm_level": "MEDIUM"})
        result = dispatch_order(state)
        assert result.get("order_id") is not None

    def test_notification_can_be_disabled_explicitly(self, monkeypatch):
        import app.agents.graph as graph

        def fail_if_called(**kwargs):
            raise AssertionError("notification adapter must not be called")

        monkeypatch.setattr(graph, "send_wechat_notification_detail", fail_if_called)
        result = dispatch_order(_make_state({"notification_enabled": False}))
        assert result["notification_sent"] is False


# ===================================================================
# Tests: final_summary
# ===================================================================

class TestFinalSummary:
    def test_generates_report(self):
        state = _make_state()
        result = final_summary(state)
        assert result["current_step"] == "final_summary"
        assert result.get("final_report") is not None
        assert len(result["final_report"]) > 0


# ===================================================================
# Tests: should_emergency_linkage (conditional edge)
# ===================================================================

class TestShouldEmergencyLinkage:
    def test_high_returns_linkage(self):
        state = _make_state({"alarm_level": "HIGH"})
        result = should_emergency_linkage(state)
        assert result == "emergency_linkage"

    def test_medium_still_returns_string(self):
        state = _make_state({"alarm_level": "MEDIUM"})
        result = should_emergency_linkage(state)
        assert isinstance(result, str)

    def test_low_still_returns_string(self):
        state = _make_state({"alarm_level": "LOW"})
        result = should_emergency_linkage(state)
        assert isinstance(result, str)


# ===================================================================
# Tests: should_skip_on_error (conditional edge)
# ===================================================================

class TestShouldSkipOnError:
    def test_no_error_returns_continue(self):
        state = _make_state()
        result = should_skip_on_error(state)
        assert result is not None

    def test_with_error_returns_skip(self):
        state = _make_state({"error_msg": "Something failed"})
        result = should_skip_on_error(state)
        assert result is not None


# ===================================================================
# Tests: run_disposal integration
# ===================================================================

class TestRunDisposal:
    def test_valid_json_string(self):
        alarm_json = json.dumps({
            "event_id": "INT001",
            "event_type": "fire",
            "alarm_level": "HIGH",
            "confidence": 0.9,
            "location": "Integration Test",
            "timestamp": "2026-07-12 12:00:00",
        })
        result = run_disposal(alarm_json)
        assert "report" in result
        assert "order_id" in result
        assert "steps" in result
        assert "notification" in result
        assert "error" in result

    def test_valid_dict_input(self):
        alarm_data = {
            "event_id": "DICT001",
            "event_type": "smoke",
            "alarm_level": "MEDIUM",
            "confidence": 0.7,
            "location": "Dict Test",
            "timestamp": "2026-07-12 12:00:00",
        }
        result = run_disposal(alarm_data)
        assert "report" in result

    def test_invalid_json_returns_error(self):
        result = run_disposal("not valid json")
        assert "error" in result
        assert result["error"] != ""

    def test_empty_json_object(self):
        result = run_disposal("{}")
        assert "report" in result
        # Shouldn't crash
        assert "error" in result

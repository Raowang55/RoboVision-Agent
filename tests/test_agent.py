# -*- coding: utf-8 -*-
"""Tests for app/agent.py -- run_agent, run_agent_with_react, and helpers.

These tests use the keyword-based intent fallback (not the LLM path)
so they can run without any external API dependencies.
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ===================================================================
# Tests: error boundary in run_agent
# ===================================================================

class TestRunAgentErrorBoundary:
    """Verify that run_agent never raises — it always returns a dict."""

    def test_returns_dict(self):
        from app.agent import run_agent
        result = run_agent(image=None, text_prompt="")
        assert isinstance(result, dict)

    def test_returns_dict_with_expected_keys(self):
        from app.agent import run_agent
        result = run_agent(image=None, text_prompt="")
        expected_keys = {"intent", "result", "error", "annotated_image", "intent_info"}
        assert expected_keys.issubset(result.keys())

    def test_no_image_for_detect_open_returns_error_message(self):
        """detect_open intent without image should return an error, not crash."""
        from app.agent import run_agent
        result = run_agent(image=None, text_prompt="detect_open objects")
        assert isinstance(result, dict)
        # The function should not raise an exception
        assert "error" in result

    def test_unknown_tool_returns_error(self):
        """An intent not in TOOL_REGISTRY should return a structured error."""
        from app.agent import run_agent
        # Use a prompt that will be parsed as an intent not in registry
        # 'xyzzy_unknown_tool_42' has no matching keywords, so it defaults to 'detect'
        result = run_agent(image=None, text_prompt="xyzzy_unknown_tool_42")
        assert isinstance(result, dict)
        assert "error" in result

    def test_event_log_intent_returns_result(self):
        """event_log intent should return a dict with log data (no crash)."""
        from app.agent import run_agent
        result = run_agent(image=None, text_prompt="event_log")
        assert result["error"] is None
        assert isinstance(result.get("result"), dict)

    def test_fire_log_intent_returns_result(self):
        """fire_log intent should return a dict (no crash)."""
        from app.agent import run_agent
        result = run_agent(image=None, text_prompt="fire alarm log")
        assert result["error"] is None
        assert isinstance(result.get("result"), dict)

    def test_explicit_open_task_routes_to_open_vocabulary_tool(self, monkeypatch):
        import app.agent as agent
        from app.contracts import tool_success

        def fake_open_tool(media, prompt, params):
            assert prompt == "forklift, helmet"
            assert params["confidence"] == 0.4
            return tool_success("detect_open", "Open vocabulary complete.", {"classes": ["forklift", "helmet"]}), None

        monkeypatch.setitem(agent.TOOL_REGISTRY, "detect_open", fake_open_tool)
        result = agent.run_agent(
            image=np.zeros((8, 8, 3), dtype=np.uint8),
            text_prompt="forklift, helmet",
            task="open",
            confidence=0.4,
            use_llm=False,
        )
        assert result["intent"] == "detect_open"
        assert result["ok"] is True


# ===================================================================
# Tests: error boundary in run_agent_with_react
# ===================================================================

class TestRunAgentWithReactErrorBoundary:
    """Verify that run_agent_with_react never raises."""

    def test_returns_dict(self):
        from app.agent import run_agent_with_react
        result = run_agent_with_react(text_prompt="test query")
        assert isinstance(result, dict)

    def test_returns_dict_with_expected_keys(self):
        from app.agent import run_agent_with_react
        result = run_agent_with_react(text_prompt="test query")
        expected_keys = {"intent", "result", "error", "annotated_image", "intent_info"}
        assert expected_keys.issubset(result.keys())


# ===================================================================
# Tests: _is_chain_query
# ===================================================================

class TestIsChainQuery:
    """Verify the chain detection logic."""

    def test_detect_and_then_rag(self):
        from app.agent import _is_chain_query
        assert _is_chain_query("detect objects and then query safety regulations")

    def test_detect_then_safety(self):
        from app.agent import _is_chain_query
        assert _is_chain_query("detect fire and safety guidelines")

    def test_single_intent_not_chain(self):
        from app.agent import _is_chain_query
        assert not _is_chain_query("detect all objects")
        assert not _is_chain_query("what is the safety regulation")

    def test_empty_text_not_chain(self):
        from app.agent import _is_chain_query
        assert not _is_chain_query("")
        assert not _is_chain_query("   ")


# ===================================================================
# Tests: _build_summary_lines
# ===================================================================

class TestBuildSummaryLines:
    """Verify the summary line builder."""

    def test_returns_list_of_strings(self):
        from app.agent import _build_summary_lines
        lines = _build_summary_lines("detect", {"tool": "yolo"})
        assert isinstance(lines, list)
        assert all(isinstance(line, str) for line in lines)

    def test_includes_tool_name(self):
        from app.agent import _build_summary_lines
        lines = _build_summary_lines("detect", {"tool": "yolo_detect"})
        assert any("yolo_detect" in line for line in lines)

    def test_detect_open_includes_prompt(self):
        from app.agent import _build_summary_lines
        lines = _build_summary_lines("detect_open", {
            "tool": "grounding",
            "prompt": "find all chairs",
            "phrases": ["chair"],
        })
        joined = " ".join(lines)
        assert "find all chairs" in joined
        assert "chair" in joined

    def test_segment_shows_count(self):
        from app.agent import _build_summary_lines
        lines = _build_summary_lines("segment", {
            "tool": "sam",
            "num_masks": 5,
        })
        joined = " ".join(lines)
        assert "5" in joined

    def test_empty_result_does_not_crash(self):
        from app.agent import _build_summary_lines
        lines = _build_summary_lines("detect", {})
        assert isinstance(lines, list)

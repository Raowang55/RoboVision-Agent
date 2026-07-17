"""Stable data contracts shared by the orchestrator and UI."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

import numpy as np


class AgentStep(TypedDict, total=False):
    """One observable tool execution step without model chain-of-thought."""

    tool: str
    status: Literal["ok", "error"]
    duration_ms: float
    summary: str


class ToolResult(TypedDict):
    """Normalized result returned by every registered tool."""

    ok: bool
    tool: str
    summary: str
    data: dict[str, Any]
    artifacts: dict[str, Any]
    error: str | None


class AgentResponse(TypedDict):
    """Public response returned by :func:`app.agent.run_agent`."""

    ok: bool
    intent: str
    result: dict[str, Any]
    error: str | None
    artifacts: dict[str, Any]
    trace: list[AgentStep]
    planner_source: Literal["explicit", "rule", "llm"]
    intent_info: dict[str, Any]
    annotated_image: np.ndarray | None


def tool_success(
    tool: str,
    summary: str,
    data: dict[str, Any] | None = None,
    artifacts: dict[str, Any] | None = None,
) -> ToolResult:
    return {
        "ok": True,
        "tool": tool,
        "summary": summary,
        "data": data or {},
        "artifacts": artifacts or {},
        "error": None,
    }


def tool_error(tool: str, error: str) -> ToolResult:
    return {
        "ok": False,
        "tool": tool,
        "summary": error,
        "data": {},
        "artifacts": {},
        "error": error,
    }

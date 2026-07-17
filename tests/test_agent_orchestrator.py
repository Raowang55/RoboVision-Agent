"""Tests for deterministic planning and normalized tool traces."""

from __future__ import annotations

from app.contracts import tool_success


def test_explicit_visual_task_uses_one_registered_tool(monkeypatch):
    import app.agent as agent

    def fake_detect(media, prompt, params):
        assert params["task"] == "ppe"
        return tool_success("detect", "done", {"detections": []}), None

    monkeypatch.setitem(agent.TOOL_REGISTRY, "detect", fake_detect)
    response = agent.run_agent("input.jpg", "", task="ppe", use_llm=False)
    assert response["ok"] is True
    assert response["planner_source"] == "explicit"
    assert response["trace"][0]["tool"] == "detect"
    assert set(response) >= {
        "ok",
        "intent",
        "result",
        "error",
        "artifacts",
        "trace",
        "planner_source",
    }


def test_offline_rule_planner_does_not_call_llm(monkeypatch):
    import app.agent as agent
    import app.llm.llm_client as llm_client

    monkeypatch.setattr(llm_client, "chat", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setitem(
        agent.TOOL_REGISTRY,
        "event_log",
        lambda media, prompt, params: (tool_success("event_log", "ok", {}), None),
    )
    response = agent.run_agent(None, "show event log", use_llm=False)
    assert response["ok"] is True
    assert response["planner_source"] == "rule"


def test_fixed_detect_to_rag_chain(monkeypatch):
    import app.agent as agent

    def fake_chain_detect(media, prompt, params):
        assert params["task"] == "ppe"
        return tool_success("detect", "one person", {"detections": [{"class_name": "person"}]}), None

    monkeypatch.setitem(
        agent.TOOL_REGISTRY,
        "detect",
        fake_chain_detect,
    )
    monkeypatch.setitem(
        agent.TOOL_REGISTRY,
        "rag",
        lambda media, prompt, params: (
            tool_success("rag", "wear PPE", {"answer": "wear PPE", "source_files": ["ppe_rules.md"]}),
            None,
        ),
    )
    response = agent.run_agent(
        "input.jpg",
        "detect objects and then query safety regulations",
        task="ppe",
        use_llm=False,
    )
    assert response["intent"] == "chain"
    assert [step["tool"] for step in response["trace"]] == ["detect", "rag"]
    assert response["result"]["rag"]["source_files"] == ["ppe_rules.md"]


def test_llm_planner_accepts_valid_structured_response(monkeypatch):
    import app.llm.llm_client as llm_client
    from app.agent import parse_intent_with_llm

    monkeypatch.setattr(
        llm_client,
        "chat",
        lambda *args, **kwargs: {
            "success": True,
            "content": '{"intent":"rag","confidence":0.9,"params":{"top_k":3}}',
            "model": "fake",
            "error": None,
        },
    )
    result = parse_intent_with_llm("ambiguous", use_llm=True)
    assert result["intent"] == "rag"
    assert result["source"] == "llm"

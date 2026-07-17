"""Regression tests for the résumé-facing Agent evaluations and demo."""

from __future__ import annotations


def test_offline_routing_evaluation_has_twenty_passing_cases():
    from scripts.evaluate_agent import evaluate_cases

    result = evaluate_cases()
    assert result["total"] == 20
    assert result["route_accuracy"] == 1.0
    assert result["tool_sequence_pass_rate"] == 1.0


def test_demo_smoke_report_contract(tmp_path, monkeypatch):
    import scripts.demo_smoke as demo

    image = tmp_path / "input.jpg"
    image.write_bytes(b"not-decoded-by-the-fake-agent")
    monkeypatch.setattr(
        demo,
        "run_agent",
        lambda **kwargs: {
            "ok": True,
            "intent": "chain",
            "planner_source": "rule",
            "trace": [
                {"tool": "detect", "status": "ok", "duration_ms": 12.3, "summary": "done"},
                {"tool": "rag", "status": "ok", "duration_ms": 4.5, "summary": "cited"},
            ],
            "result": {
                "detection": {"detections": [{"class_name": "person"}]},
                "rag": {"source_files": ["ppe_rules.md"], "used_llm": False},
            },
            "error": None,
        },
    )
    monkeypatch.setattr(
        demo,
        "run_disposal",
        lambda alarm, send_notification=False: {
            "order_id": "WO-DEMO",
            "notification": False,
            "error": "",
        },
    )
    monkeypatch.setattr(demo, "get_work_order", lambda order_id: {"order_id": order_id, "status": "completed"})
    monkeypatch.setattr(
        demo,
        "list_disposal_steps",
        lambda event_id: [{"step_name": str(index)} for index in range(5)],
    )
    monkeypatch.setattr(demo, "collect_status", lambda: {"models": {"yolo_world": True}})

    report = demo.run_demo(image)

    assert report["ok"] is True
    assert report["agent"]["intent"] == "chain"
    assert report["agent"]["rag_sources"] == ["ppe_rules.md"]
    assert report["work_order"]["status"] == "completed"
    assert report["notification_sent"] is False

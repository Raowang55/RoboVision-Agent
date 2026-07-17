"""SQLite work-order repository regression tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.fixture
def isolated_db(tmp_path):
    from app.agents import db

    original = db._db_path
    db.configure_db(tmp_path / "disposal.db")
    yield db
    db.configure_db(original)


def test_work_order_lifecycle(isolated_db):
    row_id = isolated_db.insert_work_order(
        order_id="WO-001",
        event_id="EV-001",
        event_type="fire",
        alarm_level="HIGH",
        location="warehouse",
        dispatch="Evacuate and inspect",
        status="dispatched",
    )
    assert row_id > 0
    assert isolated_db.update_work_order("WO-001", "resolved")
    order = isolated_db.get_work_order("WO-001")
    assert order["status"] == "completed"
    assert order["final_report"] == "resolved"


def test_duplicate_order_is_idempotent(isolated_db):
    values = {
        "order_id": "WO-DUP",
        "event_id": "EV-DUP",
        "event_type": "smoke",
        "alarm_level": "MEDIUM",
        "location": "zone-a",
    }
    isolated_db.insert_work_order(**values)
    isolated_db.insert_work_order(**values)
    assert isolated_db.get_work_order("WO-DUP")["event_id"] == "EV-DUP"


def test_concurrent_step_writes(isolated_db):
    def write_step(index):
        isolated_db.insert_disposal_step("EV-CONCURRENT", f"step-{index}", "ok", "2026-01-01")

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write_step, range(12)))
    assert len(isolated_db.list_disposal_steps("EV-CONCURRENT")) == 12


def test_disposal_pipeline_completes_order(isolated_db):
    from app.agents.graph import run_disposal

    result = run_disposal(
        {
            "event_id": "EV-FLOW",
            "event_type": "fire",
            "alarm_level": "HIGH",
            "location": "warehouse",
            "timestamp": "2026-01-01 10:00:00",
            "confidence": 0.92,
        }
    )
    assert result["error"] == ""
    order = isolated_db.get_work_order(result["order_id"])
    assert order["status"] == "completed"
    assert order["final_report"]

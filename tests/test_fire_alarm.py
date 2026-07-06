"""Tests for FireAlarmEngine rule logic."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.runtime.fire_alarm_rules import FireAlarmEngine


def _det(name, conf=0.6):
    return {"class_name": name, "confidence": conf, "bbox": [0, 0, 10, 10]}


def test_no_alarm_on_single_frame():
    engine = FireAlarmEngine(cooldown_seconds=0)
    assert engine.update([_det("fire")]) is None


def test_high_alarm_after_3_fire_frames():
    engine = FireAlarmEngine(cooldown_seconds=0)
    for _ in range(2):
        assert engine.update([_det("fire")]) is None
    result = engine.update([_det("fire")])
    assert result is not None
    assert result["alarm_level"] == "HIGH"


def test_medium_alarm_after_10_smoke_frames():
    engine = FireAlarmEngine(cooldown_seconds=0)
    for _ in range(9):
        assert engine.update([_det("smoke", conf=0.5)]) is None
    result = engine.update([_det("smoke", conf=0.5)])
    assert result is not None
    assert result["alarm_level"] == "MEDIUM"


def test_cooldown_suppresses_repeat():
    engine = FireAlarmEngine(cooldown_seconds=60)
    for _ in range(3):
        engine.update([_det("fire")])
    assert engine.update([_det("fire")]) is None


def test_reset_clears_counters():
    engine = FireAlarmEngine(cooldown_seconds=0)
    for _ in range(2):
        engine.update([_det("fire")])
    engine.reset()
    assert engine.update([_det("fire")]) is None

# -*- coding: utf-8 -*-
"""Tests for keyword-based intent parser."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.agent import parse_intent


def test_fire_keywords():
    assert parse_intent("fire detected in warehouse") == "fire_log"
    assert parse_intent("smoke alarm triggered") == "fire_log"


def test_rag_keywords():
    result = parse_intent("what safety regulation applies here")
    assert result in ("rag", "detect")


def test_detect_keywords():
    assert parse_intent("detect all objects in image") == "detect"
    assert parse_intent("yolo inference on this photo") == "detect"


def test_event_log_keywords():
    assert parse_intent("show me the event log") == "event_log"
    assert parse_intent("query the alarm log history") == "event_log"


def test_chain_keywords():
    assert parse_intent("detect objects and then query safety regulations") == "chain"


def test_empty_input():
    """Empty or whitespace-only input should not crash."""
    result = parse_intent("")
    assert isinstance(result, str)


def test_no_keywords_defaults_to_detect():
    """A command with no special keywords should default to detect."""
    result = parse_intent("process this image")
    assert result == "detect"


def test_chinese_fire_log():
    """Chinese fire/smoke keywords should map to fire_log."""
    assert parse_intent("火灾检测") == "fire_log"
    assert parse_intent("烟雾报警") == "fire_log"
    assert parse_intent("火警") == "fire_log"


def test_chinese_event_log():
    """Chinese log keywords should map to event_log."""
    assert parse_intent("查看日志") == "event_log"
    assert parse_intent("报警记录查询") == "event_log"
    assert parse_intent("查询事件") == "event_log"


def test_chinese_rag():
    """Chinese question words should trigger RAG."""
    result = parse_intent("有什么安全规定")
    assert result == "rag"
# -*- coding: utf-8 -*-
"""Integration tests for the unified detection pipeline."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _find_test_image():
    for d in [Path("data/alarms/fire"), Path("data/images"), Path("data/outputs")]:
        if d.exists():
            for ext in (".jpg", ".jpeg", ".png"):
                for f in d.glob("*" + ext):
                    return str(f.resolve())
    return None


def _model_available():
    from app.config import YOLO_WORLD_MODEL, YOLO_WORLD_SMALL
    return YOLO_WORLD_MODEL.exists() or YOLO_WORLD_SMALL.exists()


TEST_IMAGE = _find_test_image()
HAS_MODEL = _model_available()
NEEDS_MODEL = pytest.mark.skipif(not HAS_MODEL, reason="No model weights")
NEEDS_IMAGE = pytest.mark.skipif(TEST_IMAGE is None, reason="No test image")


@NEEDS_MODEL
@NEEDS_IMAGE
@pytest.mark.model
class TestUnifiedPipeline:

    def test_detect_image_returns_dict(self):
        from app.runtime.unified_pipeline import _detect_image
        r = _detect_image(TEST_IMAGE, conf=0.5, task="general")
        assert isinstance(r, dict)
        assert "detections" in r
        assert "output_image" in r

    def test_fire_detection_no_crash(self):
        from app.runtime.unified_pipeline import _detect_image
        r = _detect_image(TEST_IMAGE, conf=0.5, task="fire")
        assert isinstance(r, dict)

    def test_ppe_detection_no_crash(self):
        from app.runtime.unified_pipeline import _detect_image
        r = _detect_image(TEST_IMAGE, conf=0.5, task="ppe")
        assert isinstance(r, dict)

    def test_media_type_utils(self):
        from app.utils.media_utils import detect_media_type
        assert detect_media_type(input_path="test.jpg") == "image"
        assert detect_media_type(input_path="test.mp4") == "video"
        assert detect_media_type(source="0") == "camera"

    def test_task_type_utils(self):
        from app.utils.media_utils import detect_task_type
        assert detect_task_type(instruction="detect fire") == "fire"
        assert detect_task_type(instruction="check vest") == "ppe"
        assert detect_task_type(instruction="find all") == "general"

    def test_run_unified_image(self):
        from app.runtime.unified_pipeline import run_unified_detection

        class MockFile:
            def __init__(self, p): self.name = p

        r = run_unified_detection(
            file_obj=MockFile(TEST_IMAGE),
            task_dropdown="General Object Detection",
            conf=0.5,
        )
        assert isinstance(r, tuple)
        summary = r[0]
        json_str = r[4]
        assert isinstance(summary, str) and len(summary) > 0
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        assert isinstance(data, (list, dict))

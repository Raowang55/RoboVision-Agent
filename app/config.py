"""Centralized configuration for RoboVision-Agent.

All model paths, environment-dependent settings, and deployment
configuration live here.  No file should hardcode paths like
``D:/yolo26`` — import from this module instead.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Model directory — weights/ at project root
# ---------------------------------------------------------------------------

MODEL_DIR = _PROJECT_ROOT / "weights"

# ---------------------------------------------------------------------------
# YOLO-World models (YOLOv8-based open-vocabulary detection)
# ---------------------------------------------------------------------------

YOLO_WORLD_MODEL = MODEL_DIR / "yolov8m-worldv2.pt"
YOLO_WORLD_SMALL = MODEL_DIR / "yolov8s-worldv2.pt"

# Default model used by the pipeline (medium variant)
DEFAULT_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", str(YOLO_WORLD_MODEL))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_DIR = _PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DB_PATH = str(_PROJECT_ROOT / "data" / "work_order.db")

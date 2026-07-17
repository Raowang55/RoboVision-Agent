# -*- coding: utf-8 -*-
"""Lightweight media-type detection helpers.

Used by main.py and unified_pipeline.py to decide whether an input
is an image, video, or camera source — without running actual detection.
"""

from __future__ import annotations

from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"}

FIRE_KEYWORDS = ["fire", "smoke", "火灾", "火焰", "烟雾", "火", "烟"]
PPE_KEYWORDS = ["安全帽", "反光衣", "ppe", "helmet", "vest", "违规", "头盔", "工服"]


def detect_media_type(
    input_path: str | None = None,
    source: str | None = None,
) -> str:
    """Determine whether an input is an image, video, or camera.

    Returns one of: "image", "video", "camera"
    """
    if input_path:
        ext = Path(input_path).suffix.lower()
        if ext in IMAGE_EXTS:
            return "image"
        if ext in VIDEO_EXTS:
            return "video"
        return "image"

    if source:
        s = source.strip()
        if s.isdigit():
            return "camera"
        if s.startswith("rtsp://") or s.startswith("rtmp://"):
            return "camera"
        ext = Path(s).suffix.lower()
        if ext in VIDEO_EXTS:
            return "video"
        return "video"

    return "image"


def detect_task_type(
    instruction: str = "",
    task_type: str = "auto",
) -> str:
    """Determine which detection task to run.

    Returns one of: "general", "fire", "ppe"
    """
    if task_type and task_type != "auto":
        return task_type
    text = instruction.lower()
    if any(w in text for w in FIRE_KEYWORDS):
        return "fire"
    if any(w in text for w in PPE_KEYWORDS):
        return "ppe"
    return "general"


def resolve_model_path(task_type: str) -> Path:
    """Return the best model path for a given task.

    Prefers task-specific models (fire_smoke / PPE) over YOLO-World fallbacks.

    Args:
        task_type: One of "general", "fire", "ppe".

    Returns:
        Absolute Path to the model file.
    """
    from app.config import (
        FIRE_SMOKE_MODEL,
        PPE_MODEL,
        YOLO_WORLD_MODEL,
        YOLO_WORLD_SMALL,
    )

    if task_type == "fire":
        candidates = [FIRE_SMOKE_MODEL, YOLO_WORLD_SMALL]
    elif task_type == "ppe":
        candidates = [PPE_MODEL, YOLO_WORLD_SMALL]
    else:
        candidates = [YOLO_WORLD_MODEL]

    for c in candidates:
        if c.exists():
            return c

    fallback = YOLO_WORLD_SMALL
    if fallback.exists():
        return fallback
    return candidates[0] if candidates else YOLO_WORLD_SMALL

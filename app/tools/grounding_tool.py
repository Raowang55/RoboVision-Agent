"""Real YOLO-World open-vocabulary detection tool."""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from app.config import GROUNDING_BOX_THRESHOLD


def _parse_classes(text_prompt: str, classes: list[str] | None = None) -> list[str]:
    if classes:
        return [str(item).strip() for item in classes if str(item).strip()]
    cleaned = re.sub(
        r"^(detect|find|identify|检测|查找|识别)\s*",
        "",
        (text_prompt or "").strip(),
        flags=re.IGNORECASE,
    )
    parsed = [item.strip() for item in re.split(r"[,，、;；\n]+", cleaned) if item.strip()]
    return parsed or ["person"]


def detect_open(
    image: np.ndarray,
    text_prompt: str,
    box_threshold: float = GROUNDING_BOX_THRESHOLD,
    text_threshold: float = 0.25,
    classes: list[str] | None = None,
    **kwargs: Any,
) -> dict:
    """Detect user-supplied classes using the configured YOLO-World model."""
    del text_threshold, kwargs
    if image is None or not isinstance(image, np.ndarray):
        raise ValueError("detect_open requires a numpy image")

    from app.runtime.unified_pipeline import _get_world_model

    class_names = _parse_classes(text_prompt, classes)
    model, _ = _get_world_model()
    model.set_classes(class_names)
    result = model.predict(source=image, conf=float(box_threshold), verbose=False)[0]
    height, width = image.shape[:2]
    boxes: list[list[float]] = []
    phrases: list[str] = []
    scores: list[float] = []
    if result.boxes is not None:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            class_id = int(box.cls[0].item())
            boxes.append(
                [
                    round(x1 / width, 4),
                    round(y1 / height, 4),
                    round(x2 / width, 4),
                    round(y2 / height, 4),
                ]
            )
            phrases.append(str(result.names[class_id]))
            scores.append(round(float(box.conf[0].item()), 4))

    return {
        "tool": "yolo_world_open_vocabulary",
        "phrases": phrases,
        "boxes": boxes,
        "scores": scores,
        "prompt": text_prompt,
        "classes": class_names,
        "message": f"Detected {len(boxes)} open-vocabulary object(s).",
    }

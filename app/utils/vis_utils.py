# -*- coding: utf-8 -*-
"""Visualization utilities for drawing boxes and labels."""

import cv2
import numpy as np

from app.config import VIS_FONT_SCALE

# A fixed palette of distinct colours for drawing
COLORS = [
    (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (128, 255, 0), (255, 128, 0),
    (0, 128, 255), (128, 0, 255), (255, 128, 128), (128, 255, 128),
]


def _get_color(idx: int) -> tuple:
    return COLORS[idx % len(COLORS)]


def draw_boxes(
    image: np.ndarray,
    boxes: list[list[float]],
    labels: list[str] | None = None,
    scores: list[float] | None = None,
    normalized: bool = True,
) -> np.ndarray:
    """Draw bounding boxes on a copy of the image.

    Args:
        image: BGR image as numpy array.
        boxes: List of [x1, y1, x2, y2] boxes.
        labels: Optional list of label strings.
        scores: Optional list of confidence scores.
        normalized: If True, boxes are in [0,1]; convert to pixel coords.

    Returns:
        Annotated BGR image (new array, original is unchanged).
    """
    vis = image.copy()
    h, w = vis.shape[:2]

    for i, box in enumerate(boxes):
        color = _get_color(i)
        x1, y1, x2, y2 = box
        if normalized:
            x1, y1 = int(x1 * w), int(y1 * h)
            x2, y2 = int(x2 * w), int(y2 * h)
        else:
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)

        text_parts = []
        if labels and i < len(labels):
            text_parts.append(labels[i])
        if scores and i < len(scores):
            text_parts.append(f"{scores[i]:.2f}")
        if text_parts:
            label_text = " ".join(text_parts)
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(vis, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
            cv2.putText(vis, label_text, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return vis


def draw_labels(
    image: np.ndarray,
    text_lines: list[str],
    position: tuple[int, int] = (10, 30),
    font_scale: float = VIS_FONT_SCALE,
    color: tuple = (255, 255, 255),
    bg_color: tuple = (0, 0, 0),
) -> np.ndarray:
    """Overlay multi-line text on an image with a dark background strip."""
    vis = image.copy()
    x, y = position
    line_height = int(24 * font_scale)

    for i, line in enumerate(text_lines):
        ty = y + i * line_height
        (tw, th), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
        cv2.rectangle(vis, (x - 4, ty - th - 6), (x + tw + 4, ty + 4), bg_color, -1)
        cv2.putText(vis, line, (x, ty),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

    return vis

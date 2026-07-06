"""Visualization utilities for drawing boxes, masks, and labels."""

import random
from typing import List, Optional, Tuple

import cv2
import numpy as np

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
    boxes: List[List[float]],
    labels: Optional[List[str]] = None,
    scores: Optional[List[float]] = None,
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


def draw_masks(
    image: np.ndarray,
    masks: List[dict],
    alpha: float = 0.4,
) -> np.ndarray:
    """Draw semi-transparent mask overlays on a copy of the image.

    Since this is a mock utility, it draws semi-transparent coloured
    rectangles for each mask's bbox as a visual placeholder.

    Args:
        image: BGR image.
        masks: List of mask dicts (each with a 'bbox' key [x1, y1, x2, y2] in pixels).
        alpha: Blend factor (0 = fully transparent, 1 = fully opaque).

    Returns:
        Annotated BGR image.
    """
    vis = image.copy()

    for i, m in enumerate(masks):
        overlay = vis.copy()
        color = _get_color(i)
        x1, y1, x2, y2 = m.get("bbox", [0, 0, 100, 100])
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, alpha, vis, 1 - alpha, 0, vis)

        # Draw mask id label
        cv2.putText(vis, f"mask #{m.get('id', i + 1)} ({m.get('score', 0):.2f})",
                    (x1 + 4, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return vis


def draw_labels(
    image: np.ndarray,
    text_lines: List[str],
    position: Tuple[int, int] = (10, 30),
    font_scale: float = 0.7,
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

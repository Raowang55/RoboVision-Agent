"""Grounding DINO open-vocabulary detection tool (mock implementation)."""

import time
import random
from typing import Any

import numpy as np


def detect_open(
    image: np.ndarray,
    text_prompt: str,
    box_threshold: float = 0.35,
    text_threshold: float = 0.25,
    **kwargs: Any,
) -> dict:
    """Mock open-vocabulary detection. Accepts a free-form text prompt.

    Args:
        image: Input image as a numpy array (H, W, C).
        text_prompt: Natural-language description of objects to find.
        box_threshold: Confidence threshold for bounding boxes.
        text_threshold: Confidence threshold for text-to-region matching.

    Returns:
        dict with keys:
            - phrases: list of matched text phrases.
            - boxes: list of [x1, y1, x2, y2] bounding boxes (0-1).
            - scores: list of confidence scores.
            - prompt: the original text prompt.
    """
    time.sleep(random.uniform(0.5, 1.2))

    # Parse prompt into loose keywords
    keywords = [w.strip().rstrip("s") for w in text_prompt.replace(",", " ").split() if len(w) > 2]
    if not keywords:
        keywords = ["object"]

    h, w = image.shape[:2]
    num = random.randint(1, min(3, len(keywords)))
    picked = random.sample(keywords, k=num)

    boxes, phrases, scores = [], [], []
    for phrase in picked:
        cx, cy = random.uniform(0.2, 0.8), random.uniform(0.2, 0.8)
        bw, bh = random.uniform(0.08, 0.25), random.uniform(0.08, 0.25)
        x1, y1 = max(0, cx - bw / 2), max(0, cy - bh / 2)
        x2, y2 = min(1, cx + bw / 2), min(1, cy + bh / 2)
        boxes.append([round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)])
        phrases.append(phrase)
        scores.append(round(random.uniform(0.65, 0.95), 2))

    return {
        "tool": "grounding_detect",
        "phrases": phrases,
        "boxes": boxes,
        "scores": scores,
        "prompt": text_prompt,
    }

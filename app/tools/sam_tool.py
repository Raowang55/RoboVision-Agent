"""SAM segmentation tool (mock implementation)."""

import time
import random
from typing import Any

import numpy as np


def segment(
    image: np.ndarray,
    boxes: list | None = None,
    points: list | None = None,
    **kwargs: Any,
) -> dict:
    """Mock SAM segmentation. Generates placeholder masks.

    Args:
        image: Input image as a numpy array (H, W, C).
        boxes: Optional list of bounding boxes [[x1, y1, x2, y2], ...] in pixel coords.
        points: Optional list of point prompts [[x, y], ...] in pixel coords.

    Returns:
        dict with keys:
            - masks: list of mask dicts, each with 'segmentation' (RLE-like string) and 'area'.
            - num_masks: int.
    """
    time.sleep(random.uniform(0.4, 1.0))

    h, w = image.shape[:2]

    if boxes:
        num_masks = len(boxes)
    elif points:
        num_masks = len(points)
    else:
        num_masks = random.randint(1, 3)

    masks = []
    for i in range(num_masks):
        area_pct = random.uniform(0.05, 0.4)
        masks.append({
            "id": i + 1,
            "segmentation": f"<MOCK_RLE_{random.randint(1000, 9999)}>",
            "area": int(h * w * area_pct),
            "bbox": [
                random.randint(0, w // 3),
                random.randint(0, h // 3),
                random.randint(2 * w // 3, w),
                random.randint(2 * h // 3, h),
            ],
            "score": round(random.uniform(0.88, 0.99), 2),
        })

    return {
        "tool": "sam_segment",
        "masks": masks,
        "num_masks": len(masks),
    }

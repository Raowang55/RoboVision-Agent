"""Image loading / resizing / saving utilities."""

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image


def load_image(path_or_array: str | np.ndarray | Image.Image) -> np.ndarray:
    """Load an image from a file path, numpy array, or PIL Image.

    Always returns a numpy array in BGR format (OpenCV convention).
    """
    if isinstance(path_or_array, np.ndarray):
        return path_or_array
    if isinstance(path_or_array, Image.Image):
        return cv2.cvtColor(np.array(path_or_array), cv2.COLOR_RGB2BGR)
    path = Path(path_or_array)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    return cv2.imread(str(path))


def resize_image(
    image: np.ndarray,
    max_size: Tuple[int, int] = (1024, 1024),
) -> np.ndarray:
    """Resize an image so the larger side fits within max_size, preserving aspect ratio."""
    h, w = image.shape[:2]
    max_w, max_h = max_size
    scale = min(max_w / w, max_h / h, 1.0)
    if scale >= 1.0:
        return image
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def save_image(image: np.ndarray, path: str | Path) -> str:
    """Save a numpy image to disk. Returns the saved path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)
    return str(path)

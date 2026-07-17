# -*- coding: utf-8 -*-
"""File-system utility helpers."""

import time
from pathlib import Path

from app.config import OUTPUT_DIR


def ensure_dir(path: str | Path) -> Path:
    """Create directory if it doesn't exist; return the Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_images(directory: str | Path, extensions: tuple = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")) -> list[Path]:
    """Return a sorted list of image file paths in a directory (non-recursive)."""
    d = Path(directory)
    if not d.exists():
        return []
    files = [f for f in d.iterdir() if f.suffix.lower() in extensions]
    return sorted(files)


def get_output_path(prefix: str = "output", ext: str = ".png", directory: str = str(OUTPUT_DIR)) -> Path:
    """Generate a timestamped output file path."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    return Path(directory) / f"{prefix}_{ts}{ext}"

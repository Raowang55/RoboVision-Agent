"""File-system utility helpers."""

import time
from pathlib import Path
from typing import List


def ensure_dir(path: str | Path) -> Path:
    """Create directory if it doesn't exist; return the Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_images(directory: str | Path, extensions: tuple = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")) -> List[Path]:
    """Return a sorted list of image file paths in a directory (non-recursive)."""
    d = Path(directory)
    if not d.exists():
        return []
    files = [f for f in d.iterdir() if f.suffix.lower() in extensions]
    return sorted(files)


def get_output_path(prefix: str = "output", ext: str = ".png", directory: str = "data/outputs") -> Path:
    """Generate a timestamped output file path."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    return Path(directory) / f"{prefix}_{ts}{ext}"

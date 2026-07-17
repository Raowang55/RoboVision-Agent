# -*- coding: utf-8 -*-
"""Tests for utility helpers (file_utils, logging_config)."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.utils.file_utils import ensure_dir, get_output_path, list_images


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


class TestEnsureDir:
    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "a" / "b" / "c"
            result = ensure_dir(target)
            assert result == target
            assert target.is_dir()

    def test_returns_path_for_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "existing"
            target.mkdir()
            result = ensure_dir(target)
            assert result == target


class TestListImages:
    def test_returns_image_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            _touch(Path(tmp) / "a.jpg")
            _touch(Path(tmp) / "b.png")
            _touch(Path(tmp) / "c.txt")
            _touch(Path(tmp) / "d.jpeg")
            images = list_images(tmp)
            assert len(images) == 3
            names = [p.name for p in images]
            assert "a.jpg" in names
            assert "b.png" in names
            assert "c.txt" not in names

    def test_returns_empty_for_missing_dir(self):
        result = list_images("/nonexistent/path/xyz123")
        assert result == []

    def test_sorts_alphabetically(self):
        with tempfile.TemporaryDirectory() as tmp:
            _touch(Path(tmp) / "z.jpg")
            _touch(Path(tmp) / "a.jpg")
            images = list_images(tmp)
            assert images[0].name == "a.jpg"
            assert images[1].name == "z.jpg"


class TestGetOutputPath:
    def test_returns_pathlib_path(self):
        result = get_output_path()
        assert isinstance(result, Path)

    def test_uses_custom_directory(self):
        result = get_output_path(directory="/tmp/my_outputs")
        assert "my_outputs" in str(result).replace("\\", "/")

    def test_timestamp_format(self):
        result = get_output_path()
        assert result.suffix == ".png"
        name = result.stem
        # format: output_YYYYMMDD_HHMMSS
        parts = name.split("_")
        assert len(parts) >= 2
        assert len(parts[-2]) == 8  # YYYYMMDD
        assert len(parts[-1]) == 6  # HHMMSS

    def test_custom_prefix_and_ext(self):
        result = get_output_path(prefix="test", ext=".json")
        assert result.suffix == ".json"
        assert "test_" in result.stem

# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class TestParseTask:
    def test_dropdown_general(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, '', '通用物品检测') == 'general'
    def test_dropdown_fire(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, '', '火灾烟雾预警') == 'fire'
    def test_dropdown_ppe(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, '', '安全帽反光衣工检') == 'ppe'
    def test_auto_fire_en(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, 'detect fire', '自动判断') == 'fire'
    def test_auto_fire_zh(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, '检测火灾', '自动判断') == 'fire'
    def test_auto_smoke(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, 'smoke alarm', '自动判断') == 'fire'
    def test_auto_ppe_en(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, 'helmet check', '自动判断') == 'ppe'
    def test_auto_ppe_zh(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, '安全帽检测', '自动判断') == 'ppe'
    def test_default_general(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, 'find objects', '自动判断') == 'general'
    def test_unknown_dropdown(self):
        from app.runtime.unified_pipeline import _parse_task
        assert _parse_task(None, 'x', 'Nope') == 'general'

class TestDetectVideoErrors:
    def test_bad_source(self):
        from app.runtime.unified_pipeline import _detect_video
        r = _detect_video(source='no_such_file.mp4', conf=0.5, frame_stride=5, max_frames=5, task='general')
        assert isinstance(r, dict)
        assert 'Error' in r['summary_md']
    def test_bad_source_keys(self):
        from app.runtime.unified_pipeline import _detect_video
        r = _detect_video(source='no_such_file.mp4', conf=0.5, frame_stride=5, max_frames=5, task='general')
        for k in ('summary_md','video_path','log_path','detections_json','alarm_images'):
            assert k in r


class TestBrowserVideoFormatting:
    def test_missing_ffmpeg_runtime_returns_actionable_warning(self, monkeypatch, tmp_path):
        import app.runtime.unified_pipeline as pipeline

        source = tmp_path / "input.mp4"
        source.write_bytes(b"mp4v")
        monkeypatch.setitem(sys.modules, "imageio_ffmpeg", None)
        result, warning = pipeline._make_browser_playable_video(str(source))
        assert result == str(source)
        assert warning is not None
        assert "imageio-ffmpeg" in warning

    def test_ffmpeg_result_replaces_original_with_h264_file(self, monkeypatch, tmp_path):
        import app.runtime.unified_pipeline as pipeline

        source = tmp_path / "input.mp4"
        source.write_bytes(b"mp4v")

        class FakeImageioFfmpeg:
            @staticmethod
            def get_ffmpeg_exe():
                return "fake-ffmpeg"

        def fake_run(command, **kwargs):
            Path(command[-1]).write_bytes(b"h264")
            return SimpleNamespace(returncode=0, stderr="")

        monkeypatch.setitem(sys.modules, "imageio_ffmpeg", FakeImageioFfmpeg())
        monkeypatch.setattr(pipeline.subprocess, "run", fake_run)
        result, warning = pipeline._make_browser_playable_video(str(source))
        assert result == str(source)
        assert warning is None
        assert source.read_bytes() == b"h264"

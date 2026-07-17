"""Offline checks for the documented model downloader."""

from __future__ import annotations


def test_download_manifest_has_reproducible_sources_and_hashes():
    from scripts.download_models import MODELS

    assert set(MODELS) == {"yolov8s-worldv2.pt", "fire_smoke_yolov8n.pt"}
    for model in MODELS.values():
        assert model["url"].startswith("https://")
        assert len(model["sha256"]) == 64


def test_known_local_fire_weight_hash_matches_manifest():
    from scripts.download_models import MODELS, WEIGHTS_DIR, _sha256

    fire_weight = WEIGHTS_DIR / "fire_smoke_yolov8n.pt"
    if fire_weight.exists():
        assert _sha256(fire_weight) == MODELS["fire_smoke_yolov8n.pt"]["sha256"]

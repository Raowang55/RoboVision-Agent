"""Download the reproducible, third-party weights used by the demo.

The model binaries intentionally stay out of Git. This script downloads only
the weights whose public source and checksum are recorded in weights/README.md.
PPE is not downloaded because its upstream provenance is not yet documented.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEIGHTS_DIR = PROJECT_ROOT / "weights"

MODELS = {
    "yolov8s-worldv2.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s-worldv2.pt",
        "sha256": "9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792",
    },
    "fire_smoke_yolov8n.pt": {
        "url": "https://raw.githubusercontent.com/luminous0219/fire-and-smoke-detection-yolov8/main/weights/best.pt",
        "sha256": "ac0a10257b2bc1f20c9d957f8adeeb61dd6140322fc19d0b4a116cb491776d16",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(name: str, *, force: bool = False) -> None:
    config = MODELS[name]
    target = WEIGHTS_DIR / name
    expected_hash = config["sha256"]
    if target.exists() and _sha256(target) == expected_hash and not force:
        print(f"[OK] {name} already exists and passed SHA-256 verification")
        return

    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f"{name}.", suffix=".download", delete=False) as file:
        temporary = Path(file.name)
    try:
        print(f"[DOWNLOAD] {name}")
        with urllib.request.urlopen(config["url"], timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        actual_hash = _sha256(temporary)
        if actual_hash != expected_hash:
            raise RuntimeError(f"SHA-256 mismatch for {name}: expected {expected_hash}, got {actual_hash}")
        temporary.replace(target)
        print(f"[OK] {name} downloaded and verified")
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download RoboVision demo model weights")
    parser.add_argument("--force", action="store_true", help="Re-download files even when their SHA-256 already matches")
    parser.add_argument("--model", choices=[*MODELS, "all"], default="all", help="Model to download")
    args = parser.parse_args()
    selected = MODELS if args.model == "all" else {args.model: MODELS[args.model]}
    try:
        for name in selected:
            _download(name, force=args.force)
    except (OSError, RuntimeError, urllib.error.URLError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

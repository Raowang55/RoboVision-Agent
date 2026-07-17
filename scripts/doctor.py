"""Read-only environment readiness report for RoboVision Agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import (
    DB_PATH,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_PATH,
    FIRE_SMOKE_MODEL,
    LLM_BASE_URL,
    LLM_ENABLED,
    LLM_MODEL,
    PPE_MODEL,
    PROJECT_ROOT,
    WECHAT_ENABLED,
    WECHAT_WEBHOOK_KEY,
    YOLO_WORLD_MODEL,
    YOLO_WORLD_SMALL,
)


def collect_status() -> dict:
    local_embedding = (
        Path(EMBEDDING_MODEL_PATH).expanduser()
        if EMBEDDING_MODEL_PATH
        else PROJECT_ROOT
        / "app"
        / "rag"
        / "models"
        / EMBEDDING_MODEL_NAME.split("/")[0]
        / EMBEDDING_MODEL_NAME.split("/")[-1].replace(".", "___")
    )
    try:
        import imageio_ffmpeg

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_available = Path(ffmpeg_path).is_file()
    except (ImportError, OSError):
        ffmpeg_available = False
        ffmpeg_path = ""

    return {
        "python_project_root": str(PROJECT_ROOT),
        "models": {
            "yolo_world": YOLO_WORLD_MODEL.exists() or YOLO_WORLD_SMALL.exists(),
            "fire_smoke": FIRE_SMOKE_MODEL.exists(),
            "ppe": PPE_MODEL.exists(),
            "embedding_local": local_embedding.exists(),
        },
        "paths": {
            "database_parent_writable": os.access(Path(DB_PATH).parent, os.W_OK),
            "database": DB_PATH,
            "embedding_candidate": str(local_embedding),
        },
        "video": {
            "ffmpeg_available": ffmpeg_available,
            "ffmpeg_path": ffmpeg_path,
        },
        "llm": {
            "enabled": LLM_ENABLED,
            "base_url": LLM_BASE_URL,
            "model": LLM_MODEL,
            "note": "optional; rule routing and retrieval work without it",
        },
        "notification": {
            "enabled": WECHAT_ENABLED,
            "webhook_configured": bool(WECHAT_WEBHOOK_KEY),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check RoboVision runtime readiness")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    status = collect_status()
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return
    print("RoboVision Agent readiness")
    for name, available in status["models"].items():
        print(f"  [{'OK' if available else 'MISSING'}] {name}")
    print(f"  [INFO] LLM enabled: {status['llm']['enabled']} ({status['llm']['model']})")
    print(f"  [INFO] Database: {status['paths']['database']}")
    print(f"  [{'OK' if status['video']['ffmpeg_available'] else 'MISSING'}] FFmpeg video conversion")
    print(f"  [INFO] WeChat enabled: {status['notification']['enabled']} (key configured: {status['notification']['webhook_configured']})")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Centralized configuration for RoboVision-Agent.

All model paths, environment-dependent settings, and deployment
configuration live here.  Uses Pydantic Settings for type-safe,
.env-aware configuration.

Usage::

    from app.config import settings

    print(settings.LLM_MODEL)
    print(settings.YOLO_MODEL_PATH)
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    # ── Pydantic config ──────────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Project root (auto-detected) ─────────────────────────────────
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

    # ── Data directories ─────────────────────────────────────────────
    OUTPUT_DIR: Path = Path("data/outputs")
    LOG_DIR: Path = Path("data/logs")
    REPORTS_DIR: Path = Path("data/reports")
    ALARMS_DIR: Path = Path("data/alarms")
    GRADIO_TEMP_DIR: Path = Path("data/.gradio_temp")
    DEBUG_FRAMES_DIR: Path = Path("data/debug_frames")
    DB_PATH: Path = Path("data/work_order.db")

    # ── Model paths ──────────────────────────────────────────────────
    MODEL_DIR: Path = Path("weights")
    YOLO_WORLD_MODEL: Path = Path("weights/yolov8m-worldv2.pt")
    YOLO_WORLD_SMALL: Path = Path("weights/yolov8s-worldv2.pt")
    FIRE_SMOKE_MODEL: Path = Path("weights/fire_smoke_yolov8n.pt")
    PPE_MODEL: Path = Path("weights/ppe_v8.pt")

    # ── Detection thresholds ─────────────────────────────────────────
    DEFAULT_CONFIDENCE: float = 0.25
    DEFAULT_IOU: float = 0.5
    FIRE_CONF_THRESHOLD: float = 0.5
    SMOKE_CONF_THRESHOLD: float = 0.4
    ALARM_COOLDOWN_SECONDS: float = 5.0
    GROUNDING_BOX_THRESHOLD: float = 0.35
    GROUNDING_TEXT_THRESHOLD: float = 0.25
    LOW_CONF_THRESHOLD: float = 0.3
    VIS_ALPHA: float = 0.4
    VIS_FONT_SCALE: float = 0.7

    # ── LLM / API ────────────────────────────────────────────────────
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL: str = "gemma4:31b"
    LLM_ENABLED: bool = False
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT_SECONDS: float = 30.0
    INTENT_CONFIDENCE_THRESHOLD: float = 0.5
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_MODEL_PATH: str = ""

    # ── Optional heuristics ────────────────────────────────────────
    ENABLE_HSV_FIRE_FALLBACK: bool = False

    # ── Server ───────────────────────────────────────────────────────
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 7861

    # ── WeChat bot ───────────────────────────────────────────────────
    WECHAT_ENABLED: bool = False
    WECHAT_WEBHOOK_KEY: str = ""


# ── Singleton ────────────────────────────────────────────────────────
settings = _Settings()

# ── Resolve relative paths against PROJECT_ROOT ─────────────────────
_ROOT = settings.PROJECT_ROOT
PROJECT_ROOT = _ROOT

OUTPUT_DIR = _ROOT / settings.OUTPUT_DIR
LOG_DIR = _ROOT / settings.LOG_DIR
REPORTS_DIR = _ROOT / settings.REPORTS_DIR
ALARMS_DIR = _ROOT / settings.ALARMS_DIR
GRADIO_TEMP_DIR = _ROOT / settings.GRADIO_TEMP_DIR
DEBUG_FRAMES_DIR = _ROOT / settings.DEBUG_FRAMES_DIR
DB_PATH = str(_ROOT / settings.DB_PATH)

MODEL_DIR = _ROOT / settings.MODEL_DIR
YOLO_WORLD_MODEL = _ROOT / settings.YOLO_WORLD_MODEL
YOLO_WORLD_SMALL = _ROOT / settings.YOLO_WORLD_SMALL
FIRE_SMOKE_MODEL = _ROOT / settings.FIRE_SMOKE_MODEL
PPE_MODEL = _ROOT / settings.PPE_MODEL

DEFAULT_MODEL_PATH = str(YOLO_WORLD_MODEL)

LLM_BASE_URL = settings.LLM_BASE_URL
LLM_MODEL = settings.LLM_MODEL
LLM_ENABLED = settings.LLM_ENABLED
LLM_TEMPERATURE = settings.LLM_TEMPERATURE
LLM_MAX_TOKENS = settings.LLM_MAX_TOKENS
LLM_TIMEOUT_SECONDS = settings.LLM_TIMEOUT_SECONDS
INTENT_CONFIDENCE_THRESHOLD = settings.INTENT_CONFIDENCE_THRESHOLD
EMBEDDING_MODEL_NAME = settings.EMBEDDING_MODEL_NAME
EMBEDDING_MODEL_PATH = settings.EMBEDDING_MODEL_PATH
ENABLE_HSV_FIRE_FALLBACK = settings.ENABLE_HSV_FIRE_FALLBACK

SERVER_HOST = settings.SERVER_HOST
SERVER_PORT = settings.SERVER_PORT

DEFAULT_CONFIDENCE = settings.DEFAULT_CONFIDENCE
DEFAULT_IOU = settings.DEFAULT_IOU
FIRE_CONF_THRESHOLD = settings.FIRE_CONF_THRESHOLD
SMOKE_CONF_THRESHOLD = settings.SMOKE_CONF_THRESHOLD
ALARM_COOLDOWN_SECONDS = settings.ALARM_COOLDOWN_SECONDS
GROUNDING_BOX_THRESHOLD = settings.GROUNDING_BOX_THRESHOLD
GROUNDING_TEXT_THRESHOLD = settings.GROUNDING_TEXT_THRESHOLD
LOW_CONF_THRESHOLD = settings.LOW_CONF_THRESHOLD
VIS_ALPHA = settings.VIS_ALPHA
VIS_FONT_SCALE = settings.VIS_FONT_SCALE

WECHAT_ENABLED = settings.WECHAT_ENABLED
WECHAT_WEBHOOK_KEY = settings.WECHAT_WEBHOOK_KEY
WECHAT_WEBHOOK_URL = (
    f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECHAT_WEBHOOK_KEY}"
)

def ensure_runtime_dirs() -> None:
    """Create runtime directories explicitly during application startup."""
    for directory in [
        OUTPUT_DIR,
        LOG_DIR,
        REPORTS_DIR,
        ALARMS_DIR,
        GRADIO_TEMP_DIR,
        DEBUG_FRAMES_DIR,
        Path(DB_PATH).parent,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

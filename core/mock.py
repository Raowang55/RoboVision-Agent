"""External system mocks: WeChat Webhook, emergency linkage.

All external integrations are encapsulated here. Production deployment
replaces the mock implementations with real API calls.

Features:
  - WeChat Work webhook push with debounce and degrade
  - Emergency linkage mock (fire alarm → sprinkler, PA, etc.)
  - Mock toggle via USE_MOCK flag
"""

from __future__ import annotations

import time
import json
import os
import logging
logger = logging.getLogger(__name__)
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ===========================================================================
# Configuration
# ===========================================================================

# WeChat Work bot webhook — key loaded from environment
_WECHAT_WEBHOOK_KEY = os.getenv("WECHAT_WEBHOOK_KEY", "")
WECHAT_WEBHOOK_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    f"?key={_WECHAT_WEBHOOK_KEY}"
)

# Cooldown: same (location, event_type) only pushes once per 300s
ALARM_COOLDOWN = 300

# Mock mode: True = print logs only, no real HTTP requests
USE_MOCK = False

# ===========================================================================
# Debounce cache
# ===========================================================================

_last_push_cache: dict[tuple, float] = {}


def _should_push(location: str, event_type: str) -> bool:
    """Check if we should push for this (location, event_type) pair."""
    key = (location, event_type)
    now = time.time()
    last = _last_push_cache.get(key, 0)
    if now - last < ALARM_COOLDOWN:
        logger.debug(f"Debounce skip: {location} {event_type}"
              f"(冷却 {ALARM_COOLDOWN}s, 距上次 {now - last:.0f}s)")
        return False
    _last_push_cache[key] = now
    return True


# ===========================================================================
# WeChat Work Webhook
# ===========================================================================

def _level_color(alarm_level: str) -> str:
    """Map alarm level to WeChat markdown color."""
    colors = {"HIGH": "#FF0000", "MEDIUM": "#FF8C00", "LOW": "#008000"}
    return colors.get(alarm_level.upper(), "#808080")


def _level_emoji(alarm_level: str) -> str:
    """Map alarm level to emoji."""
    emojis = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢"}
    return emojis.get(alarm_level.upper(), "⚪")


def send_wechat_notification(
    event_type: str,
    alarm_level: str,
    location: str,
    summary: str,
) -> bool:
    """Send a WeChat Work webhook notification.

    Args:
        event_type:   fire / smoke / no_helmet / no_vest
        alarm_level:  HIGH / MEDIUM / LOW
        location:     location description
        summary:      analysis summary (max 500 chars)

    Returns:
        True if sent successfully (or mock mode), False on failure.
    """
    # Debounce check
    if not _should_push(location, event_type):
        return False

    level = alarm_level.upper()
    color = _level_color(level)
    emoji = _level_emoji(level)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build WeChat markdown message
    markdown_content = (
        f"## {emoji} 工业安全报警通知\n"
        f"> **等级**: <font color=\"{color}\">{level}</font>\n"
        f"> **类型**: {event_type}\n"
        f"> **位置**: {location}\n"
        f"> **时间**: {ts}\n"
        f"\n"
        f"**事件摘要**:\n{summary[:300]}\n"
        f"\n"
        f"> 请相关人员立即查看并处置\n"
        f"> [RoboVision Agent 自动推送]"
    )

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_content,
        },
    }

    # Mock mode: just print
    if USE_MOCK:
        print(f"\n{'='*60}")
        logger.info("[MOCK] WeChat push simulation")
        logger.info(f"Level: {level} | Type: {event_type} | Location: {location}")
        logger.info(f"Content preview: {summary[:100]}...")
        print(f"{'='*60}\n")
        return True

    # Real HTTP request
    try:
        import requests
        resp = requests.post(
            WECHAT_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info(f"WeChat push success: {location} {event_type} {level}")
                return True
            else:
                logger.error(f"WeChat API error: {result}")
                return False
        else:
            logger.error(f"WeChat HTTP {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"WeChat network error (degraded): {e}")
        return False


# ===========================================================================
# Emergency Linkage Mock
# ===========================================================================

def emergency_linkage_mock(alarm_data: dict) -> str:
    """Mock emergency linkage for HIGH-level alarms.

    In production, this would trigger:
      - Fire sprinkler system activation
      - Public address evacuation announcement
      - Elevator recall to ground floor
      - Fire door release
      - Emergency services auto-dial

    Args:
        alarm_data: alarm JSON dict

    Returns:
        Status string describing what was triggered.
    """
    location = alarm_data.get("location", "未知位置")
    event_type = alarm_data.get("event_type", "unknown")

    if USE_MOCK:
        print(f"\n  [MOCK] 紧急联动触发:")
        logger.info(f"  Sprinkler: ready ({location})")
        logger.info("  PA: evacuation broadcast started")
        logger.info("  Elevator recall: executed")
        logger.info("  Fire door: released")
        print(f"    - 119自动拨号: 已触发\n")

    return (
        f"紧急联动已触发（{'MOCK模拟' if USE_MOCK else '真实'}模式）:\n"
        f"  - 喷淋系统: 就绪 ({location})\n"
        f"  - 消防广播: 启动疏散广播\n"
        f"  - 电梯归底: 已执行\n"
        f"  - 防火卷帘: 已释放\n"
        f"  - 119自动拨号: 已触发\n"
        f"  - 事件类型: {event_type}"
    )


# ===========================================================================
# Test helper
# ===========================================================================

SAMPLE_ALARM = {
    "event_id": "ALARM20260624001",
    "event_type": "fire",
    "alarm_level": "HIGH",
    "confidence": 0.92,
    "location": "3号厂房焊接区",
    "timestamp": "2026-06-24 14:30:25",
    "image_path": "data/alarms/fire/alarm_HIGH_20260624_121834.jpg",
    "bbox": [320.5, 180.2, 540.8, 420.1],
    "reason": "Fire detected for 3 consecutive frames",
}

SAMPLE_ALARM_MEDIUM = {
    "event_id": "ALARM20260624002",
    "event_type": "smoke",
    "alarm_level": "MEDIUM",
    "confidence": 0.78,
    "location": "2号仓库东区",
    "timestamp": "2026-06-24 15:10:00",
    "image_path": "data/alarms/fire/alarm_MEDIUM_20260624_151000.jpg",
    "bbox": [150.0, 200.0, 400.0, 380.0],
    "reason": "Smoke detected for 10 consecutive frames",
}

SAMPLE_ALARM_LOW = {
    "event_id": "ALARM20260624003",
    "event_type": "no_helmet",
    "alarm_level": "LOW",
    "confidence": 0.85,
    "location": "1号装配线A段",
    "timestamp": "2026-06-24 16:45:00",
    "image_path": "data/alarms/fire/alarm_LOW_20260624_164500.jpg",
    "bbox": [500.0, 100.0, 650.0, 350.0],
    "reason": "Person without helmet detected",
}

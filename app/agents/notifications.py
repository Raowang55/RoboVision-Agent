"""Optional Enterprise WeChat notification adapter."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime

from app.config import WECHAT_ENABLED, WECHAT_WEBHOOK_KEY, WECHAT_WEBHOOK_URL

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationResult:
    """Safe, UI-ready outcome of one notification attempt."""

    ok: bool
    status: str
    detail: str


def notification_readiness() -> NotificationResult:
    """Return whether a real Webhook request is permitted by configuration."""
    if not WECHAT_ENABLED:
        return NotificationResult(False, "disabled", "企业微信通知已在 .env 中禁用。")
    if not WECHAT_WEBHOOK_KEY:
        return NotificationResult(False, "missing_webhook", "未配置 WECHAT_WEBHOOK_KEY。")
    return NotificationResult(True, "ready", "企业微信通知已启用。")


def _message_content(event_type: str, alarm_level: str, location: str, summary: str) -> str:
    level_label = {"HIGH": "紧急", "MEDIUM": "警告", "LOW": "提示"}
    label = level_label.get(alarm_level.upper(), "告警")
    return (
        f"**【{label}】RoboVision 工业安全告警**\n"
        f"> **等级**：{alarm_level}\n"
        f"> **类型**：{event_type}\n"
        f"> **位置**：{location}\n"
        f"> **摘要**：{summary[:200]}\n"
        f"> **时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


def send_wechat_notification_detail(
    event_type: str,
    alarm_level: str,
    location: str,
    summary: str,
) -> NotificationResult:
    """Send one notification and retain a non-secret, actionable result."""
    readiness = notification_readiness()
    if not readiness.ok:
        logger.info("[WeChat %s] Would notify: %s %s at %s", readiness.status, alarm_level, event_type, location)
        return readiness

    payload = json.dumps(
        {"msgtype": "markdown", "markdown": {"content": _message_content(event_type, alarm_level, location, summary)}},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        WECHAT_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        logger.warning("Enterprise WeChat HTTP error: %s", exc.code)
        return NotificationResult(False, "http_error", f"企业微信接口返回 HTTP {exc.code}。")
    except (OSError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Enterprise WeChat request failed: %s", exc)
        return NotificationResult(False, "request_error", f"企业微信请求失败：{exc}")

    if result.get("errcode") == 0:
        logger.info("Enterprise WeChat notification sent for %s %s", alarm_level, event_type)
        return NotificationResult(True, "sent", "已由企业微信接口确认接收。")

    code = result.get("errcode", "unknown")
    message = str(result.get("errmsg", "unknown error"))[:120]
    logger.warning("Enterprise WeChat API rejected notification: errcode=%s, errmsg=%s", code, message)
    return NotificationResult(False, "api_rejected", f"企业微信接口拒绝请求（{code}: {message}）。")


def send_wechat_notification(
    event_type: str,
    alarm_level: str,
    location: str,
    summary: str,
) -> bool:
    """Backward-compatible boolean interface for workflow callers."""
    return send_wechat_notification_detail(event_type, alarm_level, location, summary).ok

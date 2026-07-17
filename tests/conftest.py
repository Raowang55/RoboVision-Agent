"""Global isolation from external LLM and notification services."""

import os

# These values must be set before pytest imports any application module.
# Real provider checks use the explicit ``llm`` marker outside the fast suite.
os.environ["LLM_ENABLED"] = "false"
os.environ["WECHAT_ENABLED"] = "false"

import pytest


@pytest.fixture(autouse=True)
def disable_external_notifications(monkeypatch):
    import app.agents.notifications as notification_adapter

    monkeypatch.setattr(notification_adapter, "WECHAT_ENABLED", False)
    monkeypatch.setattr(notification_adapter, "WECHAT_WEBHOOK_KEY", "")

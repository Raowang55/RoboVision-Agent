"""Small OpenAI-compatible chat client used as an optional enhancement.

The same interface works with Ollama's OpenAI endpoint, DeepSeek, and other
providers that implement ``/v1/chat/completions``. Callers decide whether the
LLM is enabled; this module performs one bounded request and never retries for
minutes in the foreground.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.config import LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT_SECONDS

load_dotenv()

logger = logging.getLogger(__name__)

_api_base_url = LLM_BASE_URL
_api_model = LLM_MODEL
_api_key = os.getenv("LLM_API_KEY", "")


def configure(api_base_url: str = "", api_model: str = "", api_key: str = "") -> None:
    """Update connection settings for the current process."""
    global _api_base_url, _api_model, _api_key
    if api_base_url.strip():
        _api_base_url = api_base_url.strip().rstrip("/")
    if api_model.strip():
        _api_model = api_model.strip()
    if api_key.strip():
        _api_key = api_key.strip()


def chat(
    messages: list[dict[str, str]],
    temperature: float = LLM_TEMPERATURE,
    max_tokens: int = 1200,
    timeout_seconds: float = LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Send one OpenAI-compatible request and return a provider-neutral dict."""
    try:
        client = OpenAI(
            api_key=_api_key or "ollama",
            base_url=_api_base_url.rstrip("/"),
            timeout=timeout_seconds,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=_api_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return {
            "success": True,
            "content": content.strip(),
            "model": response.model or _api_model,
            "error": None,
        }
    except Exception as exc:
        logger.warning("Optional LLM request failed: %s", exc)
        return {
            "success": False,
            "content": "",
            "model": _api_model,
            "error": str(exc),
        }

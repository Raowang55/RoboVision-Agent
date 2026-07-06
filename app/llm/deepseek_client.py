"""LLM API client using Ollama native API format.

Reads API key, base URL, and model from environment variables.
Uses Ollama cloud /api/chat endpoint with Bearer auth.
Never hardcodes credentials.
"""

import json
import os
import time
from pathlib import Path

# Load .env file if present
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# ---------------------------------------------------------------------------
# configuration from environment
# ---------------------------------------------------------------------------

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://ollama.com/api")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "qwen3-coder-next")

# Timeout settings (seconds)
LLM_CONNECT_TIMEOUT = 15
LLM_READ_TIMEOUT = 300

# Retry settings
LLM_MAX_RETRIES = 3
LLM_RETRY_BACKOFF = 2  # base seconds for exponential backoff


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def chat(
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> dict:
    """Send a chat request to the Ollama API with retry logic.

    Args:
        messages:    List of {"role": "...", "content": "..."} dicts.
        temperature: Sampling temperature (0.0-2.0).
        max_tokens:  Maximum tokens in the response.

    Returns:
        dict with:
            - success:  bool
            - content:  str   (the assistant's reply)
            - model:    str   (model used)
            - error:    str | None
    """
    if not DEEPSEEK_API_KEY:
        return {
            "success": False,
            "content": "",
            "model": DEEPSEEK_MODEL,
            "error": (
                "Qwen3-VL API key 未配置。"
                "请在 .env 文件中设置 DEEPSEEK_API_KEY。"
            ),
        }

    try:
        import requests

        # Ollama native API endpoint: /api/chat
        url = f"{DEEPSEEK_BASE_URL}/chat"

        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        }

        last_error = None
        for attempt in range(1, LLM_MAX_RETRIES + 1):
            try:
                # Encode payload as UTF-8 explicitly (Windows GBK default corrupts Chinese)
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                response = requests.post(
                    url,
                    headers=headers,
                    data=body,
                    timeout=(LLM_CONNECT_TIMEOUT, LLM_READ_TIMEOUT),
                )
                response.raise_for_status()

                result = response.json()
                content = result.get("message", {}).get("content", "")
                return {
                    "success": True,
                    "content": content.strip() if content else "",
                    "model": result.get("model", DEEPSEEK_MODEL),
                    "error": None,
                }

            except requests.exceptions.Timeout as exc:
                last_error = exc
                if attempt < LLM_MAX_RETRIES:
                    wait = LLM_RETRY_BACKOFF * (2 ** (attempt - 1))
                    time.sleep(wait)
                continue
            except requests.exceptions.HTTPError as exc:
                last_error = exc
                # Don't retry on auth errors (401/403) or bad requests (400)
                status_code = exc.response.status_code if exc.response else 0
                if status_code in (400, 401, 403, 404):
                    return {
                        "success": False,
                        "content": "",
                        "model": DEEPSEEK_MODEL,
                        "error": f"Qwen3-VL API 错误 ({status_code}): {exc}",
                    }
                if attempt < LLM_MAX_RETRIES:
                    wait = LLM_RETRY_BACKOFF * (2 ** (attempt - 1))
                    time.sleep(wait)
                continue
            except Exception as exc:
                last_error = exc
                if attempt < LLM_MAX_RETRIES:
                    wait = LLM_RETRY_BACKOFF * (2 ** (attempt - 1))
                    time.sleep(wait)
                continue

        # All retries exhausted
        return {
            "success": False,
            "content": "",
            "model": DEEPSEEK_MODEL,
            "error": f"Qwen3-VL API 调用失败（重试 {LLM_MAX_RETRIES} 次后）: {last_error}",
        }

    except ImportError:
        return {
            "success": False,
            "content": "",
            "model": DEEPSEEK_MODEL,
            "error": "缺少 requests 库，请运行: pip install requests",
        }
    except Exception as exc:
        return {
            "success": False,
            "content": "",
            "model": DEEPSEEK_MODEL,
            "error": f"Qwen3-VL API 初始化失败: {exc}",
        }
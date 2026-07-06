"""RAG + Qwen3-VL module health check.

Usage:
    python scripts/test_rag.py

Checks:
    1. .env and DEEPSEEK_API_KEY
    2. Embedding model loading
    3. Chroma index building
    4. RAG query (retrieval + LLM generation)

Prints a summary at the end.
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

PASS = "[PASS]"
FAIL = "[FAIL]"


def check_env() -> bool:
    """Check .env exists and DEEPSEEK_API_KEY is readable."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        print(f"  {FAIL} .env file not found at {env_path}")
        print("         Create it with: DEEPSEEK_API_KEY=sk-...")
        return False

    from dotenv import load_dotenv
    load_dotenv(env_path)

    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        print(f"  {FAIL} DEEPSEEK_API_KEY is empty in .env")
        return False

    masked = key[:6] + "..." if len(key) > 6 else "***"
    base = os.getenv("DEEPSEEK_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.getenv("DEEPSEEK_MODEL", "qwen3-vl")
    print(f"  {PASS} DEEPSEEK_API_KEY = {masked}")
    print(f"         DEEPSEEK_BASE_URL = {base}")
    print(f"         DEEPSEEK_MODEL = {model}")
    return True


def check_embedding_model() -> bool:
    """Check that the embedding model loads successfully."""
    try:
        from app.rag.vector_store import _get_model, _embed_texts
        model = _get_model()
        emb = _embed_texts(["测试"])
        dim = len(emb[0])
        print(f"  {PASS} Embedding model loaded, dim={dim}")
        return True
    except Exception as e:
        print(f"  {FAIL} Embedding model failed: {e}")
        return False


def check_index() -> bool:
    """Check that the Chroma index can be built."""
    try:
        from app.rag.rag_tool import build_index
        result = build_index()
        if result["status"] == "ok":
            print(f"  {PASS} Index built: {result['document_count']} chunks, dim={result.get('embedding_dim', '?')}")
            return True
        else:
            print(f"  {FAIL} Index build returned: {result}")
            return False
    except Exception as e:
        print(f"  {FAIL} Index build failed: {e}")
        return False


def check_rag_query() -> bool:
    """Check that rag_query returns a valid answer via Qwen3-VL."""
    try:
        from app.rag.rag_tool import rag_query
        result = rag_query("检测到烟雾后应该怎么处理？", use_llm=True)

        has_answer = bool(result.get("answer"))
        used_llm = result.get("used_llm", False)
        model = result.get("model", "?")
        sources = result.get("source_files", [])

        print(f"  {PASS if has_answer else FAIL} answer returned ({len(result.get('answer', ''))} chars)")
        print(f"  {PASS if used_llm else FAIL} used_llm = {used_llm}")
        print(f"         model = {model}")
        print(f"  {PASS if sources else FAIL} source_files = {sources}")

        if has_answer and used_llm and sources:
            return True
        return False
    except Exception as e:
        print(f"  {FAIL} rag_query failed: {e}")
        return False


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  RoboVision-Agent  RAG + Qwen3-VL  Health Check")
    print("=" * 60)
    print()

    results = {}

    print("[1/4] Checking .env ...")
    results["env"] = check_env()
    print()

    print("[2/4] Checking embedding model ...")
    results["embedding"] = check_embedding_model()
    print()

    print("[3/4] Building Chroma index ...")
    results["index"] = check_index()
    print()

    print("[4/4] Testing RAG query (Qwen3-VL) ...")
    results["rag"] = check_rag_query()
    print()

    # ---- summary ----
    print("=" * 60)
    all_ok = all(results.values())
    status = "ALL PASSED" if all_ok else "SOME FAILED"
    print(f"  Result: {status}")
    for name, ok in results.items():
        print(f"    {PASS if ok else FAIL} {name}")
    print("=" * 60)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
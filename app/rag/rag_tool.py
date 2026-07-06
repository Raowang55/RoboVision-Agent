"""RAG tool: unified entry point for knowledge-base Q&A.

Orchestrates document loading, vector search, prompt building,
and Qwen3-VL API calls with fallback.
"""

from pathlib import Path

# Default knowledge base directory
KB_DIR = str(Path(__file__).resolve().parent / "knowledge_base")


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def build_index(kb_dir: str | None = None) -> dict:
    """Build the vector index from the knowledge base.

    Args:
        kb_dir: Path to knowledge base directory. Defaults to app/rag/knowledge_base/.

    Returns:
        dict from vector_store.build_index.
    """
    from app.rag.vector_store import build_index as _build

    target = kb_dir or KB_DIR
    return _build(target)


def rag_query(
    question: str,
    top_k: int = 4,
    log_context: dict | None = None,
    use_llm: bool = True,
    history: list[dict] | None = None,
) -> dict:
    """Run a RAG query: retrieve relevant chunks, then optionally call Qwen3-VL.

    Args:
        question:    The user's question.
        top_k:       Number of chunks to retrieve.
        log_context: Optional event log summary dict.
        use_llm:     Whether to call Qwen3-VL API (True) or just return chunks (False).

    Returns:
        dict with:
            - answer:           str
            - retrieved_chunks: list[dict]
            - source_files:     list[str]
            - log_context:      dict | None
            - used_llm:         bool
            - model:            str | None
    """
    from app.rag.vector_store import search
    from app.rag.prompt_builder import build_rag_prompt, build_fallback_answer

    # ---- Step 1: retrieve relevant chunks ----
    retrieved = search(question, top_k=top_k)

    # ---- Step 2: collect unique source files ----
    source_files = list(dict.fromkeys(chunk["source"] for chunk in retrieved))

    # ---- Step 3: generate answer ----
    answer = ""
    used_llm = False
    model = None

    if use_llm and retrieved:
        from app.llm.deepseek_client import chat, DEEPSEEK_MODEL

        # Build messages with optional conversation history
        if history:
            # Build knowledge context for the system prompt
            knowledge_parts = []
            for i, chunk in enumerate(retrieved, 1):
                knowledge_parts.append(
                    f"[Source {i}: {chunk['source']} | {chunk['chunk_id']}]\n{chunk['text']}"
                )
            knowledge_text = "\n\n---\n\n".join(knowledge_parts) if knowledge_parts else "(no relevant chunks)"

            system_msg = (
                "You are an industrial vision safety expert. "
                "Answer questions based on the knowledge base chunks below. "
                "If the knowledge base does not contain relevant information, "
                "clearly state that you cannot answer and do not fabricate content.\n\n"
                f"## Knowledge Base Chunks\n{knowledge_text}"
            )

            # Keep at most the last 5 rounds (10 messages)
            recent_history = history[-10:] if len(history) > 10 else history

            messages = [{"role": "system", "content": system_msg}]
            messages.extend(recent_history)
            messages.append({"role": "user", "content": question})
        else:
            messages = build_rag_prompt(question, retrieved, log_context)

        llm_result = chat(messages)

        if llm_result["success"]:
            answer = llm_result["content"]
            used_llm = True
            model = llm_result["model"]
        else:
            # LLM failed, fallback to retrieval-only
            answer = (
                f"*Qwen3-VL API 调用失败: {llm_result['error']}*\n\n"
                + build_fallback_answer(question, retrieved, log_context)
            )
    else:
        # No LLM requested, or no chunks found
        answer = build_fallback_answer(question, retrieved, log_context)

    return {
        "answer": answer,
        "retrieved_chunks": retrieved,
        "source_files": source_files,
        "log_context": log_context,
        "used_llm": used_llm,
        "model": model,
    }

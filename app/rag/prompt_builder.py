# -*- coding: utf-8 -*-
"""Prompt builder for RAG-based Q&A with Gemma.

Constructs a system prompt that forces the model to:
- Base answers on provided knowledge chunks
- Cite sources
- Explain reasoning
- Give actionable advice
- Disclose when evidence is insufficient
"""


def build_rag_prompt(
    question: str,
    retrieved_chunks: list[dict],
    log_context: dict | None = None,
) -> list[dict]:
    """Build a messages list for the Gemma chat API.

    Args:
        question:         The user's question.
        retrieved_chunks: List of {"text", "source", "chunk_id"} from vector search.
        log_context:      Optional dict with event log summary.

    Returns:
        List of {"role": "...", "content": "..."} messages.
    """
    # ---- build knowledge context ----
    knowledge_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        knowledge_parts.append(
            f"[Source {i}: {chunk['source']} | {chunk['chunk_id']}]\n{chunk['text']}"
        )
    knowledge_text = "\n\n---\n\n".join(knowledge_parts) if knowledge_parts else "(no relevant chunks)"

    # ---- build log context ----
    log_text = ""
    if log_context:
        log_text = f"""
## Recent Event Log
- Total events: {log_context.get('total_events', 0)}
- Alarm events: {log_context.get('total_alarms', 0)}
- Recent alarms: {log_context.get('recent_alarms', [])}
"""

    # ---- system prompt ----
    system_prompt = f"""You are an industrial vision safety assistant called RoboVision Agent.

# Your job is to answer questions about industrial vision, safety regulations,
# alarm handling, model deployment, and system commands based on provided context.

## Answer Requirements
1. **Evidence Basis**: Explain which knowledge base source your judgment is based on.
2. **Reasoning**: Explain why you made this judgment.
3. **Actionable Advice**: Provide specific, actionable steps.
4. **Cite Sources**: List the knowledge base files cited at the end of your answer.
5. **Risk Warning**: If safety risks exist, you must clearly warn about them.

## Important Constraints
- Only answer based on the knowledge base chunks and logs provided below.
- If knowledge base evidence is insufficient, clearly state "Based on the available KB, cannot give a definitive answer"
-- do not fabricate information.
- For life-safety questions, remind users to follow actual on-site conditions.
---

## Knowledge Base Chunks
{knowledge_text}

{log_text}
"""

    user_prompt = f"User question: {question}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_fallback_answer(
    question: str,
    retrieved_chunks: list[dict],
    log_context: dict | None = None,
) -> str:
    """Build a retrieval-only answer without requiring an LLM.

    This is a simple concatenation of relevant chunks with a header.
    """
    lines = [
        f'## "{question}" 检索结果',
        "",
        "*当前使用离线检索模式，以下为命中的知识库片段：*",
        "",
    ]

    if log_context:
        events = log_context.get('total_events', 0)
        alarms = log_context.get('total_alarms', 0)
        lines.append(f"- Recent events: {events} total, {alarms} alarms")
        lines.append("")

    if not retrieved_chunks:
        lines.append("*No relevant knowledge base chunks found.*")
    else:
        for i, chunk in enumerate(retrieved_chunks, 1):
            lines.append(f"### Chunk {i} -- {chunk['source']}")
            lines.append("")
            lines.append(chunk["text"][:300])
            lines.append("")

    return "\n".join(lines)

"""Document loader: reads .md and .txt files and splits into chunks."""

from pathlib import Path


def load_documents(kb_dir: str) -> list[dict]:
    """Load all .md and .txt files from a knowledge base directory.

    Returns a list of dicts with keys: text, source, chunk_id.
    """
    kb_path = Path(kb_dir)
    if not kb_path.exists():
        return []

    docs = []
    for file_path in sorted(kb_path.glob("*.md")) + sorted(kb_path.glob("*.txt")):
        raw = file_path.read_text(encoding="utf-8")
        chunks = split_text(raw, source=file_path.name)
        docs.extend(chunks)

    return docs


def split_text(
    text: str,
    source: str = "unknown",
    chunk_size: int = 500,
    overlap: int = 80,
) -> list[dict]:
    """Split a text into overlapping chunks.

    Args:
        text:       The raw text to split.
        source:     Source filename for tracking.
        chunk_size: Maximum characters per chunk.
        overlap:    Overlap between adjacent chunks.

    Returns:
        List of {"text": ..., "source": ..., "chunk_id": ...}.
    """
    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]

        chunks.append({
            "text": chunk_text.strip(),
            "source": source,
            "chunk_id": f"{source}#{chunk_idx}",
        })

        chunk_idx += 1
        start = end - overlap

        # Prevent infinite loop on short texts
        if start >= len(text):
            break
        if start <= 0:
            start = end

    return chunks

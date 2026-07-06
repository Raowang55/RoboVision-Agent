"""Vector store: semantic embedding + Chroma persistence.

Uses sentence-transformers (BAAI/bge-small-zh-v1.5) for embeddings
and ChromaDB as the local vector database.
"""

import atexit
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

# Local model path (downloaded via ModelScope)
_MODEL_DIR = Path(__file__).resolve().parent / "models" / "BAAI" / "bge-small-zh-v1___5"
# HuggingFace model name (fallback if local model not found)
_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

CHROMA_PERSIST_DIR = str(Path(__file__).resolve().parent / "chroma_db")
COLLECTION_NAME = "robo_knowledge"

# Lazy-loaded singletons
_model = None
_chroma_client = None


# ---------------------------------------------------------------------------
# embedding
# ---------------------------------------------------------------------------

def _get_model():
    """Load and cache the sentence-transformers model.

    Tries the local ModelScope download first, then falls back to
    downloading from HuggingFace.

    Returns:
        SentenceTransformer instance.

    Raises:
        RuntimeError with clear instructions if model cannot be loaded.
    """
    global _model
    if _model is not None:
        return _model

    from sentence_transformers import SentenceTransformer

    # Try local model path first (downloaded via ModelScope)
    if _MODEL_DIR.exists():
        _model = SentenceTransformer(str(_MODEL_DIR))
        _model.thread_pool_size = 1
        return _model

    # Try HuggingFace
    try:
        _model = SentenceTransformer(_MODEL_NAME)
        _model.thread_pool_size = 1
        return _model
    except Exception as hf_error:
        raise RuntimeError(
            f"Failed to load embedding model '{_MODEL_NAME}'.\n"
            f"HuggingFace error: {hf_error}\n\n"
            "To fix this, download the model from ModelScope:\n"
            "  python -c \"from modelscope import snapshot_download; "
            "snapshot_download('BAAI/bge-small-zh-v1.5', "
            "cache_dir='app/rag/models')\"\n"
            f"Expected local path: {_MODEL_DIR}"
        ) from hf_error


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert a list of texts to normalized embeddings."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


# ---------------------------------------------------------------------------
# Chroma client
# ---------------------------------------------------------------------------

def _get_chroma_client():
    """Return a cached ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        atexit.register(_close_chroma_client)
    return _chroma_client


def _close_chroma_client():
    """Gracefully shut down the ChromaDB client to avoid 'interpreter shutdown' errors."""
    global _chroma_client
    if _chroma_client is not None:
        try:
            _chroma_client._system.stop()
        except Exception:
            pass
        _chroma_client = None


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def build_index(kb_dir: str) -> dict:
    """Build (or rebuild) the semantic vector index from a knowledge base.

    Args:
        kb_dir: Path to the directory containing .md / .txt files.

    Returns:
        dict with status info.
    """
    from app.rag.document_loader import load_documents

    docs = load_documents(kb_dir)
    if not docs:
        return {
            "status": "empty",
            "document_count": 0,
            "message": f"No documents found in {kb_dir}",
        }

    client = _get_chroma_client()

    # Delete existing collection to avoid duplicates
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(name=COLLECTION_NAME)

    texts = [d["text"] for d in docs]
    ids = [d["chunk_id"] for d in docs]
    metadatas = [{"source": d["source"], "chunk_id": d["chunk_id"]} for d in docs]

    embeddings = _embed_texts(texts)

    collection.add(
        embeddings=embeddings,
        documents=texts,
        ids=ids,
        metadatas=metadatas,
    )

    return {
        "status": "ok",
        "document_count": len(docs),
        "collection": COLLECTION_NAME,
        "persist_dir": CHROMA_PERSIST_DIR,
        "embedding_model": str(_MODEL_DIR) if _MODEL_DIR.exists() else _MODEL_NAME,
        "embedding_dim": len(embeddings[0]),
        "message": f"Index built with {len(docs)} chunks from {kb_dir}",
    }


def search(question: str, top_k: int = 4) -> list[dict]:
    """Search the vector index for the most relevant chunks.

    Args:
        question: The query string.
        top_k:    Number of chunks to retrieve.

    Returns:
        List of {"text": ..., "source": ..., "chunk_id": ..., "score": ...}.
    """
    client = _get_chroma_client()

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return []

    query_embedding = _embed_texts([question])

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count()),
    )

    chunks = []
    if results["documents"] and results["documents"][0]:
        for i, doc_text in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            # Extract distance/score if available
            dist = None
            if results.get("distances") and results["distances"][0]:
                dist = results["distances"][0][i]
            chunks.append({
                "text": doc_text,
                "source": meta.get("source", "unknown"),
                "chunk_id": meta.get("chunk_id", "?"),
                "score": round(1.0 - dist, 4) if dist is not None else None,
            })

    return chunks

"""Local SentenceTransformer + Chroma knowledge index."""

from __future__ import annotations

import atexit
import hashlib
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_PATH

logger = logging.getLogger(__name__)

_RAG_DIR = Path(__file__).resolve().parent
_MODEL_DIR = (
    Path(EMBEDDING_MODEL_PATH).expanduser()
    if EMBEDDING_MODEL_PATH
    else _RAG_DIR / "models" / EMBEDDING_MODEL_NAME.split("/")[0] / EMBEDDING_MODEL_NAME.split("/")[-1].replace(".", "___")
)
CHROMA_PERSIST_DIR = str(_RAG_DIR / "chroma_db")
COLLECTION_NAME = "robo_knowledge"

_model = None
_chroma_client = None


def _get_model():
    """Load a configured local embedding model or the public model name."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        model_source = str(_MODEL_DIR) if _MODEL_DIR.exists() else EMBEDDING_MODEL_NAME
        try:
            _model = SentenceTransformer(model_source)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load embedding model from '{model_source}'. "
                "Run scripts/doctor.py for setup guidance."
            ) from exc
    return _model


def _embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    embeddings = _get_model().encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        atexit.register(_close_chroma_client)
    return _chroma_client


def _close_chroma_client() -> None:
    global _chroma_client
    if _chroma_client is not None:
        try:
            _chroma_client._system.stop()
        except Exception:
            logger.debug("Chroma client was already stopped", exc_info=True)
        _chroma_client = None


def _knowledge_hash(kb_dir: str | Path) -> str:
    root = Path(kb_dir)
    digest = hashlib.sha256()
    for path in sorted([*root.glob("*.md"), *root.glob("*.txt")]):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build_index(kb_dir: str) -> dict[str, Any]:
    """Rebuild the persistent index from Markdown and text files."""
    from app.rag.document_loader import load_documents

    documents = load_documents(kb_dir)
    if not documents:
        return {
            "status": "empty",
            "document_count": 0,
            "message": f"No documents found in {kb_dir}",
        }

    client = _get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        logger.debug("No previous RAG collection to delete")

    kb_hash = _knowledge_hash(kb_dir)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "kb_hash": kb_hash},
    )
    texts = [item["text"] for item in documents]
    embeddings = _embed_texts(texts)
    collection.add(
        embeddings=embeddings,
        documents=texts,
        ids=[item["chunk_id"] for item in documents],
        metadatas=[
            {"source": item["source"], "chunk_id": item["chunk_id"]}
            for item in documents
        ],
    )
    return {
        "status": "ok",
        "document_count": len(documents),
        "collection": COLLECTION_NAME,
        "persist_dir": CHROMA_PERSIST_DIR,
        "embedding_model": str(_MODEL_DIR) if _MODEL_DIR.exists() else EMBEDDING_MODEL_NAME,
        "embedding_dim": len(embeddings[0]),
        "kb_hash": kb_hash,
        "message": f"Index built with {len(documents)} chunks from {kb_dir}",
    }


def ensure_index(kb_dir: str | None = None) -> dict[str, Any]:
    """Create or refresh the index when the knowledge files change."""
    target = kb_dir or str(_RAG_DIR / "knowledge_base")
    expected_hash = _knowledge_hash(target)
    client = _get_chroma_client()
    try:
        collection = client.get_collection(COLLECTION_NAME)
        metadata = collection.metadata or {}
        if collection.count() > 0 and metadata.get("kb_hash") == expected_hash:
            return {
                "status": "ready",
                "document_count": collection.count(),
                "kb_hash": expected_hash,
                "message": "Index is current.",
            }
    except Exception:
        pass
    return build_index(target)


def search(question: str, top_k: int = 4, kb_dir: str | None = None) -> list[dict[str, Any]]:
    """Return the most relevant chunks with cosine relevance scores."""
    if not question or not question.strip() or top_k <= 0:
        return []
    status = ensure_index(kb_dir)
    if status.get("status") == "empty":
        return []

    collection = _get_chroma_client().get_collection(COLLECTION_NAME)
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_embeddings=_embed_texts([question]),
        n_results=min(int(top_k), count),
    )
    chunks: list[dict[str, Any]] = []
    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]
    for index, text in enumerate(documents[0]):
        metadata = metadatas[0][index] if metadatas[0] else {}
        distance = distances[0][index] if distances[0] else None
        relevance = max(0.0, min(1.0, 1.0 - float(distance))) if distance is not None else None
        chunks.append(
            {
                "text": text,
                "source": metadata.get("source", "unknown"),
                "chunk_id": metadata.get("chunk_id", "?"),
                "score": round(relevance, 4) if relevance is not None else None,
            }
        )
    return chunks

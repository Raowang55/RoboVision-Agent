# -*- coding: utf-8 -*-
"""Tests for app/rag/ modules -- document_loader, prompt_builder, vector_store."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestDocumentLoader:
    def test_load_documents_from_empty_dir(self):
        from app.rag.document_loader import load_documents
        with tempfile.TemporaryDirectory() as tmp:
            docs = load_documents(tmp)
            assert isinstance(docs, list)

    def test_load_documents_with_markdown(self):
        from app.rag.document_loader import load_documents
        with tempfile.TemporaryDirectory() as tmp:
            md_file = Path(tmp) / "test.md"
            md_file.write_text("# Test\\n\\nThis is a test document.", encoding="utf-8")
            docs = load_documents(tmp)
            assert len(docs) >= 1

    def test_load_documents_nonexistent_dir(self):
        from app.rag.document_loader import load_documents
        docs = load_documents("/nonexistent/path/xyz789")
        assert docs == []

    def test_split_text_empty(self):
        from app.rag.document_loader import split_text
        result = split_text("")
        assert isinstance(result, list)

    def test_split_text_short(self):
        from app.rag.document_loader import split_text
        result = split_text("Short text.")
        assert len(result) >= 1


class TestPromptBuilder:
    def test_build_rag_prompt_returns_string(self):
        from app.rag.prompt_builder import build_rag_prompt
        prompt = build_rag_prompt(
            question="What are safety rules?",
            retrieved_chunks=[{"text": "Rule 1: Wear helmet", "source": "test.md", "chunk_id": "0"}],
        )
        assert isinstance(prompt, list)
        assert len(prompt) == 2
        assert prompt[0]["role"] == "system"
        assert prompt[1]["role"] == "user"
        assert len(prompt) > 0

    def test_build_rag_prompt_no_context(self):
        from app.rag.prompt_builder import build_rag_prompt
        prompt = build_rag_prompt(question="Test?", retrieved_chunks=[])
        assert isinstance(prompt, list)
        assert len(prompt) == 2

    def test_build_fallback_answer(self):
        from app.rag.prompt_builder import build_fallback_answer
        answer = build_fallback_answer("What is fire?", retrieved_chunks=[])
        assert isinstance(answer, str)


class TestVectorStore:
    @pytest.fixture
    def isolated_store(self, tmp_path, monkeypatch):
        import numpy as np

        from app.rag import vector_store

        vector_store._close_chroma_client()
        monkeypatch.setattr(vector_store, "CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))

        def fake_embed(texts):
            vectors = []
            for text in texts:
                vector = np.zeros(64, dtype=float)
                for token in text.lower().split():
                    vector[sum(token.encode("utf-8")) % len(vector)] += 1.0
                norm = np.linalg.norm(vector) or 1.0
                vectors.append((vector / norm).tolist())
            return vectors

        monkeypatch.setattr(vector_store, "_embed_texts", fake_embed)
        kb_dir = tmp_path / "kb"
        kb_dir.mkdir()
        (kb_dir / "fire.md").write_text(
            "# Fire safety\nFire safety requires an extinguisher and evacuation.",
            encoding="utf-8",
        )
        (kb_dir / "ppe.md").write_text(
            "# PPE rules\nWorkers must wear a helmet and reflective vest.",
            encoding="utf-8",
        )
        yield vector_store, kb_dir
        vector_store._close_chroma_client()

    def test_build_index_and_search(self, isolated_store):
        vector_store, kb_dir = isolated_store
        status = vector_store.build_index(str(kb_dir))
        assert status["status"] == "ok"
        results = vector_store.search("fire safety extinguisher", top_k=2, kb_dir=str(kb_dir))
        assert results
        assert results[0]["source"] == "fire.md"
        assert results[0]["chunk_id"]

    def test_ensure_index_rebuilds_after_source_change(self, isolated_store):
        vector_store, kb_dir = isolated_store
        first = vector_store.ensure_index(str(kb_dir))
        (kb_dir / "fire.md").write_text("# Fire safety\nUpdated evacuation rules.", encoding="utf-8")
        second = vector_store.ensure_index(str(kb_dir))
        assert first["kb_hash"] != second["kb_hash"]
        assert second["status"] == "ok"

    def test_search_empty_query_does_not_build(self, isolated_store):
        vector_store, kb_dir = isolated_store
        assert vector_store.search("", top_k=1, kb_dir=str(kb_dir)) == []

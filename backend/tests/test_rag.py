import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import rag


class FakeEmbeddingProvider:
    def index_document(self, text):
        chunks = [part.strip() for part in text.split("\n\n") if part.strip()]
        return [
            {
                "chunk_index": index,
                "text": chunk,
                "token_count": len(chunk.split()),
                "embedding": self._embed(chunk).tolist(),
            }
            for index, chunk in enumerate(chunks)
        ]

    def embed_query(self, text):
        return self._embed(text)

    @staticmethod
    def _embed(text):
        lowered = text.lower()
        return np.asarray([
            float("mitosis" in lowered or "cells" in lowered),
            float("photosynthesis" in lowered or "chlorophyll" in lowered),
            float("algebra" in lowered or "equation" in lowered),
        ], dtype="float32")


@pytest.fixture(autouse=True)
def fake_rag_dependencies(monkeypatch):
    monkeypatch.setattr(rag, "_embedding_provider", FakeEmbeddingProvider())
    monkeypatch.setenv("VECTOR_STORE", "memory")
    rag.clear_session_indexes()
    yield
    rag.clear_session_indexes()
    rag._embedding_provider = None


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "learnloop-rag-test.db"
    monkeypatch.setenv("SUPABASE_DB_URI", f"sqlite:///{db_path}")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))

    sys.modules.pop("main", None)
    module = importlib.import_module("main")

    with module.app.app_context():
        module.db.create_all()

    yield module.app.test_client()

    with module.app.app_context():
        module.db.session.remove()
        module.db.drop_all()


def test_document_indexing_and_retrieval_use_the_provider_and_store(client):
    ingest_response = client.post(
        "/rag/ingest",
        json={
            "session_id": "biology",
            "source_id": "bio-notes",
            "text": "Mitosis divides cells.\n\nPhotosynthesis uses chlorophyll.",
        },
    )

    assert ingest_response.status_code == 201
    assert ingest_response.get_json()["chunks_indexed"] == 2

    retrieve_response = client.post(
        "/rag/retrieve",
        json={"session_id": "biology", "query": "How do cells divide?", "top_k": 1},
    )

    assert retrieve_response.status_code == 200
    body = retrieve_response.get_json()
    assert body["latency_ms"] >= 0
    assert len(body["chunks"]) == 1
    assert body["chunks"][0]["source_id"] == "bio-notes"
    assert "Mitosis divides cells" in body["chunks"][0]["text"]


def test_retrieval_is_scoped_to_session(client):
    client.post(
        "/rag/ingest",
        json={"session_id": "session-a", "source_id": "algebra", "text": "Algebra solves equations."},
    )
    client.post(
        "/rag/ingest",
        json={"session_id": "session-b", "source_id": "biology", "text": "Mitosis divides cells."},
    )

    response = client.post(
        "/rag/retrieve",
        json={"session_id": "session-a", "query": "How do cells divide?", "top_k": 5},
    )

    assert response.status_code == 200
    chunks = response.get_json()["chunks"]
    assert [chunk["source_id"] for chunk in chunks] == ["algebra"]
    assert all(chunk["session_id"] == "session-a" for chunk in chunks)


def test_reindexing_replaces_a_source_without_duplicates(client):
    rag.ingest_study_material("biology", "Mitosis divides cells.", "notes")
    rag.ingest_study_material("biology", "Algebra solves equations.", "notes")

    result = rag.retrieve_chunks("biology", "What solves equations?", top_k=5)

    assert len(result["chunks"]) == 1
    assert result["chunks"][0]["text"] == "Algebra solves equations."

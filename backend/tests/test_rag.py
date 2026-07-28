import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import rag


class FakeTokenizer:
    def __init__(self):
        self.tokens = {}
        self.values = {}

    def encode(self, text, add_special_tokens=False):
        ids = []
        for token in text.split():
            if token not in self.tokens:
                token_id = len(self.tokens) + 1
                self.tokens[token] = token_id
                self.values[token_id] = token
            ids.append(self.tokens[token])
        return ids

    def decode(self, token_ids, skip_special_tokens=True):
        return " ".join(self.values[token_id] for token_id in token_ids)

    def num_special_tokens_to_add(self, pair=False):
        return 2


class FakeEmbeddingModel:
    max_seq_length = 256

    def __init__(self):
        self.tokenizer = FakeTokenizer()

    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=False):
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append([
                float("mitosis" in lowered or "cells" in lowered),
                float("photosynthesis" in lowered or "chlorophyll" in lowered),
                float("algebra" in lowered or "equation" in lowered),
            ])
        return np.asarray(vectors, dtype="float32")


class FakeIndex:
    def __init__(self, dimensions):
        self.dimensions = dimensions
        self.vectors = np.empty((0, dimensions), dtype="float32")

    def add(self, vectors):
        self.vectors = np.vstack([self.vectors, vectors])

    def search(self, query, top_k):
        scores = query @ self.vectors.T
        order = np.argsort(-scores[0])[:top_k]
        return scores[:, order], order.reshape(1, -1).astype("int64")


@pytest.fixture(autouse=True)
def fake_rag_dependencies(monkeypatch):
    rag.clear_session_indexes()
    monkeypatch.setattr(rag, "_embedding_model", FakeEmbeddingModel())
    monkeypatch.setattr(rag, "_create_faiss_index", lambda dimensions: FakeIndex(dimensions))
    yield
    rag.clear_session_indexes()


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


def test_chunk_text_uses_512_tokens_with_overlap():
    text = " ".join(f"token{i}" for i in range(1100))

    chunks = rag.chunk_text(text)

    tokenizer = rag.get_embedding_model().tokenizer
    chunk_tokens = [tokenizer.encode(chunk, add_special_tokens=False) for chunk in chunks]
    assert [len(tokens) for tokens in chunk_tokens] == [512, 512, 204]
    assert chunk_tokens[0][448:512] == chunk_tokens[1][:64]
    assert chunk_tokens[1][448:512] == chunk_tokens[2][:64]


def test_embedding_includes_tokens_beyond_model_window():
    text = " ".join(["filler"] * 300 + ["mitosis", "cells"])

    embedding = rag._embed([text])

    assert embedding[0][0] > 0


def test_retrieval_returns_relevant_chunks_and_latency(client):
    ingest_response = client.post(
        "/rag/ingest",
        json={
            "session_id": "biology",
            "source_id": "bio-notes",
            "text": "Mitosis divides cells. Photosynthesis uses chlorophyll.",
        },
    )

    assert ingest_response.status_code == 201

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

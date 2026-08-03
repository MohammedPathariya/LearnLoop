import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.embeddings import HttpEmbeddingProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_http_provider_indexes_documents_and_embeds_queries(monkeypatch):
    calls = []
    document = {
        "chunks": [{
            "chunk_index": 0,
            "text": "Mitosis divides cells.",
            "token_count": 4,
            "embedding": [0.0] * 384,
        }]
    }

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(document if url.endswith("/index") else {"embeddings": [[1.0] * 384]})

    monkeypatch.setattr("httpx.post", fake_post)
    provider = HttpEmbeddingProvider("https://embeddings.example", "secret")

    chunks = provider.index_document("Mitosis divides cells.")
    query = provider.embed_query("How do cells divide?")

    assert chunks[0]["chunk_index"] == 0
    assert query.shape == (384,)
    assert calls[0][0] == "https://embeddings.example/index"
    assert calls[0][1]["headers"] == {"Authorization": "Bearer secret"}
    assert calls[1][0] == "https://embeddings.example/embed"


def test_http_provider_rejects_wrong_embedding_dimension(monkeypatch):
    monkeypatch.setattr(
        "httpx.post",
        lambda *_args, **_kwargs: FakeResponse({"embeddings": [[1.0, 2.0]]}),
    )
    provider = HttpEmbeddingProvider("https://embeddings.example")

    try:
        provider.embed_query("query")
    except RuntimeError as exc:
        assert "384-dimensional" in str(exc)
    else:
        raise AssertionError("invalid embedding dimension was accepted")

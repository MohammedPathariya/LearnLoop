import os
import time
from typing import Protocol

import httpx
import numpy as np


class EmbeddingProvider(Protocol):
    def index_document(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> list[dict]: ...

    def embed_query(self, text: str) -> np.ndarray: ...


class HttpEmbeddingProvider:
    def __init__(self, url: str, token: str = "", timeout: float = 120.0):
        self.url = url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def index_document(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> list[dict]:
        payload = self._post(
            "/index",
            {
                "text": text,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            },
        )
        chunks = payload.get("chunks") if isinstance(payload, dict) else None
        if not isinstance(chunks, list) or not chunks:
            raise RuntimeError("Embedding service returned no document chunks")
        for index, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                raise RuntimeError("Embedding service returned an invalid chunk")
            if chunk.get("chunk_index") != index:
                raise RuntimeError("Embedding service returned non-contiguous chunk indexes")
            embedding = chunk.get("embedding")
            if not isinstance(embedding, list) or len(embedding) != 384:
                raise RuntimeError("Embedding service returned a non-384-dimensional vector")
        return chunks

    def embed_query(self, text: str) -> np.ndarray:
        payload = self._post("/embed", {"texts": [text]})
        embeddings = payload.get("embeddings") if isinstance(payload, dict) else None
        if not isinstance(embeddings, list) or len(embeddings) != 1:
            raise RuntimeError("Embedding service returned an invalid query payload")
        if not isinstance(embeddings[0], list) or len(embeddings[0]) != 384:
            raise RuntimeError("Embedding service returned a non-384-dimensional query vector")
        return np.asarray(embeddings[0], dtype="float32")

    def _post(self, path: str, payload: dict) -> dict:
        if not self.url:
            raise RuntimeError("EMBEDDING_SERVICE_URL is required")
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        for attempt in range(3):
            try:
                response = httpx.post(
                    f"{self.url}{path}",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response.status_code >= 500 and attempt < 2:
                    time.sleep(0.25 * (attempt + 1))
                    continue
                response.raise_for_status()
                break
            except (httpx.ConnectError, httpx.ReadTimeout) as exc:
                if attempt == 2:
                    raise RuntimeError(f"Embedding service request failed: {exc}") from exc
                time.sleep(0.25 * (attempt + 1))
            except httpx.HTTPError as exc:
                raise RuntimeError(f"Embedding service request failed: {exc}") from exc
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("Embedding service returned an invalid JSON object")
        return body


def build_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "http").strip().lower()
    if provider != "http":
        raise RuntimeError(
            "Only EMBEDDING_PROVIDER=http is supported. Configure Modal for embeddings."
        )
    return HttpEmbeddingProvider(
        os.getenv("EMBEDDING_SERVICE_URL", ""),
        os.getenv("EMBEDDING_SERVICE_TOKEN", ""),
        float(os.getenv("EMBEDDING_SERVICE_TIMEOUT_SECONDS", "120")),
    )

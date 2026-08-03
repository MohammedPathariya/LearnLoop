import os
from typing import Protocol

import httpx
import numpy as np

from . import rag


class EmbeddingProvider(Protocol):
    @property
    def tokenizer(self): ...

    def embed(self, texts: list[str]) -> np.ndarray: ...


class LocalMiniLMProvider:
    @property
    def tokenizer(self):
        return rag.get_embedding_model().tokenizer

    def embed(self, texts: list[str]) -> np.ndarray:
        return rag._embed_local(texts)


class HttpEmbeddingProvider:
    def __init__(self, url: str, token: str = "", timeout: float = 60.0):
        self.url = url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._tokenizer = None

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            try:
                from transformers import AutoTokenizer
            except ImportError as exc:
                raise RuntimeError(
                    "transformers is required for remote embedding tokenization"
                ) from exc
            self._tokenizer = AutoTokenizer.from_pretrained(rag.EMBEDDING_MODEL_NAME)
        return self._tokenizer

    def embed(self, texts: list[str]) -> np.ndarray:
        if not self.url:
            raise RuntimeError("EMBEDDING_SERVICE_URL is required for HTTP embeddings")
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            response = httpx.post(
                f"{self.url}/embed",
                json={"texts": texts},
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Embedding service request failed: {exc}") from exc

        payload = response.json()
        embeddings = payload.get("embeddings") if isinstance(payload, dict) else None
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise RuntimeError("Embedding service returned an invalid embeddings payload")
        return np.asarray(embeddings, dtype="float32")


def build_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()
    if provider == "http":
        return HttpEmbeddingProvider(
            os.getenv("EMBEDDING_SERVICE_URL", ""),
            os.getenv("EMBEDDING_SERVICE_TOKEN", ""),
            float(os.getenv("EMBEDDING_SERVICE_TIMEOUT_SECONDS", "60")),
        )
    if provider != "local":
        raise RuntimeError(f"Unsupported EMBEDDING_PROVIDER: {provider}")
    return LocalMiniLMProvider()

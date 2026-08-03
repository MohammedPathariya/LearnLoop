import os
from dataclasses import dataclass

import numpy as np
from flask import has_app_context
from sqlalchemy import text

from ..extensions import db


@dataclass(frozen=True)
class StoredChunk:
    id: str
    session_id: str
    source_id: str
    chunk_index: int
    text: str
    token_count: int
    score: float | None = None


class MemoryVectorStore:
    """Small deterministic store used by tests and explicit local fixtures."""

    def __init__(self):
        self._chunks: dict[str, list[tuple[StoredChunk, np.ndarray]]] = {}

    def upsert(self, session_id: str, source_id: str, chunks: list[dict]) -> dict:
        session_chunks = self._chunks.setdefault(session_id, [])
        session_chunks[:] = [item for item in session_chunks if item[0].source_id != source_id]
        for item in chunks:
            stored = StoredChunk(
                id=f"{source_id}:{item['chunk_index']}",
                session_id=session_id,
                source_id=source_id,
                chunk_index=item["chunk_index"],
                text=item["text"],
                token_count=item["token_count"],
            )
            session_chunks.append((stored, np.asarray(item["embedding"], dtype="float32")))
        return {
            "session_id": session_id,
            "source_id": source_id,
            "chunks_indexed": len(chunks),
            "total_chunks": len(session_chunks),
        }

    def search(self, session_id: str, embedding: np.ndarray, top_k: int) -> list[dict]:
        candidates = self._chunks.get(session_id, [])
        if not candidates:
            return []
        query = _normalize(embedding.reshape(1, -1))[0]
        scored = [
            (float(np.dot(query, _normalize(vector.reshape(1, -1))[0])), chunk)
            for chunk, vector in candidates
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [_serialize_chunk(chunk, score) for score, chunk in scored[:top_k]]

    def delete_source(self, source_id: str):
        for session_chunks in self._chunks.values():
            session_chunks[:] = [item for item in session_chunks if item[0].source_id != source_id]

    def delete_session(self, session_id: str):
        self._chunks.pop(session_id, None)

    def has_session(self, session_id: str) -> bool:
        return bool(self._chunks.get(session_id))

    def clear(self):
        self._chunks.clear()


class PgVectorStore:
    def upsert(self, session_id: str, source_id: str, chunks: list[dict]) -> dict:
        db.session.execute(
            text("DELETE FROM study_chunk WHERE session_id = :session_id AND source_id = :source_id"),
            {"session_id": session_id, "source_id": source_id},
        )
        for item in chunks:
            db.session.execute(
                text(
                    "INSERT INTO study_chunk "
                    "(id, session_id, source_id, chunk_index, text, token_count, embedding) "
                    "VALUES (:id, :session_id, :source_id, :chunk_index, :text, :token_count, "
                    "CAST(:embedding AS vector))"
                ),
                {
                    "id": f"{source_id}:{item['chunk_index']}",
                    "session_id": session_id,
                    "source_id": source_id,
                    "chunk_index": item["chunk_index"],
                    "text": item["text"],
                    "token_count": item["token_count"],
                    "embedding": _vector_literal(item["embedding"]),
                },
            )
        db.session.flush()
        total = db.session.execute(
            text("SELECT count(*) FROM study_chunk WHERE session_id = :session_id"),
            {"session_id": session_id},
        ).scalar_one()
        return {
            "session_id": session_id,
            "source_id": source_id,
            "chunks_indexed": len(chunks),
            "total_chunks": total,
        }

    def search(self, session_id: str, embedding: np.ndarray, top_k: int) -> list[dict]:
        rows = db.session.execute(
            text(
                "SELECT id, session_id, source_id, chunk_index, text, token_count, "
                "1 - (embedding <=> CAST(:embedding AS vector)) AS score "
                "FROM study_chunk WHERE session_id = :session_id "
                "ORDER BY embedding <=> CAST(:embedding AS vector) LIMIT :top_k"
            ),
            {
                "embedding": _vector_literal(embedding),
                "session_id": session_id,
                "top_k": top_k,
            },
        ).mappings()
        return [dict(row) for row in rows]

    def delete_source(self, source_id: str):
        db.session.execute(
            text("DELETE FROM study_chunk WHERE source_id = :source_id"),
            {"source_id": source_id},
        )

    def delete_session(self, session_id: str):
        db.session.execute(
            text("DELETE FROM study_chunk WHERE session_id = :session_id"),
            {"session_id": session_id},
        )

    def has_session(self, session_id: str) -> bool:
        return bool(db.session.execute(
            text("SELECT 1 FROM study_chunk WHERE session_id = :session_id LIMIT 1"),
            {"session_id": session_id},
        ).scalar())

    def clear(self):
        db.session.execute(text("DELETE FROM study_chunk"))


_memory_store = MemoryVectorStore()


def get_vector_store():
    configured = os.getenv("VECTOR_STORE", "").strip().lower()
    if configured == "memory":
        return _memory_store
    if configured == "pgvector":
        return PgVectorStore()
    if not has_app_context():
        return _memory_store
    if db.engine.dialect.name == "postgresql":
        return PgVectorStore()
    return _memory_store


def _serialize_chunk(chunk: StoredChunk, score: float) -> dict:
    return {
        "id": chunk.id,
        "session_id": chunk.session_id,
        "source_id": chunk.source_id,
        "chunk_index": chunk.chunk_index,
        "text": chunk.text,
        "token_count": chunk.token_count,
        "score": score,
    }


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _vector_literal(vector) -> str:
    values = np.asarray(vector, dtype="float32").reshape(-1)
    return "[" + ",".join(format(float(value), ".9g") for value in values) + "]"

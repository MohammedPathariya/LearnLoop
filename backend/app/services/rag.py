import time

from .embeddings import build_embedding_provider
from .vector_store import get_vector_store


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

_embedding_provider = None


def ingest_study_material(session_id: str, text: str, source_id: str | None = None) -> dict:
    clean_session_id = session_id.strip()
    clean_text = text.strip()
    if not clean_session_id:
        raise ValueError("session_id is required")
    if not clean_text:
        raise ValueError("text is required")

    source = source_id.strip() if source_id and source_id.strip() else clean_session_id
    chunks = get_embedding_provider().index_document(clean_text)
    normalized_chunks = []
    for index, chunk in enumerate(chunks):
        chunk_text = str(chunk.get("text", "")).strip()
        if not chunk_text:
            raise RuntimeError("Embedding service returned an empty chunk")
        normalized_chunks.append({
            "chunk_index": index,
            "text": chunk_text,
            "token_count": int(chunk.get("token_count", 0)),
            "embedding": chunk["embedding"],
        })

    return get_vector_store().upsert(clean_session_id, source, normalized_chunks)


def retrieve_chunks(session_id: str, query: str, top_k: int = 5) -> dict:
    clean_session_id = session_id.strip()
    clean_query = query.strip()
    if not clean_session_id:
        raise ValueError("session_id is required")
    if not clean_query:
        raise ValueError("query is required")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    started = time.perf_counter()
    query_embedding = get_embedding_provider().embed_query(clean_query)
    chunks = get_vector_store().search(clean_session_id, query_embedding, top_k)
    return {"chunks": chunks, "latency_ms": _elapsed_ms(started)}


def clear_session_indexes():
    get_vector_store().clear()


def clear_session_index(session_id: str):
    get_vector_store().delete_session(session_id)


def has_session_index(session_id: str) -> bool:
    return False


def get_session_chunks(session_id: str) -> list[dict]:
    return []


def get_embedding_provider():
    global _embedding_provider
    if _embedding_provider is None:
        _embedding_provider = build_embedding_provider()
    return _embedding_provider


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)

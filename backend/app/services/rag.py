import time
import uuid
from dataclasses import dataclass

import numpy as np

from .embeddings import build_embedding_provider


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_TOKENS = 512
CHUNK_OVERLAP = 64


@dataclass(frozen=True)
class Chunk:
    id: str
    session_id: str
    source_id: str
    chunk_index: int
    text: str
    token_count: int


@dataclass
class SessionIndex:
    index: object
    chunks: list[Chunk]


_embedding_model = None
_embedding_provider = None
_session_indexes: dict[str, SessionIndex] = {}


def chunk_text(text: str, chunk_tokens: int = CHUNK_TOKENS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if chunk_tokens <= 0:
        raise ValueError("chunk_tokens must be greater than 0")
    if overlap < 0 or overlap >= chunk_tokens:
        raise ValueError("overlap must be non-negative and smaller than chunk_tokens")

    tokenizer = get_embedding_tokenizer()
    tokens = _encode_content_tokens(tokenizer, text)
    if not tokens:
        return []

    chunks = []
    step = chunk_tokens - overlap
    for start in range(0, len(tokens), step):
        chunk = tokens[start:start + chunk_tokens]
        chunks.append(tokenizer.decode(chunk, skip_special_tokens=True))
        if start + chunk_tokens >= len(tokens):
            break
    return chunks


def ingest_study_material(session_id: str, text: str, source_id: str | None = None) -> dict:
    clean_session_id = session_id.strip()
    clean_text = text.strip()
    if not clean_session_id:
        raise ValueError("session_id is required")
    if not clean_text:
        raise ValueError("text is required")

    source = source_id.strip() if source_id and source_id.strip() else str(uuid.uuid4())
    chunk_texts = chunk_text(clean_text)
    chunks = [
        Chunk(
            id=f"{source}:{index}",
            session_id=clean_session_id,
            source_id=source,
            chunk_index=index,
            text=chunk,
            token_count=len(_encode_content_tokens(get_embedding_tokenizer(), chunk)),
        )
        for index, chunk in enumerate(chunk_texts)
    ]

    if not chunks:
        raise ValueError("text did not produce any chunks")

    embeddings = _normalize(np.asarray(_embed([chunk.text for chunk in chunks]), dtype="float32"))
    session_index = _session_indexes.get(clean_session_id)

    if session_index is None:
        session_index = SessionIndex(index=_create_faiss_index(embeddings.shape[1]), chunks=[])
        _session_indexes[clean_session_id] = session_index

    session_index.index.add(embeddings)
    session_index.chunks.extend(chunks)

    return {
        "session_id": clean_session_id,
        "source_id": source,
        "chunks_indexed": len(chunks),
        "total_chunks": len(session_index.chunks),
    }


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
    session_index = _session_indexes.get(clean_session_id)
    if session_index is None:
        return {"chunks": [], "latency_ms": _elapsed_ms(started)}

    query_embedding = _normalize(np.asarray(_embed([clean_query]), dtype="float32"))
    limit = min(top_k, len(session_index.chunks))
    scores, indexes = session_index.index.search(query_embedding, limit)

    chunks = []
    for score, chunk_pos in zip(scores[0], indexes[0]):
        if chunk_pos < 0:
            continue
        chunk = session_index.chunks[int(chunk_pos)]
        chunks.append({
            "id": chunk.id,
            "session_id": chunk.session_id,
            "source_id": chunk.source_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "token_count": chunk.token_count,
            "score": float(score),
        })

    return {"chunks": chunks, "latency_ms": _elapsed_ms(started)}


def clear_session_indexes():
    _session_indexes.clear()


def clear_session_index(session_id: str):
    _session_indexes.pop(session_id, None)


def has_session_index(session_id: str) -> bool:
    return session_id in _session_indexes


def get_session_chunks(session_id: str) -> list[dict]:
    session_index = _session_indexes.get(session_id)
    if session_index is None:
        return []
    return [
        {
            "id": chunk.id,
            "session_id": chunk.session_id,
            "source_id": chunk.source_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "token_count": chunk.token_count,
        }
        for chunk in session_index.chunks
    ]


def _create_faiss_index(dimensions: int):
    try:
        import faiss
    except ImportError as exc:
        raise RuntimeError("FAISS is not installed. Run: python3.11 -m pip install -r backend/requirements.txt") from exc

    return faiss.IndexFlatIP(dimensions)


def _embed(texts: list[str]):
    return get_embedding_provider().embed(texts)


def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Run: python3.11 -m pip install -r backend/requirements.txt"
            ) from exc
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def get_embedding_provider():
    global _embedding_provider

    if _embedding_provider is None:
        _embedding_provider = build_embedding_provider()
    return _embedding_provider


def get_embedding_tokenizer():
    return get_embedding_provider().tokenizer


def _embed_local(texts: list[str]):
    tokenizer = get_embedding_model().tokenizer
    window_tokens = get_embedding_model().max_seq_length - tokenizer.num_special_tokens_to_add(pair=False)
    if window_tokens <= 0:
        raise RuntimeError("Embedding model has no usable content-token capacity")

    window_texts = []
    window_owners = []
    window_weights = []
    for owner, text in enumerate(texts):
        token_ids = _encode_content_tokens(tokenizer, text)
        for start in range(0, len(token_ids), window_tokens):
            window = token_ids[start:start + window_tokens]
            window_texts.append(tokenizer.decode(window, skip_special_tokens=True))
            window_owners.append(owner)
            window_weights.append(len(window))

    window_embeddings = np.asarray(
        get_embedding_model().encode(window_texts, convert_to_numpy=True, normalize_embeddings=False),
        dtype="float32",
    )
    embeddings = np.zeros((len(texts), window_embeddings.shape[1]), dtype="float32")
    weights = np.zeros(len(texts), dtype="float32")
    for embedding, owner, weight in zip(window_embeddings, window_owners, window_weights):
        embeddings[owner] += embedding * weight
        weights[owner] += weight

    return embeddings / weights[:, None]


def _encode_content_tokens(tokenizer, text: str) -> list[int]:
    return tokenizer.encode(text, add_special_tokens=False, verbose=False)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)

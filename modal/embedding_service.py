import os

import modal
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


APP_NAME = "learnloop-embeddings"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_TOKENS = 512
CHUNK_OVERLAP = 64
EMBEDDING_DIMENSIONS = 384

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi[standard]", "sentence-transformers==3.0.1")
)
app = modal.App(APP_NAME)
auth_scheme = HTTPBearer()
_model = None
_tokenizer = None


def _content_tokens(tokenizer, text: str) -> list[int]:
    return tokenizer.encode(text, add_special_tokens=False, verbose=False)


def chunk_document(tokenizer, text: str) -> list[dict]:
    tokens = _content_tokens(tokenizer, text)
    if not tokens:
        return []
    step = CHUNK_TOKENS - CHUNK_OVERLAP
    chunks = []
    for start in range(0, len(tokens), step):
        token_window = tokens[start:start + CHUNK_TOKENS]
        chunks.append({
            "chunk_index": len(chunks),
            "text": tokenizer.decode(token_window, skip_special_tokens=True),
            "token_count": len(token_window),
        })
        if start + CHUNK_TOKENS >= len(tokens):
            break
    return chunks


def embed_long_texts(model, tokenizer, texts: list[str]) -> list[list[float]]:
    window_tokens = model.max_seq_length - tokenizer.num_special_tokens_to_add(pair=False)
    if window_tokens <= 0:
        raise RuntimeError("Embedding model has no usable content-token capacity")
    window_texts = []
    owners = []
    weights = []
    for owner, text in enumerate(texts):
        tokens = _content_tokens(tokenizer, text)
        for start in range(0, len(tokens), window_tokens):
            window = tokens[start:start + window_tokens]
            window_texts.append(tokenizer.decode(window, skip_special_tokens=True))
            owners.append(owner)
            weights.append(len(window))

    if not window_texts:
        return []
    encoded = model.encode(
        window_texts,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )
    vectors = [[0.0] * encoded.shape[1] for _ in texts]
    total_weights = [0.0] * len(texts)
    for vector, owner, weight in zip(encoded, owners, weights):
        for dimension, value in enumerate(vector):
            vectors[owner][dimension] += float(value) * weight
        total_weights[owner] += weight

    for vector, weight in zip(vectors, total_weights):
        if weight == 0:
            continue
        for index in range(len(vector)):
            vector[index] /= weight
        norm = sum(value * value for value in vector) ** 0.5
        if norm:
            for index in range(len(vector)):
                vector[index] /= norm
    return vectors


@app.function(
    image=image,
    scaledown_window=300,
    secrets=[modal.Secret.from_name("learnloop-embedding")],
)
@modal.fastapi_endpoint(method="POST")
def index(
    item: dict,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    _require_token(token)
    text = item.get("text", "").strip()
    if not text:
        return {"error": "text is required"}
    model, tokenizer = _load_model()
    chunks = chunk_document(tokenizer, text)
    embeddings = embed_long_texts(model, tokenizer, [chunk["text"] for chunk in chunks])
    return {"chunks": [{**chunk, "embedding": embedding} for chunk, embedding in zip(chunks, embeddings)]}


@app.function(
    image=image,
    scaledown_window=300,
    secrets=[modal.Secret.from_name("learnloop-embedding")],
)
@modal.fastapi_endpoint(method="POST")
def embed(
    item: dict,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    _require_token(token)
    texts = item.get("texts")
    if not isinstance(texts, list) or not texts or not all(isinstance(text, str) for text in texts):
        return {"error": "texts must be a non-empty list of strings"}
    model, tokenizer = _load_model()
    return {"embeddings": embed_long_texts(model, tokenizer, texts)}


def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    from sentence_transformers import SentenceTransformer

    _model = SentenceTransformer(MODEL_NAME)
    _tokenizer = _model.tokenizer
    return _model, _tokenizer


def _require_token(token: HTTPAuthorizationCredentials):
    expected = os.environ.get("EMBEDDING_SERVICE_TOKEN", "")
    if not expected or token.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid embedding service token",
        )

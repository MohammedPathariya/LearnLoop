import sys
from pathlib import Path

import pytest
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import rag


def test_real_minilm_and_faiss_retrieval():
    rag.clear_session_indexes()
    try:
        model = SentenceTransformer(rag.EMBEDDING_MODEL_NAME, local_files_only=True)
    except OSError:
        pytest.skip("all-MiniLM-L6-v2 is not available in the local model cache")

    rag._embedding_model = model

    try:
        rag.ingest_study_material(
            session_id="integration-session",
            source_id="biology",
            text="Mitosis is the process by which a cell divides into two daughter cells.",
        )
        rag.ingest_study_material(
            session_id="integration-session",
            source_id="algebra",
            text="Algebra uses symbols to represent numbers in equations.",
        )

        result = rag.retrieve_chunks(
            session_id="integration-session",
            query="How does a cell divide?",
            top_k=1,
        )

        assert result["chunks"][0]["source_id"] == "biology"
        assert result["latency_ms"] >= 0
    finally:
        rag.clear_session_indexes()
        rag._embedding_model = None

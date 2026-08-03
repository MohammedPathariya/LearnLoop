import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import rag


def test_production_provider_is_explicitly_remote(monkeypatch):
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    monkeypatch.delenv("EMBEDDING_SERVICE_URL", raising=False)
    with pytest.raises(RuntimeError, match="EMBEDDING_SERVICE_URL is required"):
        rag.get_embedding_provider().index_document("text")

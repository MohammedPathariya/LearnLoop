import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "docs/benchmarks/real_project_corpus.json"


def test_real_project_benchmark_sources_match_pinned_hashes():
    dataset = json.loads(DATASET_PATH.read_text())

    for document in dataset["documents"]:
        source_bytes = (ROOT / document["path"]).read_bytes()
        assert hashlib.sha256(source_bytes).hexdigest() == document["sha256"]


def test_real_project_reports_and_frontend_data_match():
    dataset_sha256 = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
    frontend_data = json.loads((ROOT / "frontend/src/data/benchmarks.json").read_text())

    for top_k in (3, 5):
        report = json.loads(
            (ROOT / f"docs/benchmarks/real_project_recall_at_{top_k}.json").read_text()
        )
        frontend_result = next(
            item for item in frontend_data["retrieval"] if item["name"].endswith(f"Recall@{top_k}")
        )

        assert report["dataset_sha256"] == dataset_sha256
        assert frontend_result["recall"] == report[f"recall_at_{top_k}"]
        assert frontend_result["hits"] == f"{report[f'hits_at_{top_k}']}/{report['query_count']}"
        assert frontend_result["p50_ms"] == report["p50_latency_ms"]
        assert frontend_result["p95_ms"] == report["p95_latency_ms"]
        assert frontend_result["documents"] == report["document_count"]
        assert frontend_result["chunks"] == report["chunk_count"]

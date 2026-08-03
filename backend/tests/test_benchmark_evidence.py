import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "docs/benchmarks/real_project_corpus.json"
ABLATION_DATASET_PATH = ROOT / "docs/benchmarks/retrieval_ablation_corpus.json"
ABLATION_REPORT_PATH = ROOT / "docs/benchmarks/retrieval_ablation_report.json"
GENERATION_DATASET_PATH = ROOT / "docs/benchmarks/generation_reliability_corpus.json"
GENERATION_REPORT_PATH = ROOT / "docs/benchmarks/generation_reliability_report.json"


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


def test_retrieval_ablation_sources_and_queries_are_pinned():
    dataset = json.loads(ABLATION_DATASET_PATH.read_text())
    source_ids = {document["source_id"] for document in dataset["documents"]}

    assert len(dataset["documents"]) == 4
    assert len(dataset["queries"]) == 10
    for document in dataset["documents"]:
        source_bytes = (ROOT / document["path"]).read_bytes()
        assert hashlib.sha256(source_bytes).hexdigest() == document["sha256"]
    assert all(query["expected_source_id"] in source_ids for query in dataset["queries"])


def test_retrieval_ablation_report_matches_pinned_dataset():
    dataset_sha256 = hashlib.sha256(ABLATION_DATASET_PATH.read_bytes()).hexdigest()
    report = json.loads(ABLATION_REPORT_PATH.read_text())

    assert report["dataset_sha256"] == dataset_sha256
    assert len(report["runs"]) == 6
    assert all(run["status"] == "passed" for run in report["runs"])
    assert all(run["failure_rate"] == 0 for run in report["runs"])


def test_generation_reliability_report_matches_pinned_dataset():
    dataset_sha256 = hashlib.sha256(GENERATION_DATASET_PATH.read_bytes()).hexdigest()
    dataset = json.loads(GENERATION_DATASET_PATH.read_text())
    report = json.loads(GENERATION_REPORT_PATH.read_text())

    assert report["dataset_sha256"] == dataset_sha256
    assert report["case_count"] == len(dataset["cases"]) == 10
    assert report["metrics"]["baseline_first_pass_valid"] == 6
    assert report["metrics"]["robust_final_valid"] == 10
    assert report["metrics"]["final_failures"] == 0

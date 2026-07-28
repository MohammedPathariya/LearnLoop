import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import rag


def percentile(values: list[float], percentile_value: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def run(dataset_path: Path, report_path: Path, benchmark_name: str, top_k: int) -> dict:
    dataset_path = dataset_path.resolve()
    report_path = report_path.resolve()
    dataset_bytes = dataset_path.read_bytes()
    dataset = json.loads(dataset_bytes)
    if isinstance(dataset, dict):
        documents = dataset["documents"]
        evaluation_items = dataset["queries"]
    else:
        documents = dataset
        evaluation_items = [item for item in dataset if item.get("evaluate", True)]
    session_id = "benchmark-retrieval"
    rag.clear_session_indexes()
    started = time.perf_counter()
    try:
        chunk_count = 0
        corpus = []
        for item in documents:
            text = item.get("text")
            if text is None:
                source_path = ROOT / item["path"]
                source_bytes = source_path.read_bytes()
                source_sha256 = hashlib.sha256(source_bytes).hexdigest()
                expected_sha256 = item.get("sha256")
                if expected_sha256 is None:
                    raise ValueError(f"Missing sha256 for benchmark source: {item['path']}")
                if source_sha256 != expected_sha256:
                    raise ValueError(
                        f"Benchmark source changed: {item['path']} "
                        f"(expected {expected_sha256}, found {source_sha256})"
                    )
                text = source_bytes.decode()
                corpus.append({
                    "source_id": item["source_id"],
                    "path": item["path"],
                    "sha256": source_sha256,
                })
            else:
                corpus.append({
                    "source_id": item["source_id"],
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                })
            ingest_result = rag.ingest_study_material(
                session_id=session_id,
                source_id=item["source_id"],
                text=text,
            )
            chunk_count += ingest_result["chunks_indexed"]

        results = []
        latencies = []
        for item in evaluation_items:
            result = rag.retrieve_chunks(session_id, item["question"], top_k=top_k)
            retrieved_ids = [chunk["id"] for chunk in result["chunks"]]
            latency_ms = result["latency_ms"]
            latencies.append(latency_ms)
            results.append({
                "id": item["id"],
                "expected_chunk_id": item["expected_chunk_id"],
                "retrieved_chunk_ids": retrieved_ids,
                f"hit_at_{top_k}": item["expected_chunk_id"] in retrieved_ids,
                "latency_ms": latency_ms,
            })

        hits = sum(result[f"hit_at_{top_k}"] for result in results)
        report = {
            "benchmark": benchmark_name,
            "model": rag.EMBEDDING_MODEL_NAME,
            "dataset": str(dataset_path.relative_to(ROOT)),
            "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
            "document_count": len(documents),
            "chunk_count": chunk_count,
            "corpus": corpus,
            "query_count": len(evaluation_items),
            "top_k": top_k,
            f"recall_at_{top_k}": hits / len(evaluation_items),
            f"hits_at_{top_k}": hits,
            "p50_latency_ms": round(percentile(latencies, 50), 3),
            "p95_latency_ms": round(percentile(latencies, 95), 4),
            "latency_definition": "retrieval_chunks query embedding plus FAISS search, excluding ingestion",
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "numpy": _version("numpy"),
                "faiss": _version("faiss"),
                "sentence_transformers": _version("sentence_transformers"),
            },
            "command": f"HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=backend python3.11 scripts/evaluate_retrieval.py --dataset {_display_path(dataset_path)} --report {_display_path(report_path)} --benchmark-name '{benchmark_name}' --top-k {top_k}",
            "queries": results,
            "elapsed_seconds": time.perf_counter() - started,
        }
    finally:
        rag.clear_session_indexes()

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def _version(module_name: str) -> str:
    module = __import__(module_name)
    return getattr(module, "__version__", "unknown")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure LearnLoop retrieval Recall@5 and latency.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "docs/benchmarks/real_project_corpus.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/benchmarks/real_project_recall_at_5.json")
    parser.add_argument("--benchmark-name", default="LearnLoop real project corpus Recall@5")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    report = run(args.dataset, args.report, args.benchmark_name, args.top_k)
    print(json.dumps({
        f"recall_at_{args.top_k}": report[f"recall_at_{args.top_k}"],
        "top_k": report["top_k"],
        "p50_latency_ms": report["p50_latency_ms"],
        "p95_latency_ms": report["p95_latency_ms"],
        "report": str(args.report),
    }, indent=2))


if __name__ == "__main__":
    main()

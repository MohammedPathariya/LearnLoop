import argparse
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
    dataset = json.loads(dataset_path.read_text())
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
        for item in documents:
            text = item.get("text")
            if text is None:
                text = (ROOT / item["path"]).read_text()
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
            "document_count": len(documents),
            "chunk_count": chunk_count,
            "corpus": [
                {key: item[key] for key in ("source_id", "path") if key in item}
                for item in documents
            ],
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

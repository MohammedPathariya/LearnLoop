"""Run chunking and top-k retrieval ablations against the configured stack."""

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import create_app
from app.services.embeddings import build_embedding_provider
from app.services.vector_store import get_vector_store


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 4)


def parse_configs(value: str) -> list[dict[str, int]]:
    configs = []
    for raw_config in value.split(","):
        parts = raw_config.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid chunk config {raw_config!r}; use SIZE:OVERLAP")
        size, overlap = (int(part) for part in parts)
        if size <= 0 or overlap < 0 or overlap >= size:
            raise ValueError(f"Invalid chunk config {raw_config!r}")
        configs.append({"chunk_size": size, "chunk_overlap": overlap})
    if not configs:
        raise ValueError("At least one chunk configuration is required")
    return configs


def load_dataset(dataset_path: Path) -> tuple[dict, bytes]:
    dataset_path = dataset_path.resolve()
    dataset_bytes = dataset_path.read_bytes()
    dataset = json.loads(dataset_bytes)
    for document in dataset["documents"]:
        source_path = ROOT / document["path"]
        actual_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual_sha256 != document["sha256"]:
            raise ValueError(
                f"Benchmark source changed: {document['path']} "
                f"(expected {document['sha256']}, found {actual_sha256})"
            )
    return dataset, dataset_bytes


def run(dataset_path: Path, report_path: Path, configs: list[dict[str, int]], top_ks: list[int]) -> dict:
    _require_hosted_configuration()
    dataset, dataset_bytes = load_dataset(dataset_path)
    app = create_app()
    provider = build_embedding_provider()
    runs = []
    started = time.perf_counter()

    with app.app_context():
        for config in configs:
            session_id = f"retrieval-ablation-{config['chunk_size']}-{config['chunk_overlap']}"
            store = get_vector_store()
            store.delete_session(session_id)
            run_started = time.perf_counter()
            errors = []
            chunk_count = 0
            try:
                for document in dataset["documents"]:
                    source_text = (ROOT / document["path"]).read_text()
                    chunks = provider.index_document(
                        source_text,
                        config["chunk_size"],
                        config["chunk_overlap"],
                    )
                    normalized_chunks = [
                        {
                            "chunk_index": index,
                            "text": str(chunk["text"]).strip(),
                            "token_count": int(chunk.get("token_count", 0)),
                            "embedding": chunk["embedding"],
                        }
                        for index, chunk in enumerate(chunks)
                    ]
                    result = store.upsert(session_id, document["source_id"], normalized_chunks)
                    chunk_count += result["chunks_indexed"]
            except Exception as exc:
                errors.append({"phase": "ingestion", "error": f"{type(exc).__name__}: {exc}"})

            for top_k in top_ks:
                query_results = []
                latencies = []
                failures = 0
                if errors:
                    failures = len(dataset["queries"])
                else:
                    for query in dataset["queries"]:
                        try:
                            query_started = time.perf_counter()
                            query_embedding = provider.embed_query(query["question"])
                            retrieved_chunks = store.search(session_id, query_embedding, top_k)
                            latency_ms = round((time.perf_counter() - query_started) * 1000, 3)
                            retrieved_sources = [chunk["source_id"] for chunk in retrieved_chunks]
                            hit = query["expected_source_id"] in retrieved_sources
                            latencies.append(latency_ms)
                            query_results.append({
                                "id": query["id"],
                                "expected_source_id": query["expected_source_id"],
                                "retrieved_source_ids": retrieved_sources,
                                "hit": hit,
                                "latency_ms": latency_ms,
                            })
                        except Exception as exc:
                            failures += 1
                            query_results.append({
                                "id": query["id"],
                                "expected_source_id": query["expected_source_id"],
                                "hit": False,
                                "error": f"{type(exc).__name__}: {exc}",
                            })

                query_count = len(dataset["queries"])
                hits = sum(item["hit"] for item in query_results)
                runs.append({
                    **config,
                    "top_k": top_k,
                    "status": "failed" if failures == query_count else "passed",
                    "document_count": len(dataset["documents"]),
                    "chunk_count": chunk_count,
                    "query_count": query_count,
                    "hits": hits,
                    "recall": round(hits / query_count, 4) if query_count else None,
                    "failed_queries": failures,
                    "failure_rate": round(failures / query_count, 4) if query_count else None,
                    "p50_latency_ms": percentile(latencies, 50),
                    "p95_latency_ms": percentile(latencies, 95),
                    "errors": errors,
                    "queries": query_results,
                    "run_elapsed_seconds": round(time.perf_counter() - run_started, 4),
                })
            store.delete_session(session_id)

    report = {
        "benchmark": "LearnLoop retrieval chunking and top-k ablation",
        "dataset": _display_path(dataset_path.resolve()),
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "evaluation_unit": "source-level recall: a query is a hit when any returned chunk belongs to its expected source",
        "latency_definition": "retrieval query embedding plus vector-store search, excluding ingestion",
        "failure_rate_definition": "failed query attempts divided by total queries; ingestion failures fail every query for that configuration",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "http"),
            "vector_store": os.getenv("VECTOR_STORE", "pgvector"),
            "embedding_service_url_configured": bool(os.getenv("EMBEDDING_SERVICE_URL")),
            "database_uri_configured": bool(os.getenv("SUPABASE_DB_URI")),
        },
        "command": "PYTHONPATH=backend python3.11 scripts/evaluate_retrieval_ablation.py --dataset docs/benchmarks/retrieval_ablation_corpus.json --report docs/benchmarks/retrieval_ablation_report.json --chunk-configs 256:32,512:64,768:96 --top-k 3,5",
        "runs": runs,
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }
    report_path = report_path.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def _require_hosted_configuration() -> None:
    missing = []
    if os.getenv("EMBEDDING_PROVIDER", "http").strip().lower() != "http":
        raise RuntimeError("EMBEDDING_PROVIDER must be http for this benchmark")
    for name in ("EMBEDDING_SERVICE_URL", "EMBEDDING_SERVICE_TOKEN", "SUPABASE_DB_URI"):
        if not os.getenv(name):
            missing.append(name)
    if os.getenv("VECTOR_STORE", "pgvector").strip().lower() != "pgvector":
        raise RuntimeError("VECTOR_STORE must be pgvector for this benchmark")
    if missing:
        raise RuntimeError("Missing hosted benchmark configuration: " + ", ".join(missing))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LearnLoop retrieval chunking and top-k ablations.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "docs/benchmarks/retrieval_ablation_corpus.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/benchmarks/retrieval_ablation_report.json")
    parser.add_argument("--chunk-configs", default="256:32,512:64,768:96")
    parser.add_argument("--top-k", default="3,5")
    args = parser.parse_args()
    try:
        report = run(
            args.dataset,
            args.report,
            parse_configs(args.chunk_configs),
            [int(value) for value in args.top_k.split(",")],
        )
    except RuntimeError as exc:
        parser.error(str(exc))
    print(json.dumps({
        "report": _display_path(args.report.resolve()),
        "runs": [
            {
                "chunk_size": run["chunk_size"],
                "chunk_overlap": run["chunk_overlap"],
                "top_k": run["top_k"],
                "status": run["status"],
                "recall": run["recall"],
                "failure_rate": run["failure_rate"],
                "p50_latency_ms": run["p50_latency_ms"],
                "p95_latency_ms": run["p95_latency_ms"],
            }
            for run in report["runs"]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()

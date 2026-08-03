# Retrieval benchmark catalog

The first two exploratory benchmarks are archived under `archive/` and are not part of the active comparison set.

## Active tests

| Test ID | Report | Corpus | Metric | Purpose |
| --- | --- | --- | --- | --- |
| `synthetic-near-neighbor-recall-at-3` | `synthetic_near_neighbor_recall_at_3.json` | 25 synthetic chunks with near-neighbor distractors | Recall@3 | Controlled hard-negative baseline |
| `real-project-recall-at-3` | `real_project_recall_at_3.json` | 7 checked-in implementation and project files, 27 chunks | Recall@3 | Real-corpus precision baseline |
| `real-project-recall-at-5` | `real_project_recall_at_5.json` | Same corpus and labels as the Recall@3 test | Recall@5 | Recall improvement from a wider result set |

The real-project dataset pins every source file by SHA-256. The evaluator stops
if a source changes before the dataset and reports are deliberately refreshed.
Each report contains the dataset hash, exact command, environment, corpus
hashes, query labels, retrieved chunk IDs, and latency samples.

## Current measured results

| Test ID | Result | p50 | p95 |
| --- | --- | --- | --- |
| `synthetic-near-neighbor-recall-at-3` | 1.0, 13/13 | 6.654 ms | 8.1752 ms |
| `real-project-recall-at-3` | 0.6, 6/10 | 15.433 ms | 30.8652 ms |
| `real-project-recall-at-5` | 0.9, 9/10 | 15.826 ms | 33.8765 ms |

Latency covers query embedding plus FAISS search and excludes ingestion.

## Retrieval ablation study

`retrieval_ablation_corpus.json` is a separate pinned corpus for evaluating the
current hosted design. It varies chunk size and overlap across `256:32`,
`512:64`, and `768:96`, and evaluates both Recall@3 and Recall@5. A query is a
source-level hit when at least one returned chunk belongs to its expected
source. This keeps the comparison valid when changing chunk boundaries.

Deploy the current `modal/embedding_service.py` before running this study;
older Modal deployments accept the default 512/64 behavior but cannot evaluate
the alternate chunk configurations.

Run it only with the current HTTP embedding provider and pgvector store:

```bash
EMBEDDING_PROVIDER=http \
VECTOR_STORE=pgvector \
EMBEDDING_SERVICE_URL=https://<modal-endpoint>.modal.run \
EMBEDDING_SERVICE_TOKEN=<token> \
SUPABASE_DB_URI=<supabase-postgres-uri> \
PYTHONPATH=backend python3.11 scripts/evaluate_retrieval_ablation.py \
  --dataset docs/benchmarks/retrieval_ablation_corpus.json \
  --report docs/benchmarks/retrieval_ablation_report.json \
  --chunk-configs 256:32,512:64,768:96 \
  --top-k 3,5
```

The report records each configuration's chunk count, Recall@3, Recall@5,
failed-query rate, p50 and p95 retrieval latency, ingestion errors, per-query
results, dataset hash, environment flags, and the exact command. Latency is
query embedding plus pgvector search and excludes ingestion. Failure rate is
failed query attempts divided by the ten-query set. Do not copy metrics into
the README or resume until the report has `status: passed` for the relevant
configuration and the run is verified against the hosted Modal and pgvector
services.

### Current hosted ablation result

Run completed on 2026-08-03 against the deployed Modal embedding service and
Supabase pgvector. All 60 query attempts completed without failures. Because
latency includes the remote Modal query-embedding request and pgvector search,
these values are not directly comparable to the historical local FAISS report.

| Chunk size | Overlap | Top-k | Chunks | Recall | Failure rate | Median latency |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 256 | 32 | 3 | 36 | 1.0, 10/10 | 0% | 711.89 ms |
| 256 | 32 | 5 | 36 | 1.0, 10/10 | 0% | 617.15 ms |
| 512 | 64 | 3 | 18 | 0.9, 9/10 | 0% | 677.74 ms |
| 512 | 64 | 5 | 18 | 1.0, 10/10 | 0% | 611.83 ms |
| 768 | 96 | 3 | 12 | 0.7, 7/10 | 0% | 608.85 ms |
| 768 | 96 | 5 | 12 | 1.0, 10/10 | 0% | 682.96 ms |

The checked-in report is [`retrieval_ablation_report.json`](retrieval_ablation_report.json).
For this ten-query corpus, Recall@5 reached 1.0 for every chunk configuration;
the smaller 256-token configuration used twice as many stored chunks as the
768-token configuration, while all configurations had zero query failures.

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
| `synthetic-near-neighbor-recall-at-3` | 1.0, 13/13 | 12.89 ms | 543.597 ms |
| `real-project-recall-at-3` | 0.6, 6/10 | 15.433 ms | 30.8652 ms |
| `real-project-recall-at-5` | 0.9, 9/10 | 15.826 ms | 33.8765 ms |

Latency covers query embedding plus FAISS search and excludes ingestion.

# Retrieval benchmark catalog

The first two exploratory benchmarks are archived under `archive/` and are not part of the active comparison set.

## Active tests

| Test ID | Report | Corpus | Metric | Purpose |
| --- | --- | --- | --- | --- |
| `synthetic-near-neighbor-recall-at-3` | `synthetic_near_neighbor_recall_at_3.json` | 25 synthetic chunks with near-neighbor distractors | Recall@3 | Controlled hard-negative baseline |
| `real-project-recall-at-3` | `real_project_recall_at_3.json` | 7 checked-in implementation and project files, 25 chunks | Recall@3 | Real-corpus precision baseline |
| `real-project-recall-at-5` | `real_project_recall_at_5.json` | Same corpus and labels as the Recall@3 test | Recall@5 | Recall improvement from a wider result set |

Each report contains its exact command, environment, corpus, query labels, retrieved chunk IDs, and latency samples.

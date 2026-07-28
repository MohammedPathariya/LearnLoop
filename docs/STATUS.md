# LearnLoop Revamp Status

Last updated: 2026-07-28

## Current State

- Days 1 through 6 are complete locally on `main`.
- Day 7 deployment compatibility and public deployment have not started.
- The backend is a Flask package under `backend/app/`, with `backend/main.py`
  for local development and `backend/wsgi.py` for Gunicorn.
- Persistent learning spaces, materials, grounded conversations, quizzes,
  flashcards, history, and score-based progress are implemented.
- RAG uses tokenizer-based 512-token chunks with 64-token overlap, weighted
  embedding pooling across MiniLM-sized windows, and session-scoped FAISS
  indexes.
- Material text is durable. In-memory indexes rebuild after a backend restart.
- Pydantic validates generated quizzes and flashcards. Invalid model output gets
  at most two repair retries before the API returns a stable HTTP 502 error.
- The frontend uses React 19, Vite, Vitest, Wouter, and custom responsive CSS.
- Primary navigation is Home, Learn, and Progress. History, Benchmarks, System,
  and GitHub are under More.
- Learn presents materials, grounded questions, quizzes, and flashcards as
  connected modes inside one selected learning space.
- The Machine Learning Foundations demo provides a complete browser-isolated
  journey and resets to its canonical seed after 24 hours without saved
  activity or when the visitor chooses reset.
- The interface does not imply authentication. Browser IDs isolate visitor data
  without representing accounts.
- Progress displays saved score trends and topic averages only. Concept mastery
  remains Day 8 scope.
- `backend/conversations.db` is untracked runtime state. Docker Compose persists
  SQLite data in the `learnloop-data` named volume.

## Current Verification

Passed on 2026-07-28:

- `python3.11 -m pytest`: 28 passed
- `npm --prefix frontend test`: 4 passed
- `npm --prefix frontend run build`: production build succeeded
- `npm --prefix frontend audit --omit=dev`: 0 vulnerabilities
- `docker compose config --quiet`
- real MiniLM and FAISS integration test
- pinned benchmark source and frontend-report consistency tests
- all three active retrieval benchmark commands

The active retrieval measurements are:

| Benchmark | Result | p50 | p95 |
| --- | --- | --- | --- |
| Synthetic near-neighbor Recall@3 | 1.0, 13/13 | 12.89 ms | 543.597 ms |
| Real-project Recall@3 | 0.6, 6/10 | 15.433 ms | 30.8652 ms |
| Real-project Recall@5 | 0.9, 9/10 | 15.826 ms | 33.8765 ms |

The real-project benchmark uses seven checked-in files and 27 chunks. Every
source is pinned by SHA-256, and reports include the dataset hash, corpus hashes,
environment, command, per-query results, and latency samples. Latency covers
query embedding plus FAISS search and excludes ingestion.

The fixed Day 5 local Gunicorn load run remains the current load evidence:
128,917 requests, zero failures, 1,078.47 requests per second, aggregate p50
260 ms, and aggregate p95 580 ms with 500 Locust users. The server and load
generator shared one Mac, so this is explicitly local-only evidence.

## Day 6 Frontend Coverage

The frontend behavior suite verifies:

- the simplified primary navigation and More menu
- the new-learning-space form labels
- opening a learning space and switching to its embedded quiz without the
  previous null-session crash
- quiz question-card layout and radio options without redundant letter prefixes

The production dependency tree is audit-clean. The legacy Create React App
toolchain, stale Browserslist warning, Node deprecation warning, and React Router
advisory surface were removed by the Vite, Vitest, and Wouter migration.

## Guardrails

- `scripts/precommit-check.sh` requires `main`, blocks staged `.env` files and
  mutable database files, checks staged whitespace, and runs backend and
  frontend tests.
- `scripts/verify.sh` requires `main`, checks staged and unstaged whitespace,
  runs backend tests, frontend tests, the production build, and a production
  dependency audit.
- `backend/tests/test_benchmark_evidence.py` fails if benchmark source hashes,
  reports, or frontend benchmark data drift apart.

## Phase Progress

| Phase | Focus | Status |
| --- | --- | --- |
| 1 | Backend stabilization | Complete |
| 2 | Real RAG layer | Complete |
| 3 | Benchmark evidence | Complete |
| 4 | Pydantic self-healing generation | Complete |
| 5 | Load testing and WAL validation | Measured locally; deployed rerun pending |
| 6 | Complete frontend redesign | Complete locally |
| 7 | Deployment compatibility and production deployment | Not started |
| 8 | Additional product features | Not started |

## Immediate Next Step

Day 7 should:

- choose the hosted embedding architecture
- configure the frontend and backend for the selected hosts
- deploy the current core app
- verify health, persistence, ingestion, retrieval, grounded generation, and
  frontend-to-backend calls
- rerun load testing against the deployable architecture before making a
  production capacity claim

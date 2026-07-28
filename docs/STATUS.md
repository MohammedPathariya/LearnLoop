# LearnLoop Revamp Status

Last updated: 2026-07-28

## Current State

- Day 2 RAG changes are implemented on `main`.
- Day 1 backend stabilization is implemented.
- Day 2 session-based RAG is implemented in the backend.
- Backend is split into a minimal Flask package under `backend/app/`.
- `backend/main.py` is the local and Docker entry point.
- Frontend is Create React App with React 19 and `react-scripts@5`.
- Frontend production build passes.
- Frontend test suite has been replaced with a baseline app render test and now passes.
- Backend smoke checks pass for import without `OPENAI_API_KEY`, health, read endpoints, selected write validation, and SQLite WAL.
- Backend pytest smoke tests pass for health, read endpoints, validation errors, quiz-result persistence, empty search, no-key import, and SQLite WAL.
- Local guardrail scripts have been added and installed as Git hooks for pre-commit and pre-push verification.
- Study material ingestion exists at `POST /rag/ingest`.
- Retrieval exists at `POST /rag/retrieve` and returns top-k chunks plus retrieval latency.
- Source-grounded answering exists at `POST /rag/answer` using retrieved chunks as source context.
- RAG uses tokenizer-based 512-token chunking with 64-token overlap.
- Chunk embeddings use weighted pooling across MiniLM-sized windows so all 512 chunk tokens contribute.
- RAG uses lazy local `sentence-transformers/all-MiniLM-L6-v2` embeddings and per-session in-memory FAISS `IndexFlatIP` indexes.
- The current local embedding path is not yet deployment-tuned for Render memory, cold-start, or scale-out constraints.
- Retrieval benchmark and Locust load test do not exist yet.
- Git workflow for this revamp is direct commits to `main` with logical multi-commit history.
- Local folder and GitHub remote have been renamed from `LearnLoop-Deployment` to `LearnLoop`.
- Docker Compose maps the backend to `5050:5050`, matching the Flask default and frontend API fallback.

## Baseline Verification

Passed:

- `PYTHONDONTWRITEBYTECODE=1 python3 -c "compile(open('backend/main.py').read(), 'backend/main.py', 'exec')"`
- Flask app import without `OPENAI_API_KEY`
- `GET /healthz`
- `GET /history`
- `GET /analytics/stats`
- `GET /quiz_history`
- `GET /analytics/quiz_stats`
- `GET /flashcards_history`
- `GET /analytics/flashcard_stats`
- temporary SQLite smoke test for `/quiz_results`
- `python3.11 -m pytest` with 7 backend tests passing
- `python3.11 -m pytest` with 12 backend tests passing after Day 2 RAG changes
- `PYTHONPYCACHEPREFIX=/tmp/learnloop-pycache python3.11 -m compileall backend/app backend/tests`
- `npm test -- --watchAll=false`
- `npm run build`
- `bash scripts/precommit-check.sh`
- `bash scripts/verify.sh`
- `bash scripts/install-git-hooks.sh`

Failed:

- None in the latest baseline verification.

Previous failure reason:

- Previous failure was caused by Jest parsing ESM `axios` through the CRA/Jest setup.
- The old test also expected stale "learn react" boilerplate.

Dependency Notes:

- `npm ci` completed successfully.
- `npm audit` reported 61 vulnerabilities, including 3 critical.
- This is likely tied to the old CRA/react-scripts toolchain.
- Backend tests require Python 3.10+; `python3` is 3.9.6 locally, so use `python3.11`.
- `python3.11 -m pip install -r backend/requirements.txt` completed successfully.
- Day 2 adds `faiss-cpu==1.8.0.post1`, `numpy==1.26.4`, and `sentence-transformers==3.0.1`.
- The real embedding model is loaded lazily on first ingestion.
- Unit tests use a deterministic fake embedder, and an integration test exercises real MiniLM embeddings plus FAISS retrieval.

Residual Warnings:

- Frontend Jest reports React Router v7 future-flag warnings.
- Frontend build reports stale Browserslist data and a Node deprecation warning from the current CRA toolchain.

Guardrails:

- `scripts/precommit-check.sh` verifies the current branch is `main`, blocks staged `.env` files and `conversations.db`, checks staged whitespace, runs backend tests, and runs frontend tests.
- `scripts/verify.sh` verifies the current branch is `main`, checks unstaged and staged whitespace, runs backend tests, runs frontend tests, and runs the frontend production build.
- `scripts/install-git-hooks.sh` installs local `pre-commit` and `pre-push` hooks that call those scripts.

## Phase Progress

| Phase | Focus | Status |
| --- | --- | --- |
| 1 | Backend stabilization | Complete |
| 2 | Real RAG layer | Complete |
| 3 | Benchmark evidence | Not started |
| 4 | Pydantic self-healing generation | Not started |
| 5 | Load testing and WAL validation | Not started |
| 6 | Complete frontend redesign | Not started |
| 7 | Deployment compatibility and production deployment | Not started |
| 8 | Additional impressive product features | Not started |

## Day 2 Implementation Notes

- `backend/app/services/rag.py` owns chunking, embedding generation, FAISS index creation, ingestion, retrieval, latency measurement, and session-index clearing for tests.
- In-memory indexes are keyed by `session_id`; retrieval does not search across sessions.
- `backend/app/services/generation.py` now includes grounded answer generation that instructs the model to answer only from retrieved source chunks.
- `backend/tests/test_rag.py` covers 512-token chunking with overlap, full-chunk embedding coverage, relevant retrieval, and session isolation.
- `backend/tests/test_rag_integration.py` covers real MiniLM embedding generation and FAISS retrieval.

## Immediate Next Step

Continue on `main` and start Phase 3:

- add a small retrieval benchmark dataset
- measure Recall@5 and retrieval latency
- save traceable benchmark output under `docs/benchmarks/`
- update README only with measured retrieval results

Before adding Day 8 product features, complete Day 7 deployment compatibility and production deployment:

- decide whether Render runs embeddings locally or calls Modal/another model service
- document Vercel, Render, and Modal environment variables and deployment steps
- deploy the core app and record public URLs
- verify deployed health, ingestion, retrieval, grounded answer generation, and frontend-to-backend calls
- verify load-test claims against the deployable architecture or label them local-only

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
- Retrieval benchmark evidence is saved under `docs/benchmarks/`.
- Quiz and flashcard generation now validates Pydantic schemas and retries malformed or schema-invalid model output up to two times with validation feedback.
- Exhausted generation retries return a stable error object with the last raw output, validation errors, and attempt count; generation routes return HTTP 502 for those failures.
- Locust load test does not exist yet.
- Git workflow for this revamp is direct commits to `main` with logical multi-commit history.
- Local folder and GitHub remote have been renamed from `LearnLoop-Deployment` to `LearnLoop`.
- Docker Compose maps the backend to `5050:5050`, matching the Flask default and frontend API fallback.
- Frontend environment overrides are no longer tracked; `frontend/.env.example` uses the browser-reachable `http://localhost:5050` API URL, and `backend/.env.example` contains placeholders only.

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
- `python3.11 -m pytest` with 16 backend tests passing after Day 4 generation changes
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
| 3 | Benchmark evidence | Complete |
| 4 | Pydantic self-healing generation | Complete |
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

## Day 3 Benchmark Notes

- v1 and v2 are archived under `docs/benchmarks/archive/` as exploratory provenance.
- `scripts/evaluate_retrieval.py` reruns the named tests against the RAG service with configurable `--top-k`.
- `synthetic-near-neighbor-recall-at-3` measured Recall@3 `1.0` (13/13), p50 `6.591 ms`, and p95 `8.5436 ms`.
- `real-project-recall-at-3` uses seven actual checked-in implementation and project files, 25 indexed chunks, and 10 manually labeled questions; it measured Recall@3 `0.6` (6/10), p50 `6.304 ms`, and p95 `9.2693 ms`.
- `real-project-recall-at-5` uses the unchanged real corpus and labels; it measured Recall@5 `0.9` (9/10), p50 `6.146 ms`, and p95 `10.2577 ms`. The remaining miss is the embedding-model query.
- The named tests and stable report paths are cataloged in `docs/benchmarks/README.md` for later frontend use.
- Latency covers query embedding plus FAISS search and excludes ingestion. The report includes each query's result IDs, latency, environment, and command.

## Immediate Next Step

Continue on `main` and start Phase 5:

- Day 4 structured output validation is complete. Continue with Phase 5 load testing and SQLite WAL validation.

## Day 4 Generation Notes

- `backend/app/schemas.py` defines strict quiz question, quiz output, flashcard, and flashcard output schemas.
- `backend/app/services/generation.py` validates JSON before returning it and performs at most two repair retries after the initial model response.
- `backend/tests/test_generation.py` covers valid output, malformed JSON repair, schema-invalid JSON repair, retry exhaustion, answer normalization, and content validation.
- The frontend now consumes the validated API response directly and displays generation errors returned by the backend.
- Local security follow-up: rotate any credentials currently present in `backend/.env`, remove that file from local sharing, and replace the tracked `backend/conversations.db` with a sanitized or untracked database before publishing the repository.

Before adding Day 8 product features, complete Day 7 deployment compatibility and production deployment:

- decide whether Render runs embeddings locally or calls Modal/another model service
- document Vercel, Render, and Modal environment variables and deployment steps
- deploy the core app and record public URLs
- verify deployed health, ingestion, retrieval, grounded answer generation, and frontend-to-backend calls
- verify load-test claims against the deployable architecture or label them local-only

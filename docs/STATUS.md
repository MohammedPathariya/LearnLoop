# LearnLoop Revamp Status

Last updated: 2026-08-03

## Current State

- Days 1 through 7 are complete locally on `main`.
- Day 8 deployment compatibility is implemented locally. Public deployment is
  blocked on authenticated access to the deployment providers.
- The backend is a Flask package under `backend/app/`, with `backend/main.py`
  for local development and `backend/wsgi.py` for Gunicorn.
- Persistent learning spaces, materials, grounded conversations, quizzes,
  flashcards, history, and score-based progress are implemented.
- RAG uses tokenizer-based 512-token chunks with 64-token overlap, weighted
  embedding pooling across MiniLM-sized windows, and session-scoped FAISS
  indexes.
- PDF upload and pasted-text sources are indexed into the active session flow.
  The intended Supabase schema has no durable source table. The legacy
  SQLAlchemy material path still persists pasted material text, so the privacy
  boundary is not yet fully enforced and must be resolved before deployment.
- Pydantic validates generated quizzes and flashcards. Invalid model output gets
  at most two repair retries before the API returns a stable HTTP 502 error.
- The frontend uses React 19, Vite, Vitest, Wouter, and custom responsive CSS.
- Supabase Auth and the account-oriented Postgres schema are configured locally.
- Primary navigation is Home, Learn, and Progress. History, Benchmarks, System,
  and GitHub are under More.
- Home shows live backend availability and warns that the free backend may take
  up to 60 seconds to wake.
- Learn presents materials, grounded questions, quizzes, and flashcards as
  connected modes inside one selected learning space.
- The Machine Learning Foundations demo is available to guests and is hidden
  from authenticated users.
- Supabase email/password authentication, account navigation, confirmed sign-out,
  and user-scoped request tokens are implemented locally.
- Guest mode remains available without an account and is presented as a
  browser-session experience.
- Progress displays saved score trends and topic averages only. Concept mastery
  remains Day 8 scope.
- `backend/conversations.db` is untracked runtime state. Docker Compose persists
  SQLite data in the `learnloop-data` named volume.
- The selected first-host architecture is Vercel, Render, and in-process local
  MiniLM on one Render worker. `EMBEDDING_PROVIDER=http` is available for a
  future Modal or remote embedding service.
- `render.yaml`, `backend/.python-version`, and `frontend/vercel.json` define
  the deployable configuration. No public URLs are recorded because no service
  was created or verified.

## Current Verification

Passed on 2026-07-29:

- `python3.11 -m pytest`: 31 passed
- `npm --prefix frontend test`: 6 passed
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
| Real-project Recall@3 | 0.6, 6/10 | 5.716 ms | 6.7814 ms |
| Real-project Recall@5 | 0.9, 9/10 | 6.822 ms | 11.4189 ms |

The real-project benchmark uses seven checked-in files and 27 chunks. Every
source is pinned by SHA-256, and reports include the dataset hash, corpus hashes,
environment, command, per-query results, and latency samples. Latency covers
query embedding plus FAISS search and excludes ingestion.

The fixed Day 5 local Gunicorn load run remains the current load evidence:
128,917 requests, zero failures, 1,078.47 requests per second, aggregate p50
260 ms, and aggregate p95 580 ms with 500 Locust users. The server and load
generator shared one Mac, so this is explicitly local-only evidence.

## Day 7 Frontend And Account Coverage

The frontend behavior suite verifies:

- the simplified primary navigation and More menu
- the new-learning-space form labels
- opening a learning space and switching to its embedded quiz without the
  previous null-session crash
- quiz question-card layout and radio options without redundant letter prefixes
- PDF and pasted-text source addition in one learning-space flow
- Enter-to-ask and Shift+Enter multiline question behavior
- account profile navigation and styled sign-out/delete confirmations

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
| 7 | Accounts and PDF sources | Complete locally |
| 8 | Deployment compatibility and production deployment | Compatibility complete; hosted deployment blocked |
| 9 | Additional product features | Not started |

## Day 8 Deployment Evidence

Local checks completed during this phase:

- RAG provider boundary supports local MiniLM and an authenticated HTTP
  embedding provider without changing the ingest/retrieve contract.
- Render configuration pins Python 3.11.12 and one Gunicorn worker to avoid
  per-worker model duplication.
- Refreshed real-corpus reports and frontend benchmark data pass the pinned
  source/report consistency checks.
- A separate local Gunicorn smoke with 10 Locust users for 10 seconds produced
  598 requests, zero failures, 62.68 requests per second, aggregate p50 4 ms,
  and aggregate p95 9 ms. This is a short local smoke, not hosted capacity.
- `bash scripts/verify.sh` passed after moving the pre-existing generated
  `frontend/build` directory to `/private/tmp`: 31 backend tests, 6 frontend
  tests, production build, and 0 frontend audit vulnerabilities.
- Provider access check reached the Render sign-in page. No credentials were
  entered and no external deployment side effect was performed.

Remaining risks and required public verification:

- Create the Render service and set `CORS_ORIGINS`, OpenAI, Supabase, and
  database variables.
- Create the Vercel project with `VITE_API_URL` pointing at Render.
- Verify `/healthz`, session creation, pasted/PDF ingestion, retrieval,
  grounded answer, quiz or flashcard generation, and authenticated account
  calls from the public frontend.
- Verify restart behavior and decide whether session re-ingestion is acceptable
  or whether durable indexes are required before scale-out.
- Run Locust from a separate machine against the public backend. Keep the
  existing 500-user result labeled local-only until then.

## Immediate Next Step

Day 8 should:

- choose the hosted embedding architecture
- configure the frontend and backend for the selected hosts
- deploy the current core app
- verify health, persistence, ingestion, retrieval, grounded generation, and
  frontend-to-backend calls
- rerun load testing against the deployable architecture before making a
  production capacity claim

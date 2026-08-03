# LearnLoop Revamp Status

Last updated: 2026-08-03

## Current State

- Days 1 through 7 are complete locally on `main`.
- Day 8 deployment compatibility is implemented locally. Public deployment
  still requires applying the pgvector migration and deploying Modal.
- The backend is a Flask package under `backend/app/`, with `backend/main.py`
  for local development and `backend/wsgi.py` for Gunicorn.
- Persistent learning spaces, materials, grounded conversations, quizzes,
  flashcards, history, and score-based progress are implemented.
- RAG sends source text to Modal, which performs 512-token chunking with
  64-token overlap and weighted pooling across MiniLM-sized windows. Supabase
  pgvector stores the resulting source chunks and 384-dimensional vectors.
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
- The selected hosted architecture is Vercel, Render, Modal, and Supabase
  pgvector. Render no longer installs FAISS, Sentence Transformers, or the
  local MiniLM model.
- `modal/embedding_service.py`, `render.yaml`, `backend/.python-version`, and
  `frontend/vercel.json` define the deployable configuration. Render and Vercel
  URLs are recorded below from the existing manual deployments; Modal and
  pgvector are not yet publicly verified.

Current deployment URLs:

- Frontend: https://learnloop-portfolio.vercel.app/
- Backend: https://learnloop-api-a1h4.onrender.com
- Backend health: https://learnloop-api-a1h4.onrender.com/healthz
- Modal embedding service: not deployed yet

## Current Verification

Passed locally on 2026-08-03:

- `PYTHONPATH=backend python3.11 -m pytest`: 32 passed
- `npm --prefix frontend test`: 6 passed
- `npm --prefix frontend run build`: production build succeeded
- `npm --prefix frontend audit --omit=dev`: 0 vulnerabilities
- `docker compose config --quiet`
- remote-provider contract tests with a deterministic fake provider
- pinned benchmark source and frontend-report consistency tests
- all three active retrieval benchmark commands

The active retrieval measurements are:

| Benchmark | Result | p50 | p95 |
| --- | --- | --- | --- |
| Synthetic near-neighbor Recall@3 | 1.0, 13/13 | 12.89 ms | 543.597 ms |
| Real-project Recall@3 | 0.6, 6/10 | 5.716 ms | 6.7814 ms |
| Real-project Recall@5 | 0.9, 9/10 | 6.822 ms | 11.4189 ms |

The checked-in real-project benchmark reports are historical pre-cutover
evidence from local MiniLM and FAISS. They are retained for traceability, but
they are not evidence for Modal or pgvector performance. A fresh benchmark
requires a configured Modal endpoint and Supabase database.

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

- RAG now requires an authenticated HTTP embedding provider and a durable
  vector-store boundary. Local tests use a deterministic fake provider and
  memory store only.
- Render configuration pins Python 3.11.12 and one Gunicorn worker. The model
  is no longer installed on Render.
- The pgvector migration and Modal service source are present locally. Their
  hosted deployment has not yet been verified.
- The standard Vite build could not clear a pre-existing protected
  `frontend/build` directory in this checkout. An equivalent production build
  succeeded with `npx vite build --outDir /private/tmp/learnloop-build-day8`.
- `npm --prefix frontend audit --omit=dev` could not reach the npm registry in
  this environment; the prior audit result remains 0 vulnerabilities.
- A separate local Gunicorn smoke with 10 Locust users for 10 seconds produced
  598 requests, zero failures, 62.68 requests per second, aggregate p50 4 ms,
  and aggregate p95 9 ms. This is a short local smoke, not hosted capacity.
- `bash scripts/verify.sh` passed after moving the pre-existing generated
  `frontend/build` directory to `/private/tmp`: 31 backend tests, 6 frontend
  tests, production build, and 0 frontend audit vulnerabilities.
- Provider access check reached the Render sign-in page. No credentials were
  entered and no external deployment side effect was performed.

Remaining risks and required public verification:

- Apply the pgvector migration to the production Supabase database.
- Deploy `modal/embedding_service.py`, create its secret, and test both
  `/index` and `/embed`.
- Update Render with the Modal URL/token and `VECTOR_STORE=pgvector`.
- Verify `/healthz`, session creation, pasted/PDF ingestion, retrieval,
  grounded answer, quiz or flashcard generation, and authenticated account
  calls from the public frontend.
- Restart Render and confirm an indexed workspace remains searchable.
- Run Locust from a separate machine against the public backend. Keep the
  existing 500-user result labeled local-only until then.

## Immediate Next Step

Day 8 implementation is complete locally. The remaining work is operational:
apply the database migration, deploy Modal, update Render variables, and run
the public end-to-end verification before marking production deployment
complete.

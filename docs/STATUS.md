# LearnLoop Revamp Status

Last updated: 2026-07-28

## Current State

- Repo is clean on `main`.
- Backend is a single Flask file with SQLAlchemy models and OpenAI generation helpers.
- Frontend is Create React App with React 19 and `react-scripts@5`.
- Frontend production build passes.
- Frontend test suite has been replaced with a baseline app render test and now passes.
- Backend smoke checks pass for import, health, read endpoints, and selected write validation.
- Backend pytest smoke tests pass for health, read endpoints, validation errors, quiz-result persistence, and empty search.
- Local guardrail scripts have been added and installed as Git hooks for pre-commit and pre-push verification.
- No actual RAG implementation exists yet.
- No FAISS, local embedding, chunking, retrieval benchmark, Locust load test, or WAL configuration exists yet.
- Git workflow for this revamp is direct commits to `main` with logical multi-commit history.

## Baseline Verification

Passed:

- `PYTHONDONTWRITEBYTECODE=1 python3 -c "compile(open('backend/thinkmate.py').read(), 'backend/thinkmate.py', 'exec')"`
- Flask app import with dummy `OPENAI_API_KEY`
- `GET /healthz`
- `GET /history`
- `GET /analytics/stats`
- `GET /quiz_history`
- `GET /analytics/quiz_stats`
- `GET /flashcards_history`
- `GET /analytics/flashcard_stats`
- temporary SQLite smoke test for `/quiz_results`
- `python3.11 -m pytest`
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

Residual Warnings:

- Backend pytest reports a SQLAlchemy `Query.get()` legacy warning from the current Flask-SQLAlchemy query API.
- Frontend Jest reports React Router v7 future-flag warnings.
- Frontend build reports stale Browserslist data and a Node deprecation warning from the current CRA toolchain.

Guardrails:

- `scripts/precommit-check.sh` verifies the current branch is `main`, blocks staged `.env` files and `conversations.db`, checks staged whitespace, runs backend tests, and runs frontend tests.
- `scripts/verify.sh` verifies the current branch is `main`, checks unstaged and staged whitespace, runs backend tests, runs frontend tests, and runs the frontend production build.
- `scripts/install-git-hooks.sh` installs local `pre-commit` and `pre-push` hooks that call those scripts.

## Phase Progress

| Phase | Focus | Status |
| --- | --- | --- |
| 1 | Backend stabilization | Not started |
| 2 | Real RAG layer | Not started |
| 3 | Benchmark evidence | Not started |
| 4 | Pydantic self-healing generation | Not started |
| 5 | Load testing and WAL validation | Not started |
| 6 | Complete frontend redesign | Not started |
| 7 | Additional impressive product features | Not started |

## Immediate Next Step

Continue on `main` and start Phase 1:

- split backend structure carefully
- fix OpenAI import-time requirement
- fix Docker port behavior
- add backend tests
- configure SQLite WAL
- keep behavior equivalent unless a fix is explicitly part of the phase

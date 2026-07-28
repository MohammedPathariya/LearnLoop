# LearnLoop Deployment Notes

This file tracks local, Docker, and hosted deployment behavior during the revamp.

## Current Setup

Backend:

- Framework: Flask
- Smoke-test entry point: `backend/main.py`
- WSGI entry point: `backend/wsgi.py`, which creates the schema before serving
- Production-style local/Docker server: Gunicorn with four workers and two
  threads per worker
- App package: `backend/app/`
- Default local fallback DB: `backend/conversations.db`
- Optional production DB: `SUPABASE_DB_URI`
- Direct local startup with `python3.11 backend/main.py` uses SQLite even if a
  stale remote URI exists in `backend/.env`. Set `LEARNLOOP_USE_REMOTE_DB=1`
  only when deliberately testing a valid remote database URI.
- Required model key: `OPENAI_API_KEY` only for generation endpoints.

Frontend:

- Framework: Create React App
- API base URL: `REACT_APP_API_URL`, falling back to `http://localhost:5050`
- Production build command: `npm run build`

Docker:

- Root compose file: `docker-compose.yml`
- Backend service builds from `./backend`
- Frontend service builds from `./frontend`

## Verified Baseline

- Frontend production build succeeds with `npm run build`.
- Backend imports and `/healthz` returns `200 OK` without requiring `OPENAI_API_KEY`.
- Backend read endpoints return `200` against the checked-in SQLite DB.
- Backend write-path smoke checks pass against a temporary SQLite DB.
- Local SQLite connections use `PRAGMA journal_mode=WAL`.
- The Day 5 500-user local run used WAL plus `PRAGMA busy_timeout=5000`; it
  completed with no SQLite lock errors, but the single-process local setup had
  21.52% client-side transport failures under the load generator.

## Known Deployment Issues

- Docker Compose maps backend host port `5050` to container port `5050`, matching the Flask default.
- README and the frontend default both point to the backend at `http://localhost:5050`.
- The backend no longer requires `OPENAI_API_KEY` during import; missing keys fail only when generation endpoints need the model client.
- The Docker volume maps `./backend/conversations.db` to `/app/conversations.db`; this matches the current Docker workdir but should be rechecked after backend refactoring.
- The Flask development server is for smoke checks only. Load tests must use
  the Gunicorn command documented in `load_tests/README.md`.

## Deployment Goals

- Local dev should start with one documented command.
- Docker Compose should expose backend and frontend on documented ports.
- Tests do not require a real OpenAI key.
- Local SQLite uses WAL mode.
- 500-user load-test evidence is local-only until repeated with a production
  WSGI server and a separate load-generator process or host.
- Hosted deployment configuration should be documented after the backend structure settles.

## Commands To Reverify

Full local guardrail suite:

```bash
cd /Users/mohammedpathariya/Docs/IUB\ Docs/Projects/LearnLoop
bash scripts/verify.sh
```

Pre-commit guardrail suite:

```bash
cd /Users/mohammedpathariya/Docs/IUB\ Docs/Projects/LearnLoop
bash scripts/precommit-check.sh
```

```bash
cd /Users/mohammedpathariya/Docs/IUB\ Docs/Projects/LearnLoop
docker compose up --build
```

```bash
cd frontend
npm run build
```

```bash
cd backend
python main.py
```

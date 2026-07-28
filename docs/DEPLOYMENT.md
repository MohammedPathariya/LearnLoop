# LearnLoop Deployment Notes

This file tracks local, Docker, and hosted deployment behavior during the revamp.

## Current Setup

Backend:

- Framework: Flask
- Entry point: `backend/thinkmate.py`
- Default local fallback DB: `backend/conversations.db`
- Optional production DB: `SUPABASE_DB_URI`
- Required model key: `OPENAI_API_KEY`

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
- Backend imports and `/healthz` returns `200 OK` when `OPENAI_API_KEY` is present.
- Backend read endpoints return `200` against the checked-in SQLite DB.
- Backend write-path smoke checks pass against a temporary SQLite DB.

## Known Deployment Issues

- `docker-compose.yml` maps host port `5050` to container port `5000`, but the Flask app defaults to port `8080` unless `PORT` is set.
- README currently says the backend runs at `http://localhost:5000`, while the frontend default points to `http://localhost:5050`.
- The backend requires `OPENAI_API_KEY` during import, which makes tests and health checks more brittle than necessary.
- The Docker volume maps `./backend/conversations.db` to `/app/conversations.db`; this matches the current Docker workdir but should be rechecked after backend refactoring.

## Deployment Goals

- Local dev should start with one documented command.
- Docker Compose should expose backend and frontend on documented ports.
- Tests should not require a real OpenAI key.
- Local SQLite should use WAL mode.
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
python thinkmate.py
```

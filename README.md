# LearnLoop

LearnLoop is a source-grounded study workspace. Learners organize material into
persistent journeys, ask questions backed by retrieved evidence, generate
validated quizzes and flashcards from the same sources, and review saved
progress.

The redesigned Day 7 application is verified locally. The previous public
deployment does not represent this version. Public deployment is Day 8 scope.

## Product

- Home resumes a learning space or starts a new one.
- Learn combines materials, grounded questions, quizzes, and flashcards in one
  journey.
- Progress reports saved quiz score trends and topic averages.
- History reopens saved sessions and practice artifacts.
- Users can sign in with Supabase email/password authentication and return to
  account-associated learning activity.
- Guests can use the guided Machine Learning Foundations demo and create a
  learning space without signing in.
- Learning spaces accept PDF uploads and pasted study text together.
- Benchmarks display checked-in retrieval and local load-test evidence.

## Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11, Flask, SQLAlchemy, Pydantic |
| Retrieval | sentence-transformers, FAISS |
| Generation | OpenAI Python client |
| Frontend | React 19, Vite, Vitest, Wouter |
| Local persistence | SQLite with WAL |
| Account persistence | Supabase Auth and Postgres schema |
| Containers | Docker Compose, Gunicorn |

## Run locally

### Docker Compose

Copy `backend/.env.example` to `backend/.env`. Add `OPENAI_API_KEY` to use
generation endpoints. The health check, seeded demo, retrieval, and frontend
build do not require the key.

```bash
docker compose up --build
```

Open the frontend at `http://localhost:3000`. The backend runs at
`http://localhost:5050`. Docker persists SQLite data in the `learnloop-data`
named volume.

### Separate development servers

Backend:

```bash
python3.11 -m pip install -r backend/requirements.txt
python3.11 backend/main.py
```

Frontend:

```bash
cd frontend
npm ci
npm start
```

Set `VITE_API_URL` only when the backend is not at
`http://localhost:5050`.

## Verify

```bash
bash scripts/verify.sh
```

This runs backend tests, frontend behavior tests, the production frontend build,
and a production dependency audit.

## Retrieval benchmarks

The active real-project corpus is pinned by source-file SHA-256 hashes so source
drift cannot silently change a result.

| Benchmark | Result | Latency |
| --- | --- | --- |
| Synthetic near-neighbor Recall@3 | 1.0, 13/13 | p50 12.89 ms, p95 543.597 ms |
| Real-project Recall@3 | 0.6, 6/10 | p50 15.433 ms, p95 30.8652 ms |
| Real-project Recall@5 | 0.9, 9/10 | p50 15.826 ms, p95 33.8765 ms |

The real corpus contains seven checked-in source files and 27 indexed chunks.
Latency measures query embedding plus FAISS search and excludes ingestion.
Exact commands, environments, per-query results, and corpus hashes are in
[`docs/benchmarks/README.md`](docs/benchmarks/README.md).

## Load-test evidence

The fixed local Gunicorn run completed 128,917 requests with zero failures at
1,078.47 requests per second, aggregate p50 of 260 ms, and aggregate p95 of
580 ms. It used 500 Locust users, four Gunicorn workers, two threads per worker,
and SQLite WAL. The load generator and server shared one Mac, so this is
local-only evidence, not a production capacity claim. See
[`docs/load-tests/README.md`](docs/load-tests/README.md).

## Current boundaries

- Guest mode uses a browser-session identifier and does not require an account.
- Supabase email/password authentication is implemented for account-associated
  sessions, scores, history, messages, quizzes, and flashcards.
- PDF upload and text paste are implemented source inputs. The intended
  privacy boundary is session-only source content, but the legacy SQLAlchemy
  material path still needs removal before that boundary is production-enforced.
- Progress is based on saved quiz results, not inferred concept mastery.
- Retrieval indexes are in memory and rebuilt from durable material text.
- The hosted architecture and production load rerun remain Day 8 work.

Project status and remaining work are tracked in
[`docs/STATUS.md`](docs/STATUS.md).

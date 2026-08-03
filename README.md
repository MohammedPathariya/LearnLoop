# LearnLoop

LearnLoop is a source-grounded study workspace. Learners organize material into
persistent journeys, ask questions backed by retrieved evidence, generate
validated quizzes and flashcards from the same sources, and review saved
progress.

This repository is also a research portfolio project. Its implementation,
architecture decisions, benchmark reports, load-test reports, and remaining
limitations are kept together so that technical claims can be inspected rather
than inferred from a product demo.

[Live application](https://learnloop-portfolio.vercel.app/) · [Render API health](https://learnloop-api-a1h4.onrender.com/healthz)

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
| Retrieval | Modal embedding service, `all-MiniLM-L6-v2`, Supabase pgvector |
| Generation | OpenAI Python client |
| Frontend | React 19, Vite, Vitest, Wouter |
| Local persistence | SQLite with WAL fallback |
| Hosted persistence | Supabase Auth, Postgres, and pgvector |
| Containers | Docker Compose, Gunicorn |

## Architecture

The implemented system is documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
including Mermaid diagrams for:

- the deployed component boundaries and trust boundary
- PDF and pasted-text ingestion into durable vector storage
- grounded question, retrieval, and generation flow
- authenticated and guest identity paths
- the code and configuration behind each boundary

At a high level, Vercel serves the frontend, Render serves the Flask API,
Modal owns chunking and embedding, Supabase stores account activity and
pgvector chunks, and OpenAI performs answer, quiz, and flashcard generation.
The API coordinates these services and is the only component that holds
database and provider credentials.

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
- PDF upload and text paste are implemented source inputs. Current pgvector
  retrieval stores source chunks and text durably. Pasted text also follows the
  legacy SQLAlchemy material path, while PDF source metadata/text uses the
  current in-memory source registry. This mixed retention model is a known
  privacy boundary and must be resolved before making a uniform source-retention
  claim.
- Progress is based on saved quiz results, not inferred concept mastery.
- Production retrieval is intended to use durable Supabase pgvector rows. The
  memory vector store is retained for deterministic local tests and fixtures.
- Modal deployment, production pgvector migration, public end-to-end smoke
  testing, and a separate-machine load rerun remain incomplete.

Project status and remaining work are tracked in
[`docs/STATUS.md`](docs/STATUS.md).

## Documentation map

| Document | Purpose |
| --- | --- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System boundaries, data movement, identity, persistence, and code map |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Architecture decisions and the reasoning behind them |
| [`docs/STATUS.md`](docs/STATUS.md) | Current implementation, verification evidence, and deployment gaps |
| [`docs/benchmarks/README.md`](docs/benchmarks/README.md) | Retrieval evaluation method, reports, and provenance |
| [`docs/load-tests/README.md`](docs/load-tests/README.md) | Load-test commands, raw reports, failures, and local-only limits |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Hosted configuration and operational deployment sequence |

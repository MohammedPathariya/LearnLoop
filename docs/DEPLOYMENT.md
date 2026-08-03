# LearnLoop Deployment Notes

This document describes the Day 8 deployment architecture and the limits of
the current hosted design. Public deployment is not marked complete until the
frontend-to-backend workflow is verified from the deployed frontend URL.

## Selected architecture

- Vercel serves the Vite frontend from `frontend/`.
- Render serves the Flask API from `backend/` with Python 3.11.12, one Gunicorn
  worker, two threads, and a 120-second request timeout.
- Render runs `all-MiniLM-L6-v2` in-process for the first deployment. The model
  is downloaded on the first embedding request and remains in that worker's
  memory.
- FAISS indexes remain in memory and are scoped by `session_id`.
- OpenAI handles generation only. It is not required for health, reads, or
  retrieval setup, but it is required for answer, quiz, flashcard, and chat
  generation.
- Supabase Postgres is the intended production database. SQLite is retained for
  local development and Docker only.

The backend also supports `EMBEDDING_PROVIDER=http`. That provider sends
`POST {EMBEDDING_SERVICE_URL}/embed` with `{"texts": [...]}` and expects
`{"embeddings": [[...], ...]}`. The service must use the same model, weighted
MiniLM-window pooling, and vector dimension as the local provider. Selecting
this mode sends the chunk text to that service, so the privacy boundary changes
from local-only embeddings to provider-mediated embeddings. Modal is not
selected or deployed in this phase because no authenticated Modal deployment
was available for verification.

## Render configuration

`render.yaml` defines the service. The Render service should use the repository
root and the Blueprint file, or equivalent manual settings:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 wsgi:app
Health check: /healthz
Python: 3.11.12
```

Required Render environment variables:

```text
PYTHON_VERSION=3.11.12
EMBEDDING_PROVIDER=local
CORS_ORIGINS=["https://<actual-vercel-project>.vercel.app"]
OPENAI_API_KEY=<secret>
SUPABASE_DB_URI=<Supabase Postgres URI>
SUPABASE_URL=<Supabase project URL>
SUPABASE_PUBLISHABLE_KEY=<Supabase publishable key>
```

Do not set `CORS_ORIGINS` to a quoted JSON string containing extra shell
quotes. It must be a JSON array whose origin exactly matches the browser origin.

The Docker image uses the same Python major/minor version and one worker. This
keeps local production-style behavior close to Render. Docker's named
`learnloop-data` volume persists SQLite files across container restarts, but a
Render filesystem should not be treated as durable application storage.

## Vercel configuration

Set the Vercel project root directory to `frontend`. `frontend/vercel.json`
uses `npm run build` and publishes the Vite `build` directory. Set:

```text
VITE_API_URL=https://<actual-render-service>.onrender.com
```

After the frontend URL is known, put that exact origin in Render's
`CORS_ORIGINS`, redeploy the backend, then redeploy the frontend if its API URL
changed.

## Memory, cold-start, and scale tradeoffs

In-process MiniLM keeps raw study text out of a hosted vector database and has
no network hop for embeddings after warm-up. Its costs are model download time,
model memory per worker, and duplicated model memory if workers are increased.
The selected one-worker configuration is a compatibility choice, not a
capacity guarantee.

Each worker has its own FAISS session registry. A restart, deploy, crash, or
scale-out sends the user to an empty retrieval index even when the SQL database
still contains the learning session and material metadata. The current core
app therefore needs a re-ingestion path after such an event. Durable source
storage is intentionally not added in Day 8.

The HTTP provider boundary can move model memory and model downloads to Modal
or another service. That trades Render memory for network latency, provider
cold starts, service authentication, request-size limits, and another failure
mode. It does not by itself make FAISS indexes durable or solve scale-out
session affinity.

## Verification commands

Run from the canonical checkout:

```bash
cd /Users/mohammedpathariya/Docs/IUB\ Docs/Projects/LearnLoop
bash scripts/precommit-check.sh
bash scripts/verify.sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=backend \
  python3.11 scripts/evaluate_retrieval.py \
  --dataset docs/benchmarks/real_project_corpus.json \
  --report /private/tmp/learnloop-recall5.json \
  --benchmark-name 'LearnLoop real project corpus Recall@5' \
  --top-k 5
```

For local production-style API testing:

```bash
gunicorn --chdir backend --bind 127.0.0.1:5050 \
  --workers 1 --threads 2 --timeout 120 wsgi:app
```

For the existing Locust evidence:

```bash
locust -f load_tests/locustfile.py --headless \
  --users 500 --spawn-rate 25 --run-time 2m \
  --host http://127.0.0.1:5050 \
  --csv /private/tmp/learnloop-locust
```

The checked-in 500-user report remains local-only. It used a shared Mac for
the backend and load generator and must not be presented as hosted capacity.
Until a separate load generator targets the public Render URL, no production
throughput or user-capacity claim is verified.

## Deployment status

As of 2026-08-03, deployment provider authentication was not available in the
Codex session. No Render, Vercel, or Modal service was created or publicly
verified. Do not add placeholder deployment URLs to `docs/STATUS.md`.

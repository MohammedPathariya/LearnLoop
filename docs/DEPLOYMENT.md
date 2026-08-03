# LearnLoop Deployment Notes

This document describes the production architecture for the deployed core
app. Public deployment is complete only after the frontend, Render API, Modal
embedding service, and Supabase pgvector database have passed the smoke test.

## Selected architecture

- Vercel serves the Vite frontend from `frontend/`.
- Render serves the Flask API from `backend/` with Python 3.11.12, one
  Gunicorn worker, two threads, and a 120-second request timeout.
- Modal owns `all-MiniLM-L6-v2`, document chunking, and embedding generation.
- Supabase Postgres with pgvector stores document chunks and 384-dimensional
  embeddings durably.
- OpenAI handles answer, quiz, flashcard, and conversation generation only.
- The frontend does not receive the Modal token or any database credentials.

The backend no longer loads MiniLM, uses FAISS, or keeps a process-local RAG
index. A Render restart or scale-out does not erase indexed material because
chunks and vectors are stored in Supabase.

Existing SQLAlchemy materials created before this cutover are reindexed once on
their first grounded question if their session has no pgvector rows. New
materials are written to pgvector during ingestion.

## Modal embedding service

The service source is `modal/embedding_service.py`. It exposes:

```text
POST /index  {"text": "..."}
POST /embed  {"texts": ["..."]}
```

`/index` chunks source text with 512-token chunks and 64-token overlap, pools
MiniLM-sized windows, and returns chunks with 384-dimensional normalized
vectors. `/embed` creates query vectors. Both endpoints require a Bearer token.

Create a Modal secret containing `EMBEDDING_SERVICE_TOKEN`, then deploy:

```bash
modal secret create learnloop-embedding EMBEDDING_SERVICE_TOKEN=<random-token>
modal deploy modal/embedding_service.py
```

Record the deployed `/index` or `/embed` base URL in Render as
`EMBEDDING_SERVICE_URL`. Modal web endpoints can cold-start after inactivity,
and deployed web functions have a maximum HTTP request timeout of 150 seconds.
See the [Modal Web Functions documentation](https://modal.com/docs/guide/webhooks)
and [Modal timeout documentation](https://modal.com/docs/guide/webhook-timeouts).

## Supabase pgvector

Apply the migration:

```text
supabase/migrations/20260803180000_create_study_chunks_vector.sql
```

It enables pgvector and creates `public.study_chunk` with a `vector(384)`
column. The current API enforces session ownership before reading or changing
chunks. Database-level RLS for this legacy Flask table is a remaining security
hardening task.

Source text is now durable because grounded answer generation needs the stored
chunk text. This is a deliberate change from the earlier ephemeral PDF/source
design and must be disclosed in the portfolio documentation.

## Render configuration

`render.yaml` defines the service:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 wsgi:app
Health check: /healthz
Python: 3.11.12
```

Required Render variables:

```text
PYTHON_VERSION=3.11.12
EMBEDDING_PROVIDER=http
EMBEDDING_SERVICE_URL=https://<modal-endpoint>.modal.run
EMBEDDING_SERVICE_TOKEN=<secret>
EMBEDDING_SERVICE_TIMEOUT_SECONDS=120
VECTOR_STORE=pgvector
CORS_ORIGINS=["https://learnloop-portfolio.vercel.app"]
OPENAI_API_KEY=<secret>
SUPABASE_DB_URI=<Supabase Postgres URI>
SUPABASE_URL=<Supabase project URL>
SUPABASE_PUBLISHABLE_KEY=<Supabase publishable key>
```

Do not commit or paste secrets into source files. `CORS_ORIGINS` must be a JSON
array containing the exact browser origin.

Removing PyTorch, Sentence Transformers, Transformers, and FAISS from the
Render dependency set reduces model memory and image size. Render Free can
still sleep after inactivity, so the first frontend request may wait for the
Render service to wake before Modal is called.

## Vercel configuration

Set the Vercel project root directory to `frontend` and configure:

```text
VITE_API_URL=https://learnloop-api-a1h4.onrender.com
```

The frontend uses the same API routes as local development. No Modal or
Supabase secret belongs in Vercel.

## Persistence, cold starts, and scale

| Component | Restart behavior | Main tradeoff |
| --- | --- | --- |
| Render API | Stateless API process | Free-tier wake delay |
| Modal model | Container may cold-start | Lower Render memory, extra network hop |
| Supabase pgvector | Durable chunks and vectors | Database cost and source retention |
| Vercel frontend | Static build persists | Separate deployment environment |

Modal does not provide vector persistence. Supabase pgvector provides that.
Modal only moves chunking and model inference away from Render. A first request
can still encounter both Render and Modal cold starts.

The current vector search uses exact cosine-distance ordering, which is
appropriate for this portfolio-sized corpus. An HNSW or IVFFlat index should be
considered only if the stored corpus grows materially.

## Verification commands

Run local application tests:

```bash
cd /Users/mohammedpathariya/Docs/IUB\ Docs/Projects/LearnLoop
bash scripts/precommit-check.sh
bash scripts/verify.sh
```

Verify the Modal contract before changing Render variables:

```bash
curl -X POST "$EMBEDDING_SERVICE_URL/index" \
  -H "Authorization: Bearer $EMBEDDING_SERVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Mitosis divides one parent cell into two daughter cells."}'
```

Then verify the public app in this order:

1. `GET https://learnloop-api-a1h4.onrender.com/healthz` returns `OK`.
2. Open `https://learnloop-portfolio.vercel.app/`.
3. Log in and open the existing demo/account learning space.
4. Ask a grounded question and confirm sources are returned.
5. Create a new workspace and add pasted material.
6. Wait for indexing to finish and ask a question about that material.
7. Restart or redeploy Render, reopen the workspace, and repeat retrieval.
8. Generate a quiz or flashcards.

The existing 500-user Locust report remains local-only evidence. It must not be
described as hosted capacity without a separate load generator targeting the
public architecture.

# LearnLoop Architecture

This document describes the implemented LearnLoop architecture as of 2026-08-03. It is intentionally split into system boundaries and request flows so that the research claims in the repository can be traced to code and configuration.

## System context

```mermaid
flowchart LR
    learner["Learner"] --> browser["React 19 + Vite\nVercel frontend"]
    browser -->|HTTPS + visitor header\nor Supabase bearer token| api["Flask API\nRender + Gunicorn"]
    browser -->|email/password auth| auth["Supabase Auth"]
    api -->|verify bearer token| auth
    api -->|SQLAlchemy\nlearning records| db["Supabase Postgres\nSQLite fallback locally"]
    api -->|chunk and embed\n/index or /embed| modal["Modal embedding service\nMiniLM + tokenizer"]
    api -->|write and query\nsource chunks + vectors| vector["Supabase pgvector\nstudy_chunk"]
    api -->|grounded answer,\nquiz, flashcards| openai["OpenAI API"]
    modal -->|384-dimensional vectors\nand chunk metadata| api
    api -->|retrieved evidence| openai
    openai -->|validated output| api
    api --> browser

    classDef runtime fill:#e8f0ff,stroke:#3b5bdb,color:#172554;
    classDef data fill:#eaf7ef,stroke:#2f855a,color:#173b2a;
    classDef external fill:#fff4df,stroke:#b7791f,color:#4a2c00;
    class browser,api,modal runtime;
    class db,vector data;
    class auth,openai external;
```

The API is the trust boundary. The browser never receives database credentials or the Modal token. Authenticated requests are checked against Supabase Auth. Guest requests use an `X-LearnLoop-Visitor` browser-session identifier.

## Source ingestion flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as Flask API
    participant P as PDF extractor
    participant M as Modal embedding service
    participant V as Supabase pgvector
    participant R as SQL database

    B->>A: POST material or PDF to a learning session
    A->>R: Create or update learning-session record
    alt PDF upload
        A->>P: Extract selectable text from uploaded bytes
        P-->>A: Plain text
    end
    A->>M: POST /index with source text
    Note over M: 512-token chunks, 64-token overlap\nweighted pooling over MiniLM-sized windows
    M-->>A: Chunk text, token counts, 384-d vectors
    A->>V: Replace source rows for session/source
    V-->>A: Indexed chunk count
    A->>R: Store material metadata and status
    A-->>B: Source status and chunk count
```

Pasted text is stored through the legacy `StudyMaterial` SQLAlchemy path. PDF text is held in the current in-memory source registry while its chunks are persisted in pgvector. This is a known privacy and deployment boundary, not a claim that all source text is ephemeral.

## Grounded question flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as Flask API
    participant M as Modal embedding service
    participant V as Supabase pgvector
    participant O as OpenAI API
    participant R as SQL database

    B->>A: POST question for session
    A->>M: POST /embed with question
    M-->>A: Query vector
    A->>V: Cosine search by session_id
    V-->>A: Top-k chunks with scores
    A->>O: Question plus retrieved source evidence
    O-->>A: Candidate grounded answer
    A->>R: Save message, sources, and retrieval latency
    A-->>B: Answer, citations, and grounding metadata
```

The same session retrieval path supplies context for quiz and flashcard generation. Pydantic schemas validate generated structures, and the bounded repair loop returns a stable error after the allowed retries are exhausted.

## Identity and persistence

```mermaid
flowchart TD
    request["Incoming browser request"] --> authcheck{"Supabase bearer token?"}
    authcheck -->|valid| user["Authenticated user id"]
    authcheck -->|absent| guest["X-LearnLoop-Visitor\n(or local-dev fallback)"]
    user --> owner["Session ownership check"]
    guest --> owner
    owner --> records["Learning sessions,\nmessages, quiz results,\nflashcard sets"]
    owner --> sources["Source ingestion\nand vector retrieval"]
    records --> postgres["Supabase Postgres\nRLS-backed account schema"]
    sources --> chunks["study_chunk\npgvector rows"]
```

Account-associated activity is stored in the Supabase schema. Guest activity is scoped by the browser visitor identifier. The current migration comment states that `study_chunk` access is enforced by the Flask API; database-level RLS for this legacy Flask table remains a hardening task.

## Repository map

| Concern | Code or configuration |
| --- | --- |
| Flask app factory and startup | `backend/app/factory.py`, `backend/main.py`, `backend/wsgi.py` |
| Auth and ownership | `backend/app/auth.py`, `backend/app/study_routes.py` |
| Study and generation routes | `backend/app/routes.py`, `backend/app/study_routes.py` |
| PDF extraction and source registry | `backend/app/services/pdf.py`, `backend/app/services/pdf_sources.py` |
| Embedding boundary and retrieval orchestration | `backend/app/services/embeddings.py`, `backend/app/services/rag.py` |
| Vector persistence | `backend/app/services/vector_store.py`, `supabase/migrations/20260803180000_create_study_chunks_vector.sql` |
| Modal model service | `modal/embedding_service.py` |
| Client API and UI | `frontend/src/api/learnloopApi.js`, `frontend/src/pages/`, `frontend/src/components/` |
| Evidence and verification | `docs/benchmarks/`, `docs/load-tests/`, `scripts/verify.sh` |

## Boundaries and non-claims

- The checked-in retrieval benchmarks are historical local MiniLM and FAISS evidence. They do not verify current Modal or pgvector performance.
- The 500-user Locust result is a shared-machine local result, not hosted capacity evidence.
- Modal deployment, the production pgvector migration, and public end-to-end verification remain operational work recorded in [`STATUS.md`](STATUS.md).
- Source retention is not uniform yet. The portfolio should describe the current durable pgvector and legacy SQLAlchemy paths, not claim session-only storage globally.

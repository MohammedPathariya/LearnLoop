# LearnLoop Revamp Week Plan

Each phase is one focused day. Keep changes scoped, verified, and documented in `docs/STATUS.md`.

## Day 1: Backend Stabilization

Goal: Make the backend maintainable and testable without changing the product surface unnecessarily.

Scope:

- Create a clean backend structure around app factory, db setup, routes, services, and schemas.
- Remove import-time dependency on a real OpenAI key.
- Fix Docker/backend port mismatch.
- Add pytest smoke tests for health, read endpoints, validation errors, and quiz-result persistence.
- Enable SQLite WAL for local SQLite mode.

Definition of done:

- Backend tests pass.
- Existing endpoints keep their current response shapes unless explicitly changed.
- Docker/local port behavior is documented.
- `docs/STATUS.md` is updated.

## Day 2: Real RAG Layer

Goal: Implement the actual session-based RAG layer described in the resume claim.

Scope:

- Add study material ingestion.
- Add 512-token chunking with overlap.
- Add local `all-MiniLM-L6-v2` embeddings.
- Add in-memory FAISS index scoped by session.
- Add retrieval endpoint returning top-k chunks and latency.
- Add source-grounded answer generation using retrieved chunks.

Definition of done:

- A session can ingest text and retrieve relevant chunks.
- Retrieval does not mix data across sessions.
- Basic unit tests cover chunking and session isolation.
- `docs/STATUS.md` is updated.

## Day 3: Benchmark Evidence

Goal: Produce traceable retrieval metrics instead of unverified claims.

Scope:

- Add a small benchmark dataset with questions and expected source chunks.
- Add a retrieval evaluation script.
- Measure Recall@5 and retrieval latency.
- Save benchmark output under `docs/benchmarks/`.
- Update README only with measured results.

Definition of done:

- Benchmark can be rerun locally.
- Report includes environment, command, dataset size, Recall@5, and p50/p95 latency.
- No resume-style metric is added unless measured.

## Day 4: Pydantic Self-Healing Generation

Goal: Make quiz and flashcard generation reliable and defensible.

Scope:

- Add Pydantic schemas for generated quizzes and flashcards.
- Validate model output.
- Retry with validation feedback when output is malformed.
- Cap retry attempts.
- Record validation attempts and final failure cases.
- Add tests for malformed JSON and schema-invalid JSON.

Definition of done:

- Generated quiz and flashcard outputs conform to schemas.
- Malformed-output handling is tested.
- User-facing errors are clearer.
- `docs/STATUS.md` is updated with measured behavior if available.

## Day 5: Load Testing And SQLite WAL

Goal: Validate concurrency behavior and make the load-test claim real.

Scope:

- Add Locust load tests.
- Simulate realistic flows: session creation, retrieval, quiz save, flashcard save, history reads.
- Run 500 simulated users locally or in Docker.
- Compare SQLite behavior with WAL enabled.
- Save reports under `docs/load-tests/`.

Definition of done:

- Locust test command is documented.
- Load-test output is saved.
- Failure rate, throughput, p50, and p95 latency are reported.
- SQLite lock behavior is documented honestly.

## Day 6: Frontend Redesign

Goal: Replace the current UI with a modern study workspace.

Scope:

- Decide whether to keep CRA temporarily or migrate to Vite.
- Build a new app layout around sessions, study materials, RAG chat, source snippets, quizzes, flashcards, and analytics.
- Add real loading, empty, error, and success states.
- Remove stale boilerplate tests.
- Add practical frontend tests for core routes/components.

Definition of done:

- Frontend build passes.
- Frontend tests pass.
- Main workflows are usable from the redesigned interface.
- No backend claims are hidden behind unfinished UI.

## Day 7: Additional Product Features

Goal: Add extra features that make LearnLoop more useful and more impressive on a resume.

Scope:

- Brainstorm and choose the best 2-3 features after Days 1-6 are complete.
- Candidate features:
  - adaptive review based on missed quiz questions
  - topic mastery tracking
  - flashcard export to CSV or Anki-style format
  - source-cited study summaries
  - shareable study packs
  - spaced-repetition scheduling
  - per-session learning timeline

Definition of done:

- Selected features are implemented end-to-end.
- Features are tied to real user value and measurable technical work.
- README and resume bullets are updated with only verified claims.

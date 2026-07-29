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

## Day 7: Accounts And PDF Sources

Goal: Add the first user-facing product features beyond the core study workspace.

Scope:

- Add PDF upload with selectable-text extraction and session-scoped chunk indexing.
- Allow a learning space to contain both PDF and pasted-text sources.
- Add Supabase email/password authentication and verified bearer-token handling.
- Associate authenticated learning activity with the signed-in user.
- Keep guest mode available without an account and show the guided demo only to guests.
- Add account, sign-out, guest-mode, and source-privacy UI states.
- Provision the Supabase schema with RLS for profiles, learning sessions, messages,
  quiz results, and flashcard sets, without a durable source table.

Definition of done:

- A user can upload a PDF and add pasted text to the same learning space.
- Authenticated users can sign in, sign out, and recover their account-specific study flow.
- Guest users can use the demo and create a session without signing in.
- PDF and pasted-source behavior, account isolation, and guest behavior are tested locally.
- `docs/STATUS.md` and the decision log record the implementation and remaining privacy risks.

## Day 8: Deployment Compatibility And Production Deployment

Goal: Deploy the completed core app before adding extra product features.

Scope:

- Revisit the RAG architecture after Days 1-7 are implemented.
- Decide whether embeddings run in-process on Render, behind a Modal service, or through another provider boundary.
- Add environment-driven configuration for local versus deployed embedding and generation providers.
- Keep the Render backend lightweight enough for the selected instance type.
- Document what data is ephemeral, what is durable, and what breaks on restart or scale-out.
- Update deployment files and docs for Vercel frontend, Render backend, and Modal model service if used.
- Deploy the frontend, backend, and model service pieces needed for the core app.
- Verify the deployed app end-to-end from the public frontend URL.
- Re-run backend tests, frontend tests, frontend build, benchmark commands, and load tests that apply to the deployment architecture.
- Re-run or revise the 500-user Locust target against the deployable architecture, not only the local demo path.

Definition of done:

- `docs/DEPLOYMENT.md` clearly explains the deployed architecture and required environment variables.
- The backend has a feasible path for model work on the selected Render instance type.
- The deployed frontend can call the deployed backend successfully.
- Core deployed workflows work: health check, study material ingestion, retrieval, source-grounded answer generation, quiz or flashcard generation, and relevant read endpoints.
- Local development still works without requiring hosted Modal infrastructure.
- Load-test claims are tied to the final deployment architecture or clearly labeled local-only.
- Public deployment URLs and verification results are recorded in `docs/STATUS.md`.
- `docs/STATUS.md` is updated with the deployment decision, verification results, and remaining risks.

## Day 9: Additional Product Features

Goal: Add extra features that make LearnLoop more useful and more impressive on a resume.

Scope:

- Brainstorm and choose the best 2-3 features after Days 1-8 are complete.
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

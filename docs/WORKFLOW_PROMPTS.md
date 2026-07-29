# LearnLoop Workflow Prompts

Use one new Codex chat per day. Start each day by asking Codex to read the project docs and current diff before editing.

## Standard Start Prompt

```text
We are working on /Users/mohammedpathariya/Docs/IUB Docs/Projects/LearnLoop.

Before editing, read:
- docs/STATUS.md
- docs/WEEK_PLAN.md
- docs/DECISIONS.md
- docs/DEPLOYMENT.md
- docs/WORKFLOW_PROMPTS.md

Then inspect git status and the relevant source files for today's phase. Keep the diff scoped to the phase. Run the appropriate verification before saying the work is done. Update docs/STATUS.md at the end.

Git workflow:
- Work directly on main.
- Do not create a branch unless I explicitly ask for one.
- Keep commits logically separate.
- Use commit messages with a concise subject and a short body explaining what changed and why.
- Before committing, run `bash scripts/precommit-check.sh`.
- Before pushing, run `bash scripts/verify.sh`.
- Push directly to origin/main when I ask you to push.
```

## Commit And Push Guardrails

Use these checks as the replacement safety net for not working on a separate branch.

Before every commit:

```bash
bash scripts/precommit-check.sh
```

Before every push:

```bash
bash scripts/verify.sh
```

Optional local Git hooks:

```bash
bash scripts/install-git-hooks.sh
```

The hooks are intentionally stored in `scripts/git-hooks/` because `.git/hooks/` is local-only and cannot be reviewed in normal Git history.

## Day 1 Prompt: Backend Stabilization

```text
Start Day 1 of the LearnLoop revamp: backend stabilization.

Goal:
Make the backend maintainable and testable while preserving existing endpoint behavior as much as possible.

Tasks:
- Inspect backend/main.py, backend/app/, docker-compose.yml, backend/requirements.txt, and current README setup notes.
- Create a cleaner backend structure only as much as needed.
- Remove the import-time requirement for a real OpenAI key.
- Fix the Docker/backend port mismatch.
- Enable SQLite WAL for local SQLite.
- Add pytest smoke tests for health, read endpoints, validation errors, and quiz result persistence.
- Run backend tests.
- Update docs/STATUS.md with what changed and what passed or failed.

Do not start RAG implementation yet.
```

## Day 2 Prompt: Real RAG Layer

```text
Start Day 2 of the LearnLoop revamp: real session-based RAG.

Goal:
Implement in-memory FAISS retrieval using local all-MiniLM-L6-v2 embeddings and 512-token chunking.

Tasks:
- Read docs/STATUS.md, docs/WEEK_PLAN.md, and docs/DECISIONS.md.
- Inspect the backend structure from Day 1.
- Add study material ingestion.
- Add 512-token chunking with overlap.
- Add local embedding generation.
- Add per-session in-memory FAISS indexes.
- Add retrieval endpoint returning top-k chunks and retrieval latency.
- Add source-grounded answer generation using retrieved chunks.
- Add tests for chunking, retrieval, and session isolation.
- Update docs/STATUS.md.

Keep frontend changes minimal unless needed for smoke testing.
```

## Day 3 Prompt: Benchmark Evidence

```text
Start Day 3 of the LearnLoop revamp: retrieval benchmark evidence.

Goal:
Measure Recall@5 and retrieval latency with reproducible evidence.

Tasks:
- Read docs/STATUS.md and inspect the RAG implementation.
- Add a small benchmark dataset with questions and expected source chunks.
- Add a rerunnable evaluation command.
- Measure Recall@5 and p50/p95 retrieval latency.
- Save benchmark results under docs/benchmarks/.
- Update README only with measured numbers.
- Update docs/STATUS.md.

Do not invent or round metrics beyond what the report supports.
```

## Day 4 Prompt: Pydantic Self-Healing Generation

```text
Start Day 4 of the LearnLoop revamp: Pydantic self-healing quiz and flashcard generation.

Goal:
Replace regex-only JSON cleanup with schema validation and bounded repair retries.

Tasks:
- Read docs/STATUS.md and inspect quiz/flashcard generation code.
- Add Pydantic schemas for quiz and flashcard outputs.
- Validate model output.
- Retry malformed or schema-invalid output with validation feedback.
- Add tests for valid output, malformed JSON, schema-invalid JSON, and retry exhaustion.
- Update docs/STATUS.md.

Keep the user-facing API shape stable unless a change is necessary and documented.
```

## Day 5 Prompt: Load Testing And WAL

```text
Start Day 5 of the LearnLoop revamp: load testing and SQLite WAL validation.

Goal:
Make the 500 simulated user load-test claim real and documented.

Tasks:
- Read docs/STATUS.md and docs/DEPLOYMENT.md.
- Add Locust tests for realistic app flows.
- Include read-heavy and write-heavy endpoints.
- Run a 500-user test locally or with Docker.
- Capture failure rate, throughput, p50 latency, and p95 latency.
- Save reports under docs/load-tests/.
- Document SQLite WAL behavior and any lock errors.
- Update docs/STATUS.md.

Do not hide failures. If the app does not handle the target load, report the bottleneck and smallest fix.
```

## Day 6 Prompt: Frontend Redesign

```text
Start Day 6 of the LearnLoop revamp: complete frontend redesign.

Goal:
Build a modern, usable study workspace around the now-real backend workflows.

Tasks:
- Read docs/STATUS.md, docs/WEEK_PLAN.md, and current frontend source.
- Decide whether to migrate CRA to Vite or redesign in place.
- Redesign the main experience around sessions, material ingestion, RAG chat, source snippets, quiz generation, flashcards, and analytics.
- Add loading, empty, error, and success states.
- Remove stale boilerplate tests and add useful frontend tests.
- Run frontend tests and production build.
- Update docs/STATUS.md.

Do not create a marketing landing page. The first screen should be the actual app experience.
```

## Day 7 Prompt: Accounts And PDF Sources

```text
Start Day 7 of the LearnLoop revamp: accounts and PDF sources.

Goal:
Add PDF sources and account-aware study flows while preserving a usable guest mode.

Tasks:
- Read docs/STATUS.md, docs/WEEK_PLAN.md, docs/DECISIONS.md, and the current frontend/backend source.
- Add PDF upload and selectable-text extraction with session-scoped indexing.
- Allow PDF and pasted text to be added to the same learning space.
- Add Supabase email/password authentication, account navigation, and verified backend tokens.
- Keep guest sessions available without an account and show the guided demo only to guests.
- Add account isolation tests and styled account/source-management states.
- Provision the Supabase schema with RLS and avoid adding a durable source table.
- Record any remaining source-persistence or privacy gap honestly in docs/STATUS.md.

Do not start deployment in this phase. Verify the complete local account, guest, PDF, question, quiz, and flashcard flows first.
```

## Day 8 Prompt: Deployment Compatibility And Production Deployment

```text
Start Day 8 of the LearnLoop revamp: deployment compatibility and production deployment.

Goal:
Deploy the completed core app before adding additional product features.

Tasks:
- Read docs/STATUS.md, docs/WEEK_PLAN.md, docs/DECISIONS.md, and docs/DEPLOYMENT.md.
- Inspect the completed Days 1-7 implementation, especially RAG, embeddings, FAISS indexes, answer generation, account configuration, frontend API config, Docker, and load tests.
- Revisit whether Render should run sentence-transformers in-process or call a remote embedding service.
- Add a provider boundary if needed so local development can use local MiniLM while deployment can use Modal or another remote embedding provider.
- Document memory, cold-start, persistence, scale-out, and model-download tradeoffs.
- Update deployment config and docs for Vercel, Render, and Modal if Modal is selected.
- Deploy the backend to Render or the selected backend host.
- Deploy the frontend to Vercel or the selected frontend host.
- Deploy the embedding/model service to Modal if the deployment architecture uses it.
- Configure production environment variables and CORS for the deployed frontend/backend connection.
- Verify the deployed app end-to-end from the public frontend URL.
- Make Locust testing target the deployable architecture, or clearly document local-only limits.
- Run backend tests, frontend tests, production build, and relevant benchmark/load-test commands.
- Update docs/STATUS.md with deployment URLs, verification commands, results, and remaining risks.

Do not add extra product features in this phase. The end goal is actual deployment of the core app, not just deployment planning.
```

## Day 9 Prompt: Additional Product Features

```text
Start Day 9 of the LearnLoop revamp: additional impressive product features.

Goal:
Brainstorm and implement 2-3 features that make the app more useful and stronger for resume discussion, after production deployment has been completed.

Tasks:
- Read docs/STATUS.md and inspect the completed Days 1-8 implementation.
- Brainstorm feature candidates and explain tradeoffs.
- Choose the best 2-3 based on user value, implementation time, and resume impact.
- Implement the selected features end-to-end.
- Add tests where appropriate.
- Update README and docs/STATUS.md with only verified claims.

Candidate areas:
- adaptive review
- topic mastery tracking
- spaced repetition
- Anki or CSV export
- source-cited study summaries
- shareable study packs
- per-session learning timeline
```

## Standard Verification Prompt

```text
Verify the current LearnLoop revamp state.

Run the relevant backend tests, frontend tests, frontend build, and any benchmark or load-test commands that apply to the current phase. Then summarize:
- what passed
- what failed
- what was not run and why
- whether docs/STATUS.md matches the actual current state
```

# LearnLoop Revamp Decisions

This file records architecture and product decisions made during the revamp. Keep each entry short, concrete, and tied to implementation evidence.

## Current Baseline

- The backend started as a single Flask app in `backend/thinkmate.py`.
- Day 1 split the backend into a minimal Flask package under `backend/app/` and renamed the stale backend entry point to `backend/main.py`.
- The frontend is Create React App with React 19 and `react-scripts`.
- Persistence is currently SQLAlchemy with SQLite fallback and optional Supabase URI.
- The checked-in SQLite DB contains existing conversation, quiz, and flashcard records.
- Day 2 adds session-scoped in-memory FAISS retrieval with local `all-MiniLM-L6-v2` embeddings.
- There is no retrieval benchmark, Locust test, or Pydantic validation loop yet.

## Decisions

### 1. Stabilize the backend before redesigning the frontend

Decision: Phase 1 will focus on backend structure, testability, Docker correctness, and SQLite WAL before adding new user-facing workflows.

Reason: The resume claims depend on backend behavior. A frontend redesign before real RAG, validation, and load testing would make the app look better without making the technical claims true.

### 2. Keep local development privacy-first

Decision: The RAG layer will use local `all-MiniLM-L6-v2` embeddings and in-memory FAISS indexes scoped by session.

Reason: This directly supports the privacy and session-isolation claim. It also keeps retrieval fast and avoids sending raw study material to a vector database service.

### 3. Measure before claiming benchmark numbers

Decision: Recall@5, retrieval latency, malformed JSON rate, and load-test results must be measured and saved before appearing in README or resume wording.

Reason: The project should exceed the existing resume claims with traceable evidence, not approximate or fabricated numbers.

### 4. Replace regex-only JSON cleanup with schema validation

Decision: Quiz and flashcard generation will use Pydantic schemas plus a bounded repair loop.

Reason: Current regex cleanup handles only simple formatting problems. Schema validation is more defensible and lets us report actual malformed-output recovery behavior.

### 5. Defer full frontend redesign until backend workflows are real

Decision: Phase 6 is the complete frontend redesign. Earlier phases may add small UI hooks only when needed to test backend workflows.

Reason: The final interface should be designed around the real study workspace, source-grounded answers, quiz generation, flashcards, and analytics.

### 6. Add a feature-expansion phase after the core claims are real

Decision: Phase 8 will add additional high-value product features after the baseline revamp, RAG, validation, load testing, redesign, and production deployment phases are complete.

Reason: Extra features should build on stable and deployed foundations. We will brainstorm exact Phase 8 scope later, but candidates include adaptive review, exports, source citations, topic mastery tracking, and shareable study packs.

### 7. Work directly on main for this revamp

Decision: Subsequent commits should be made directly on `main` and pushed to `origin/main`; do not create feature branches unless explicitly requested later.

Reason: The user wants a seamless linear workflow for this project instead of branch-and-merge coordination.

### 8. Use logical multi-commit history with explanatory messages

Decision: Keep commits logically separate and use commit messages with a concise subject plus a short body explaining what changed and why.

Reason: Separate commits make review and rollback easier. The body should preserve the reasoning behind each change without making the subject line noisy.

### 9. Use `main.py` as the backend entry point

Decision: The backend now uses `backend/app/` for factory, models, routes, and services, with `backend/main.py` as the executable entry point.

Reason: `thinkmate.py` was stale project branding. `main.py` is a standard backend entry-point name and keeps Docker/local startup aligned with the LearnLoop project name.

### 10. Deploy the core app before feature expansion

Decision: Phase 7 will make the completed core app deployment-compatible and deploy it before Phase 8 product work starts.

Reason: Render, Vercel, and any separate model service must be validated against the real RAG and load-test architecture before additional features expand the deployment surface.

### 11. Preserve 512-token retrieval chunks across MiniLM windows

Decision: RAG chunks use the MiniLM tokenizer for 512-token boundaries with 64-token overlap. Embeddings are pooled across model-sized windows so all chunk tokens contribute despite the model's 256-token sequence limit.

Reason: Sending a 512-token chunk directly to `all-MiniLM-L6-v2` silently truncates content after its usable sequence limit and weakens retrieval for information near the end of the chunk.

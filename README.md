# 📚 LearnLoop: Your Personal AI Study Companion

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-🐳-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

</div>

**LearnLoop is a source-grounded study workspace. Learners organize material into persistent journeys, ask questions backed by retrieved evidence, generate validated quizzes and flashcards from the same sources, and review saved progress.**

---

## Deployment status

The redesigned Day 6 application is complete and verified locally. The previous
public deployment does not represent this redesign. Day 7 covers deployment
compatibility, public hosting, and end-to-end verification of the refreshed app.

---

## 💡 My Motivation & Vision

As a lifelong learner and now a data science student, I constantly felt the friction of juggling multiple study tools. I had one app for notes, another for flashcards, a separate website for practice quizzes, and chatbots that felt disconnected from my actual course material. I wanted to build a single "learning command center" where I could:

1. **Ground questions** in study material I provide.
2. **Quiz myself** on specific concepts or pasted text, with saved feedback.
3. **Generate flashcards** from the same learning journey.
4. **Review progress and history** without losing the connection to source material.

> LearnLoop connects source-grounded study, practice, and review in one persistent workspace.

---

## ✨ Key Features

The redesigned product is organized around one connected study journey:

1. **Grounded Study**
   - Add text material to a persistent journey.
   - Ask questions answered from retrieved source chunks.
   - Inspect the material supporting each grounded answer.

2. **Validated Practice**
   - Generate mixed-format quizzes from a journey, topic, or pasted content.
   - Review saved scores, answers, and explanations.
   - Generate flashcards from the same session material.

3. **Progress And History**
   - View real quiz score trends and topic-level averages.
   - Resume sessions and reopen saved quiz or flashcard artifacts.
   - Explore a resettable Machine Learning Foundations demo journey.

4. **Technical Benchmarks**
   - Review checked-in retrieval quality and latency measurements.
   - Inspect the 500-user local load-test result with its environment limitations.

---

## 🛠️ Tech Stack & Design Choices

| Layer       | Technology              | Rationale                                                    |
| ----------- | ----------------------- | ------------------------------------------------------------ |
| **Language** | Python / JavaScript     | Python for a lightweight API; JS/React for a dynamic UI.       |
| **Framework** | Flask / React           | Flask’s simplicity is perfect for an API; React’s component model is ideal for the UI. |
| **AI Client** | `openai-python`         | The official, easy-to-integrate client for OpenAI models.      |
| **Database** | SQLite (for local dev)  | Zero-setup local persistence in a single `conversations.db` file. |
| **HTTP** | REST + JSON             | Simple, universal, and works perfectly with `axios` and Flask. |
| **Styling** | Custom responsive CSS   | A compact design system without a heavy component dependency. |
| **Container** | Docker Compose          | Allows spinning up the entire full-stack environment with a single command. |

---

## 🚀 Getting Started Locally

This project is fully containerized with Docker for a simple setup.

### Prerequisites

-   Docker and Docker Compose installed.
-   An OpenAI API Key.

### Setup Instructions

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/MohammedPathariya/LearnLoop.git
    cd LearnLoop
    ```
2.  **Configure Your API Key**
    -   Copy `backend/.env.example` to `backend/.env` and fill in the values. Keep `backend/.env` local and never commit it.
    -   Add your OpenAI API key to this file:
        ```
        OPENAI_API_KEY=sk-YourSecretKeyHere
        ```
3.  **Build and Run with Docker Compose**
    -   From the root directory of the project, run:
        ```bash
        docker compose up --build
        ```
    -   This command will build the images for both the frontend and backend, install all dependencies, and start the services.

5.  **Access the Application**
    -   **Frontend:** Open your browser and go to `http://localhost:3000`
    -   **Backend API:** The backend will be running on `http://localhost:5050`

---

## 🧗 Key Challenges & Solutions

Developing this project involved solving several interesting technical hurdles:

1.  **Challenge: Unreliable JSON from AI**
    -   **Problem:** The GPT model could return malformed or structurally invalid quiz and flashcard JSON.
    -   **Solution:** Generation now validates model output with Pydantic schemas and sends validation feedback through at most two repair retries. Exhausted retries return a clear error instead of being treated as successful generation.

2.  **Challenge: Losing Data in Docker**
    -   **Problem:** The SQLite database file (`conversations.db`) was being created inside the Docker container, so it was deleted every time the container was rebuilt.
    -   **Solution:** I used a Docker **bind mount** to map the `./backend` directory on my local machine to the `/code/backend` directory inside the container. This ensures the `.db` file persists on my machine, surviving container rebuilds.

3.  **Challenge: Uniform Styling**
    -   **Problem:** I wanted a consistent layout with a side-panel accent across multiple pages without duplicating CSS.
    -   **Solution:** I created a shared `.page-bg-wrapper` CSS class snippet and wrapped every main page component in it, ensuring a consistent look and feel with minimal code.

---

## 🎯 Future Work & Vision

## Retrieval benchmark

The active retrieval comparison contains three named tests. The synthetic near-neighbor Recall@3 test measured `1.0` (13/13), with `6.591 ms` p50 and `8.5436 ms` p95 latency. The real project corpus Recall@3 test uses seven implementation and project files, 25 indexed chunks, and 10 manually labeled questions; it measured `0.6` (6/10), with `6.304 ms` p50 and `9.2693 ms` p95 latency. The same real corpus at Recall@5 measured `0.9` (9/10), with `6.146 ms` p50 and `10.2577 ms` p95 latency. These measurements exclude ingestion and are backed by [`docs/benchmarks/README.md`](docs/benchmarks/README.md), [`docs/benchmarks/synthetic_near_neighbor_recall_at_3.json`](docs/benchmarks/synthetic_near_neighbor_recall_at_3.json), [`docs/benchmarks/real_project_recall_at_3.json`](docs/benchmarks/real_project_recall_at_3.json), and [`docs/benchmarks/real_project_recall_at_5.json`](docs/benchmarks/real_project_recall_at_5.json). The initial v1 and v2 exploratory tests remain in [`docs/benchmarks/archive/`](docs/benchmarks/archive/).

Rerun it with the cached embedding model:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=backend python3.11 scripts/evaluate_retrieval.py
```

Run the synthetic near-neighbor Recall@3 test:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=backend python3.11 scripts/evaluate_retrieval.py --dataset docs/benchmarks/archive/retrieval_dataset_v2.json --report docs/benchmarks/synthetic_near_neighbor_recall_at_3.json --benchmark-name 'LearnLoop synthetic near-neighbor Recall@3' --top-k 3
```

Run Recall@3 on the real project corpus:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=backend python3.11 scripts/evaluate_retrieval.py --dataset docs/benchmarks/real_project_corpus.json --report docs/benchmarks/real_project_recall_at_3.json --benchmark-name 'LearnLoop real project corpus Recall@3' --top-k 3
```

Run Recall@5 on the same real project corpus:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=backend python3.11 scripts/evaluate_retrieval.py --dataset docs/benchmarks/real_project_corpus.json --report docs/benchmarks/real_project_recall_at_5.json --benchmark-name 'LearnLoop real project corpus Recall@5' --top-k 5
```

-   **User Accounts & Auth:** Implement user authentication so learners can have private, secure notebooks and track their progress over time.
-   **Export & Share:** Add functionality to export flashcard sets as CSVs or share quiz results with classmates via a link.
-   **Adaptive Learning:** Track a user's weak topics based on quiz performance and automatically generate targeted review quizzes.
-   **Enhanced Analytics:** Build out more detailed progress graphs, topic heatmaps, and time-to-complete metrics.

---
<div align="center">
Made with ❤️ and lots of ☕ by Mohammed
</div>

# 📚 LearnLoop: Your Personal AI Study Companion

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.2-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-🐳-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

</div>

**LearnLoop is an integrated, AI-powered web application designed to be a one-stop-shop for studying. It combines an interactive chatbot, a quiz generator, and a flashcard creator into a single, cohesive learning experience.**

---

## 💡 My Motivation & Vision

As a lifelong learner and now a data science student, I constantly felt the friction of juggling multiple study tools. I had one app for notes, another for flashcards, a separate website for practice quizzes, and chatbots that felt disconnected from my actual course material. I wanted to build a single "learning command center" where I could:

1.  **Interact** with any topic through a natural, student-teacher dialogue.
2.  **Quiz myself** on specific concepts or pasted text, with instant feedback.
3.  **Generate flashcards** for quick, on-the-fly review sessions.
4.  **Review past sessions** so that no learning progress is ever lost.

> The goal of LearnLoop was to blend **conversation**, **testing**, and **memory aids** into one seamless web experience—powered by AI, but packaged in a way that feels intuitive and focused.

---

## ✨ Key Features

This project is organized into three core, interconnected modules:

1.  **🧠 ThinkMate Chat**
    -   Engage in a dynamic student-teacher dialogue on any subject.
    -   Control the AI's tone (natural, formal, humorous, technical) and who starts the conversation.
    -   Every conversation is automatically saved with a timestamp and topic for later review.

2.  **📝 Quiz Builder**
    -   Instantly generate mixed-type quizzes (Multiple Choice, True/False, Fill-in-the-Blank) from any topic or pasted content.
    -   Answer questions in an interactive UI with immediate scoring and explanations.
    -   All quiz sessions are persisted, tracking your scores and showing a full history with analytics.

3.  **📇 Flashcard Generator**
    -   Create sets of topic-focused flashcards with a term and a definition.
    -   Review your cards with a simple, responsive click-to-flip grid layout.
    -   All generated sets are saved for future study sessions.

4.  **📊 Dashboard & Analytics**
    -   View aggregate stats: total chats, quizzes taken, average scores, and more.
    -   Easily navigate between recent activities and a complete history.
    -   A minimal, professional design keeps the focus on your learning progress.

---

## 🛠️ Tech Stack & Design Choices

| Layer       | Technology              | Rationale                                                    |
| ----------- | ----------------------- | ------------------------------------------------------------ |
| **Language** | Python / JavaScript     | Python for a lightweight API; JS/React for a dynamic UI.       |
| **Framework** | Flask / React           | Flask’s simplicity is perfect for an API; React’s component model is ideal for the UI. |
| **AI Client** | `openai-python`         | The official, easy-to-integrate client for OpenAI models.      |
| **Database** | SQLite (for local dev)  | Zero-setup local persistence in a single `conversations.db` file. |
| **HTTP** | REST + JSON             | Simple, universal, and works perfectly with `axios` and Flask. |
| **Styling** | CSS Modules + Flexbox   | A custom look with minimal dependencies, avoiding heavy UI libraries. |
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
    git clone
    cd learnloop
    ```
2.  **Configure Your API Key**
    -   In the `backend/` directory, create a new file named `.env`.
    -   Add your OpenAI API key to this file:
        ```
        OPENAI_API_KEY=sk-YourSecretKeyHere
        ```
3.  **Build and Run with Docker Compose**
    -   Install dependencies: `pip install -r requirements.txt`
    -   From the root directory of the project, run:
        ```bash
        docker compose up --build
        ```
    -   This command will build the images for both the frontend and backend, install all dependencies, and start the services.

5.  **Access the Application**
    -   **Frontend:** Open your browser and go to `http://localhost:3000`
    -   **Backend API:** The backend will be running on `http://localhost:5000`

---

## 🧗 Key Challenges & Solutions

Developing this project involved solving several interesting technical hurdles:

1.  **Challenge: Unreliable JSON from AI**
    -   **Problem:** The GPT model would sometimes return JSON with formatting errors, like trailing commas, which would break the Python `json.loads` parser.
    -   **Solution:** I implemented a pre-processing step using a regular expression to clean up the JSON string before parsing. I also added `try...except` blocks to gracefully handle any remaining errors and report them.

2.  **Challenge: Losing Data in Docker**
    -   **Problem:** The SQLite database file (`conversations.db`) was being created inside the Docker container, so it was deleted every time the container was rebuilt.
    -   **Solution:** I used a Docker **bind mount** to map the `./backend` directory on my local machine to the `/code/backend` directory inside the container. This ensures the `.db` file persists on my machine, surviving container rebuilds.

3.  **Challenge: Uniform Styling**
    -   **Problem:** I wanted a consistent layout with a side-panel accent across multiple pages without duplicating CSS.
    -   **Solution:** I created a shared `.page-bg-wrapper` CSS class snippet and wrapped every main page component in it, ensuring a consistent look and feel with minimal code.

---

## 🎯 Future Work & Vision

-   **User Accounts & Auth:** Implement user authentication so learners can have private, secure notebooks and track their progress over time.
-   **Export & Share:** Add functionality to export flashcard sets as CSVs or share quiz results with classmates via a link.
-   **Adaptive Learning:** Track a user's weak topics based on quiz performance and automatically generate targeted review quizzes.
-   **Enhanced Analytics:** Build out more detailed progress graphs, topic heatmaps, and time-to-complete metrics.

---
<div align="center">
Made with ❤️ and lots of ☕ by Mohammed
</div>


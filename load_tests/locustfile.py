import os
import random

from locust import HttpUser, between, task


QUIZ = {
    "type": "MCQ",
    "question": "What does SQLite WAL mode allow?",
    "options": [
        "A. Readers and a writer to proceed concurrently",
        "B. Multiple writers at the same time",
        "C. Queries without a database file",
        "D. Writes without transactions",
    ],
    "answer": "A",
    "explanation": "WAL lets readers continue while a writer appends to the log.",
}


class LearnLoopUser(HttpUser):
    """Exercise the non-LLM study history flow used by the frontend."""

    wait_time = between(0.2, 1.0)

    def on_start(self):
        self.quiz_result_id = None

    @task(5)
    def read_dashboard(self):
        for path in (
            "/history",
            "/analytics/stats",
            "/quiz_history",
            "/analytics/quiz_stats",
            "/flashcards_history",
            "/analytics/flashcard_stats",
        ):
            self.client.get(path, name=path)

    @task(3)
    def search_history(self):
        query = random.choice(("WAL", "indexes", "biology", "database"))
        self.client.get("/search", params={"query": query}, name="/search")

    @task(2)
    def save_and_read_quiz_result(self):
        payload = {
            "topic": f"load-test-{os.getpid()}",
            "num_questions": 1,
            "quiz": [QUIZ],
            "user_answers": {"0": "A"},
            "correct_answers": ["A"],
            "score": 1,
        }
        response = self.client.post("/quiz_results", json=payload, name="POST /quiz_results")
        if response.status_code != 201:
            return

        self.quiz_result_id = response.json()["quiz_session_id"]
        self.client.get(
            f"/quiz_results/{self.quiz_result_id}",
            name="GET /quiz_results/:id",
        )

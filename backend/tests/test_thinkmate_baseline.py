import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def thinkmate_app(tmp_path, monkeypatch):
    db_path = tmp_path / "learnloop-test.db"
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SUPABASE_DB_URI", f"sqlite:///{db_path}")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))

    sys.modules.pop("thinkmate", None)
    module = importlib.import_module("thinkmate")

    with module.app.app_context():
        module.db.create_all()

    yield module

    with module.app.app_context():
        module.db.session.remove()
        module.db.drop_all()


@pytest.fixture()
def client(thinkmate_app):
    return thinkmate_app.app.test_client()


def test_healthz_returns_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.data.decode() == "OK"


def test_empty_database_read_endpoints_return_success(client):
    endpoints = [
        "/history",
        "/analytics/stats",
        "/quiz_history",
        "/analytics/quiz_stats",
        "/flashcards_history",
        "/analytics/flashcard_stats",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        assert response.status_code == 200


def test_missing_generation_inputs_return_validation_errors(client):
    checks = [
        ("/chat", {"error": "Missing 'topic'"}),
        ("/quiz", {"error": "Provide either 'topic' or 'content'"}),
        ("/flashcards", {"error": "Missing 'topic'"}),
    ]

    for endpoint, expected_body in checks:
        response = client.post(endpoint, json={})

        assert response.status_code == 400
        assert response.get_json() == expected_body


def test_quiz_result_can_be_saved_and_fetched(client):
    payload = {
        "topic": "database indexes",
        "num_questions": 1,
        "quiz": [
            {
                "type": "MCQ",
                "question": "What does an index improve?",
                "options": ["A. Reads", "B. Syntax", "C. Imports", "D. Formatting"],
                "answer": "A",
                "explanation": "Indexes speed up lookups for matching rows.",
            }
        ],
        "user_answers": {"0": "A"},
        "correct_answers": ["A"],
        "score": 1,
    }

    save_response = client.post("/quiz_results", json=payload)

    assert save_response.status_code == 201
    quiz_session_id = save_response.get_json()["quiz_session_id"]

    fetch_response = client.get(f"/quiz_results/{quiz_session_id}")

    assert fetch_response.status_code == 200
    body = fetch_response.get_json()
    assert body["topic"] == "database indexes"
    assert body["score"] == 1
    assert body["quiz"][0]["question"] == "What does an index improve?"


def test_empty_search_query_returns_empty_list(client):
    response = client.get("/search?query=")

    assert response.status_code == 200
    assert response.get_json() == []

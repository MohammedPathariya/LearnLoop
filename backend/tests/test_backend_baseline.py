import importlib
import sys
from pathlib import Path

import pytest
from sqlalchemy import text


@pytest.fixture()
def backend_app(tmp_path, monkeypatch):
    db_path = tmp_path / "learnloop-test.db"
    monkeypatch.setenv("SUPABASE_DB_URI", f"sqlite:///{db_path}")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))

    sys.modules.pop("main", None)
    module = importlib.import_module("main")

    with module.app.app_context():
        module.db.create_all()

    yield module

    with module.app.app_context():
        module.db.session.remove()
        module.db.drop_all()


@pytest.fixture()
def client(backend_app):
    return backend_app.app.test_client()


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
        ("/flashcards", {"error": "Provide either 'topic', 'content', or 'session_id'"}),
    ]

    for endpoint, expected_body in checks:
        response = client.post(endpoint, json={})

        assert response.status_code == 400
        assert response.get_json() == expected_body


def test_generation_count_ranges_are_validated(client):
    quiz_response = client.post(
        "/quiz",
        json={"topic": "biology", "num_questions": 0},
    )
    flashcard_response = client.post(
        "/flashcards",
        json={"topic": "biology", "num_cards": 11},
    )

    assert quiz_response.status_code == 400
    assert quiz_response.get_json() == {"error": "num_questions must be between 1 and 20"}
    assert flashcard_response.status_code == 400
    assert flashcard_response.get_json() == {"error": "num_cards must be between 1 and 10"}


def test_generation_failures_return_bad_gateway(client, monkeypatch):
    from app import routes

    failure = {
        "error": "Generated output failed validation after repair retries",
        "raw_output": "not json",
        "validation_errors": "invalid JSON",
        "validation_attempts": 3,
    }
    monkeypatch.setattr(routes, "generate_quiz", lambda **_: failure)
    monkeypatch.setattr(routes, "generate_flashcards", lambda *_args, **_: failure)

    quiz_response = client.post("/quiz", json={"topic": "biology"})
    flashcard_response = client.post("/flashcards", json={"topic": "biology"})

    assert quiz_response.status_code == 502
    assert flashcard_response.status_code == 502
    assert quiz_response.get_json() == failure
    assert flashcard_response.get_json() == failure


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


def test_openai_key_is_not_required_to_import_backend(tmp_path, monkeypatch):
    db_path = tmp_path / "learnloop-no-key.db"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_DB_URI", f"sqlite:///{db_path}")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))

    sys.modules.pop("main", None)
    module = importlib.import_module("main")

    response = module.app.test_client().get("/healthz")

    assert response.status_code == 200


def test_sqlite_uses_wal_journal_mode(backend_app):
    with backend_app.app.app_context():
        journal_mode = backend_app.db.session.execute(text("PRAGMA journal_mode")).scalar()

    assert journal_mode == "wal"


def test_wsgi_entrypoint_creates_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "learnloop-wsgi.db"
    monkeypatch.setenv("SUPABASE_DB_URI", f"sqlite:///{db_path}")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))

    sys.modules.pop("wsgi", None)
    module = importlib.import_module("wsgi")

    with module.app.app_context():
        table_name = module.db.session.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'quiz_session'"
            )
        ).scalar()

    assert table_name == "quiz_session"

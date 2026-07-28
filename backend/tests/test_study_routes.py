import importlib
import sys
from pathlib import Path

import pytest


VISITOR_HEADERS = {"X-LearnLoop-Visitor": "visitor-a"}


@pytest.fixture()
def backend_app(tmp_path, monkeypatch):
    db_path = tmp_path / "learnloop-study-test.db"
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


def test_demo_journey_is_seeded_and_isolated(client):
    response = client.post("/study/demo", headers=VISITOR_HEADERS)

    assert response.status_code == 200
    demo = response.get_json()
    assert demo["title"] == "Machine Learning Foundations"
    assert demo["is_demo"] is True
    assert demo["material_count"] == 3
    assert demo["quiz_count"] == 3
    assert demo["flashcard_count"] == 1

    own_sessions = client.get("/study/sessions", headers=VISITOR_HEADERS).get_json()
    other_sessions = client.get(
        "/study/sessions",
        headers={"X-LearnLoop-Visitor": "visitor-b"},
    ).get_json()

    assert [session["id"] for session in own_sessions] == [demo["id"]]
    assert other_sessions == []
    assert client.get(
        f"/study/sessions/{demo['id']}",
        headers={"X-LearnLoop-Visitor": "visitor-b"},
    ).status_code == 404


def test_session_and_material_crud(client, monkeypatch):
    from app import study_routes

    monkeypatch.setattr(
        study_routes,
        "ingest_study_material",
        lambda **_: {"chunks_indexed": 2, "total_chunks": 2},
    )
    session_response = client.post(
        "/study/sessions",
        headers=VISITOR_HEADERS,
        json={"title": "Statistics", "domain": "Data Science"},
    )
    session = session_response.get_json()

    material_response = client.post(
        f"/study/sessions/{session['id']}/materials",
        headers=VISITOR_HEADERS,
        json={"title": "Confidence intervals", "content": "A confidence interval estimates a population parameter."},
    )
    material = material_response.get_json()

    assert session_response.status_code == 201
    assert material_response.status_code == 201
    assert material["status"] == "indexed"
    assert material["chunk_count"] == 2

    renamed = client.patch(
        f"/study/materials/{material['id']}",
        headers=VISITOR_HEADERS,
        json={"title": "Interval estimates"},
    ).get_json()
    assert renamed["title"] == "Interval estimates"

    deleted = client.delete(
        f"/study/materials/{material['id']}",
        headers=VISITOR_HEADERS,
    )
    assert deleted.status_code == 200
    assert client.get(
        f"/study/sessions/{session['id']}/materials",
        headers=VISITOR_HEADERS,
    ).get_json() == []


def test_grounded_question_is_saved_with_sources(client, monkeypatch):
    from app import study_routes

    demo = client.post("/study/demo", headers=VISITOR_HEADERS).get_json()
    source = demo["materials"][0]
    monkeypatch.setattr(study_routes, "_ensure_session_index", lambda _: None)
    monkeypatch.setattr(
        study_routes,
        "retrieve_chunks",
        lambda *_args, **_kwargs: {
            "chunks": [{
                "id": f"{source['id']}:0",
                "source_id": source["id"],
                "session_id": demo["id"],
                "chunk_index": 0,
                "text": "Generalization is performance on unseen data.",
                "token_count": 7,
                "score": 0.91,
            }],
            "latency_ms": 6.2,
        },
    )
    monkeypatch.setattr(
        study_routes,
        "generate_grounded_answer",
        lambda *_args: "Generalization measures performance on unseen data. [Source 1]",
    )

    response = client.post(
        f"/study/sessions/{demo['id']}/ask",
        headers=VISITOR_HEADERS,
        json={"question": "What is generalization?"},
    )

    assert response.status_code == 201
    answer = response.get_json()
    assert answer["grounded"] is True
    assert answer["source_count"] == 1
    assert answer["sources"][0]["title"] == source["title"]

    messages = client.get(
        f"/study/sessions/{demo['id']}/messages",
        headers=VISITOR_HEADERS,
    ).get_json()
    assert messages[-2]["role"] == "user"
    assert messages[-1]["role"] == "assistant"


def test_demo_progress_and_history_use_saved_artifacts(client):
    client.post("/study/demo", headers=VISITOR_HEADERS)

    progress = client.get("/study/progress", headers=VISITOR_HEADERS).get_json()
    history = client.get("/study/history", headers=VISITOR_HEADERS).get_json()

    assert progress["quizzes"] == 3
    assert progress["average_score"] == 80
    assert progress["strong_topics"][0]["topic"] == "Generalization"
    assert progress["needs_review"][0]["topic"] == "Evaluation metrics"
    assert {item["type"] for item in history} == {"session", "quiz", "flashcards"}

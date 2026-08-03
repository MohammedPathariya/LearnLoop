import json
from datetime import datetime, timedelta
import uuid

from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .auth import current_user
from .models import (
    FlashcardSet,
    QuizSession,
    SessionFlashcardLink,
    SessionQuizLink,
    StudyMaterial,
    StudyMessage,
    StudySession,
)
from .services.generation import generate_grounded_answer
from .services.rag import (
    clear_session_index,
    ingest_study_material,
    retrieve_chunks,
)
from .services.vector_store import get_vector_store
from .services.pdf import extract_pdf_text
from .services.pdf_sources import clear_sources, get_source, get_sources, register_source, remove_source


DEMO_TITLE = "Machine Learning Foundations"
DEMO_DOMAIN = "Machine Learning"
DEMO_RESET_AFTER = timedelta(hours=24)

DEMO_MATERIALS = [
    {
        "title": "Generalization and the bias-variance tradeoff",
        "content": (
            "A supervised learning model learns a mapping from labeled examples. "
            "Generalization describes how well that learned mapping performs on unseen data. "
            "Underfitting occurs when a model is too simple to capture useful patterns, producing "
            "high bias on both training and validation data. Overfitting occurs when a model learns "
            "training-specific noise, producing low training error but high validation error. "
            "Regularization discourages excessive complexity. L1 regularization can drive some "
            "coefficients to zero, while L2 regularization shrinks coefficients smoothly. "
            "The bias-variance tradeoff describes the balance between systematic error from an "
            "overly simple model and sensitivity to fluctuations in the training sample."
        ),
    },
    {
        "title": "Evaluation, splitting, and cross-validation",
        "content": (
            "Training data is used to fit model parameters. Validation data supports model and "
            "hyperparameter selection. Test data should remain untouched until the final evaluation. "
            "Using the test set repeatedly during development leaks evaluation information into model "
            "selection. K-fold cross-validation divides the available training data into k folds, "
            "trains on k minus one folds, and validates on the remaining fold. Classification accuracy "
            "can be misleading for imbalanced data. Precision measures the fraction of predicted "
            "positives that are correct. Recall measures the fraction of actual positives found. "
            "F1 is the harmonic mean of precision and recall."
        ),
    },
    {
        "title": "Data leakage and reliable pipelines",
        "content": (
            "Data leakage occurs when information unavailable at prediction time influences model "
            "training or evaluation. Target leakage happens when a feature directly or indirectly "
            "reveals the label. Train-test contamination happens when preprocessing learns from the "
            "full dataset before the split. Scaling, imputation, feature selection, and resampling "
            "should be fitted only on training data. A pipeline keeps preprocessing and modeling "
            "steps together so cross-validation applies every learned transformation inside each "
            "training fold. Time-dependent data requires chronological splitting rather than random "
            "splitting when future information must not influence past predictions."
        ),
    },
]

DEMO_MESSAGES = [
    {
        "role": "user",
        "content": "Why can accuracy be misleading on an imbalanced classification problem?",
        "grounded": False,
        "sources": [],
    },
    {
        "role": "assistant",
        "content": (
            "A model can achieve high accuracy by predicting the majority class most of the time "
            "while missing the minority class you care about. Precision, recall, and F1 expose those "
            "errors more clearly. For example, recall shows how many actual positive cases the model found."
        ),
        "grounded": True,
        "sources": [
            {
                "source_id": "demo-evaluation",
                "title": "Evaluation, splitting, and cross-validation",
                "chunk_index": 0,
            }
        ],
        "latency": 6.146,
    },
    {
        "role": "user",
        "content": "What is the safest way to prevent preprocessing leakage?",
        "grounded": False,
        "sources": [],
    },
    {
        "role": "assistant",
        "content": (
            "Put preprocessing and the model in one pipeline, then run cross-validation on that "
            "pipeline. Each fold fits scaling, imputation, feature selection, and similar steps only "
            "on its training portion."
        ),
        "grounded": True,
        "sources": [
            {
                "source_id": "demo-leakage",
                "title": "Data leakage and reliable pipelines",
                "chunk_index": 0,
            }
        ],
        "latency": 6.304,
    },
]


def register_study_routes(app):
    @app.route("/study/sessions", methods=["GET", "POST"])
    def study_sessions():
        visitor_id = _visitor_id()
        if request.method == "POST":
            data = request.get_json(force=True)
            title = data.get("title", "").strip()
            if not title:
                return jsonify({"error": "title is required"}), 400
            session = StudySession(
                visitor_id=visitor_id,
                title=title,
                domain=data.get("domain", "").strip() or None,
            )
            db.session.add(session)
            db.session.commit()
            return jsonify(_serialize_session(session)), 201

        sessions = (
            _visible_sessions(visitor_id)
            .order_by(StudySession.updated_at.desc())
            .all()
        )
        return jsonify([_serialize_session(session) for session in sessions])

    @app.route("/study/sessions/<session_id>", methods=["GET", "PATCH", "DELETE"])
    def study_session_detail(session_id):
        session = _owned_session(session_id)
        if request.method == "GET":
            return jsonify(_serialize_session(session, include_details=True))
        if request.method == "PATCH":
            data = request.get_json(force=True)
            title = data.get("title")
            if title is not None:
                clean_title = title.strip()
                if not clean_title:
                    return jsonify({"error": "title is required"}), 400
                session.title = clean_title
            if "domain" in data:
                session.domain = data.get("domain", "").strip() or None
            session.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify(_serialize_session(session))

        _delete_session_data(session)
        return jsonify({"success": True})

    @app.route("/study/sessions/<session_id>/materials", methods=["GET", "POST"])
    def study_materials(session_id):
        session = _owned_session(session_id)
        if request.method == "POST":
            if request.files.get("file") is not None:
                return _add_pdf_material(session)
            data = request.get_json(force=True)
            title = data.get("title", "").strip()
            content = data.get("content", "").strip()
            if not title:
                return jsonify({"error": "title is required"}), 400
            if not content:
                return jsonify({"error": "content is required"}), 400

            material = StudyMaterial(
                session_id=session.id,
                title=title,
                content=content,
                status="indexing",
            )
            db.session.add(material)
            db.session.commit()
            try:
                result = ingest_study_material(
                    session_id=session.id,
                    text=material.content,
                    source_id=material.id,
                )
            except (RuntimeError, ValueError) as exc:
                material.status = "failed"
                db.session.commit()
                return jsonify({"error": str(exc), "material": _serialize_material(material)}), 503

            material.chunk_count = result["chunks_indexed"]
            material.status = "indexed"
            session.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify(_serialize_material(material)), 201

        query = request.args.get("query", "").strip()
        materials_query = StudyMaterial.query.filter_by(session_id=session.id)
        if query:
            materials_query = materials_query.filter(StudyMaterial.title.ilike(f"%{query}%"))
        materials = materials_query.order_by(StudyMaterial.created_at.desc()).all()
        ephemeral = get_sources(session.id)
        if query:
            ephemeral = [source for source in ephemeral if query.lower() in source.title.lower()]
        return jsonify(
            [_serialize_material(material) for material in materials]
            + [_serialize_ephemeral_source(source) for source in ephemeral]
        )

    @app.route("/study/materials/<material_id>", methods=["GET", "PATCH", "DELETE"])
    def study_material_detail(material_id):
        ephemeral = get_source(material_id)
        if ephemeral is not None:
            _owned_session(ephemeral.session_id)
            if request.method == "GET":
                return jsonify(_serialize_ephemeral_source(ephemeral))
            if request.method == "DELETE":
                remove_source(material_id)
                _rebuild_session_index(ephemeral.session_id)
                return jsonify({"success": True})
            return jsonify({"error": "PDF sources cannot be renamed"}), 400

        material = db.get_or_404(StudyMaterial, material_id)
        _owned_session(material.session_id)
        if request.method == "GET":
            return jsonify(_serialize_material(material, include_content=True))
        if request.method == "PATCH":
            data = request.get_json(force=True)
            title = data.get("title", "").strip()
            if not title:
                return jsonify({"error": "title is required"}), 400
            material.title = title
            db.session.commit()
            return jsonify(_serialize_material(material))

        session_id = material.session_id
        db.session.delete(material)
        get_vector_store().delete_source(material_id)
        db.session.commit()
        return jsonify({"success": True})

    @app.route("/study/sessions/<session_id>/messages", methods=["GET"])
    def study_messages(session_id):
        _owned_session(session_id)
        messages = (
            StudyMessage.query.filter_by(session_id=session_id)
            .order_by(StudyMessage.timestamp.asc(), StudyMessage.id.asc())
            .all()
        )
        return jsonify([_serialize_message(message) for message in messages])

    @app.route("/study/sessions/<session_id>/ask", methods=["POST"])
    def ask_study_question(session_id):
        session = _owned_session(session_id)
        data = request.get_json(force=True)
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "question is required"}), 400
        try:
            top_k = int(data.get("top_k", 5))
        except (TypeError, ValueError):
            return jsonify({"error": "top_k must be an integer"}), 400

        _ensure_session_index(session.id)
        retrieval = retrieve_chunks(session.id, question, top_k=top_k)
        chunks = _add_source_titles(retrieval["chunks"])
        try:
            answer = generate_grounded_answer(question, chunks)
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 503

        user_message = StudyMessage(
            session_id=session.id,
            role="user",
            content=question,
        )
        assistant_message = StudyMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
            grounded=bool(chunks),
            sources_json=json.dumps([_persisted_source(chunk) for chunk in chunks]),
            retrieval_latency_ms=retrieval["latency_ms"],
        )
        session.updated_at = datetime.utcnow()
        db.session.add_all([user_message, assistant_message])
        db.session.commit()
        response = _serialize_message(assistant_message)
        response["sources"] = chunks
        response["source_count"] = len(chunks)
        return jsonify(response), 201

    @app.route("/study/demo", methods=["POST"])
    def study_demo():
        visitor_id = _visitor_id()
        cleanup_duplicate_demos(visitor_id)
        existing = StudySession.query.filter_by(
            visitor_id=visitor_id,
            is_demo=True,
        ).first()
        if existing is not None and datetime.utcnow() - existing.updated_at >= DEMO_RESET_AFTER:
            _delete_session_data(existing)
            existing = None
        if existing is None:
            try:
                existing = _seed_demo(visitor_id)
            except IntegrityError:
                db.session.rollback()
                existing = db.session.get(StudySession, _demo_session_id(visitor_id))
        return jsonify(_serialize_session(existing, include_details=True))

    @app.route("/study/demo/reset", methods=["POST"])
    def reset_study_demo():
        visitor_id = _visitor_id()
        cleanup_duplicate_demos(visitor_id)
        existing = StudySession.query.filter_by(
            visitor_id=visitor_id,
            is_demo=True,
        ).first()
        if existing is not None:
            _delete_session_data(existing)
        session = _seed_demo(visitor_id)
        return jsonify(_serialize_session(session, include_details=True))

    @app.route("/study/progress", methods=["GET"])
    def study_progress():
        visitor_id = _visitor_id()
        sessions = _visible_sessions(visitor_id).all()
        session_ids = [session.id for session in sessions]
        if not session_ids:
            return jsonify(_empty_progress())

        links = SessionQuizLink.query.filter(SessionQuizLink.session_id.in_(session_ids)).all()
        quizzes = [db.session.get(QuizSession, link.quiz_id) for link in links]
        quizzes = [quiz for quiz in quizzes if quiz is not None]
        trend = [
            {
                "id": quiz.id,
                "topic": quiz.topic or "Study material",
                "score": quiz.score,
                "total": quiz.num_questions,
                "percentage": round((quiz.score / quiz.num_questions) * 100) if quiz.num_questions else 0,
                "timestamp": quiz.timestamp.isoformat(),
            }
            for quiz in sorted(quizzes, key=lambda item: item.timestamp)
        ]
        topics = {}
        for quiz in quizzes:
            topic = quiz.topic or "Study material"
            topics.setdefault(topic, []).append(
                (quiz.score / quiz.num_questions) * 100 if quiz.num_questions else 0
            )
        topic_scores = [
            {"topic": topic, "score": round(sum(scores) / len(scores))}
            for topic, scores in topics.items()
        ]
        topic_scores.sort(key=lambda item: item["score"], reverse=True)
        material_count = StudyMaterial.query.filter(StudyMaterial.session_id.in_(session_ids)).count()
        material_count += sum(len(get_sources(session_id)) for session_id in session_ids)
        flashcard_count = (
            db.session.query(func.count(SessionFlashcardLink.id))
            .filter(SessionFlashcardLink.session_id.in_(session_ids))
            .scalar()
            or 0
        )
        return jsonify({
            "sessions": len(sessions),
            "materials": material_count,
            "quizzes": len(quizzes),
            "average_score": round(
                sum(item["percentage"] for item in trend) / len(trend)
            ) if trend else 0,
            "flashcard_sets": flashcard_count,
            "score_trend": trend,
            "strong_topics": [item for item in topic_scores if item["score"] >= 75],
            "needs_review": [item for item in reversed(topic_scores) if item["score"] < 75],
        })

    @app.route("/study/history", methods=["GET"])
    def study_history():
        visitor_id = _visitor_id()
        sessions = _visible_sessions(visitor_id).all()
        session_ids = [session.id for session in sessions]
        if not session_ids:
            return jsonify([])
        session_titles = {session.id: session.title for session in sessions}
        items = []

        quiz_links = SessionQuizLink.query.filter(
            SessionQuizLink.session_id.in_(session_ids)
        ).all()
        for link in quiz_links:
            quiz = db.session.get(QuizSession, link.quiz_id)
            if quiz is not None:
                items.append({
                    "id": quiz.id,
                    "type": "quiz",
                    "title": quiz.topic or session_titles[link.session_id],
                    "session_id": link.session_id,
                    "timestamp": quiz.timestamp.isoformat(),
                    "metadata": f"{quiz.score}/{quiz.num_questions} correct",
                    "action": "Review",
                    "href": f"/practice/results/{quiz.id}",
                })

        flashcard_links = SessionFlashcardLink.query.filter(
            SessionFlashcardLink.session_id.in_(session_ids)
        ).all()
        for link in flashcard_links:
            flashcard = db.session.get(FlashcardSet, link.flashcard_id)
            if flashcard is not None:
                items.append({
                    "id": flashcard.id,
                    "type": "flashcards",
                    "title": flashcard.topic,
                    "session_id": link.session_id,
                    "timestamp": flashcard.timestamp.isoformat(),
                    "metadata": f"{flashcard.num_cards} cards",
                    "action": "Open",
                    "href": f"/flashcards/{flashcard.id}",
                })

        for session in sessions:
            items.append({
                "id": session.id,
                "type": "session",
                "title": session.title,
                "session_id": session.id,
                "timestamp": session.updated_at.isoformat(),
                "metadata": f"{StudyMessage.query.filter_by(session_id=session.id).count()} messages",
                "action": "Resume",
                "href": f"/learn/{session.id}",
            })

        items.sort(key=lambda item: item["timestamp"], reverse=True)
        return jsonify(items)

    @app.route("/study/flashcards", methods=["GET"])
    def study_flashcards():
        visitor_id = _visitor_id()
        session_ids = [
            session.id
            for session in _visible_sessions(visitor_id).all()
        ]
        if not session_ids:
            return jsonify([])
        links = SessionFlashcardLink.query.filter(
            SessionFlashcardLink.session_id.in_(session_ids)
        ).all()
        results = []
        for link in links:
            item = db.session.get(FlashcardSet, link.flashcard_id)
            if item is not None:
                results.append({
                    "id": item.id,
                    "session_id": link.session_id,
                    "timestamp": item.timestamp.isoformat(),
                    "topic": item.topic,
                    "num_cards": item.num_cards,
                })
        results.sort(key=lambda item: item["timestamp"], reverse=True)
        return jsonify(results)


def get_session_content(session_id: str) -> str:
    _owned_session(session_id)
    materials = (
        StudyMaterial.query.filter_by(session_id=session_id)
        .order_by(StudyMaterial.created_at.asc())
        .all()
    )
    durable_content = "\n\n".join(
        f"{material.title}\n{material.content}"
        for material in materials
    )
    ephemeral_content = "\n\n".join(
        f"{source.title}\n{source.text}" for source in get_sources(session_id)
    )
    return "\n\n".join(part for part in (durable_content, ephemeral_content) if part)


def require_owned_session(session_id: str):
    return _owned_session(session_id)


def _visitor_id():
    user = current_user()
    if user is not None:
        return user["id"]
    visitor_id = request.headers.get("X-LearnLoop-Visitor", "").strip()
    return visitor_id[:64] if visitor_id else "local-dev"


def _visible_sessions(visitor_id):
    query = StudySession.query.filter_by(visitor_id=visitor_id)
    if current_user() is not None:
        query = query.filter_by(is_demo=False)
    return query


def _owned_session(session_id):
    session = db.get_or_404(StudySession, session_id)
    if session.visitor_id != _visitor_id():
        return db.get_or_404(StudySession, "__not_found__")
    return session


def _serialize_session(session, include_details=False):
    material_count = StudyMaterial.query.filter_by(session_id=session.id).count() + len(
        get_sources(session.id)
    )
    message_count = StudyMessage.query.filter_by(session_id=session.id).count()
    quiz_count = SessionQuizLink.query.filter_by(session_id=session.id).count()
    flashcard_count = SessionFlashcardLink.query.filter_by(session_id=session.id).count()
    payload = {
        "id": session.id,
        "title": session.title,
        "domain": session.domain,
        "is_demo": session.is_demo,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "material_count": material_count,
        "message_count": message_count,
        "quiz_count": quiz_count,
        "flashcard_count": flashcard_count,
    }
    if include_details:
        payload["materials"] = [
            _serialize_material(material)
            for material in StudyMaterial.query.filter_by(session_id=session.id)
            .order_by(StudyMaterial.created_at.asc())
            .all()
        ]
        payload["materials"].extend(
            _serialize_ephemeral_source(source) for source in get_sources(session.id)
        )
    return payload


def _serialize_material(material, include_content=False):
    payload = {
        "id": material.id,
        "session_id": material.session_id,
        "title": material.title,
        "chunk_count": material.chunk_count,
        "status": material.status,
        "created_at": material.created_at.isoformat(),
    }
    if include_content:
        payload["content"] = material.content
    return payload


def _serialize_ephemeral_source(source):
    return {
        "id": source.id,
        "session_id": source.session_id,
        "title": source.title,
        "chunk_count": source.chunk_count,
        "status": "indexed",
        "source_type": source.source_type,
        "created_at": source.created_at,
    }


def _add_pdf_material(session):
    uploaded_file = request.files["file"]
    filename = (uploaded_file.filename or "").strip()
    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Upload a PDF file"}), 400

    title = request.form.get("title", "").strip() or filename.rsplit(".", 1)[0]
    if not title:
        return jsonify({"error": "title is required"}), 400

    try:
        text = extract_pdf_text(uploaded_file.read())
        source = register_source(session.id, title, text, 0)
        result = ingest_study_material(
            session_id=session.id,
            text=text,
            source_id=source.id,
        )
        source = register_source(
            session.id,
            title,
            text,
            result["chunks_indexed"],
            source_id=source.id,
        )
    except (RuntimeError, ValueError) as exc:
        if "source" in locals():
            remove_source(source.id)
        return jsonify({"error": str(exc)}), 400

    session.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_ephemeral_source(source)), 201


def _serialize_message(message):
    sources = json.loads(message.sources_json or "[]")
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "grounded": message.grounded,
        "sources": sources,
        "source_count": len(sources),
        "retrieval_latency_ms": message.retrieval_latency_ms,
        "timestamp": message.timestamp.isoformat(),
    }


def _persisted_source(chunk):
    if get_source(chunk["source_id"]) is None:
        return chunk
    return {key: value for key, value in chunk.items() if key != "text"}


def _ensure_session_index(session_id):
    store = get_vector_store()
    if store.has_session(session_id):
        return None
    materials = StudyMaterial.query.filter_by(session_id=session_id).all()
    if not materials:
        return None
    try:
        for material in materials:
            result = ingest_study_material(
                session_id=session_id,
                text=material.content,
                source_id=material.id,
            )
            material.chunk_count = result["chunks_indexed"]
            material.status = "indexed"
    except (RuntimeError, ValueError):
        store.delete_session(session_id)
        raise
    db.session.commit()


def _rebuild_session_index(session_id):
    get_vector_store().delete_session(session_id)
    materials = StudyMaterial.query.filter_by(session_id=session_id).all()
    for material in materials:
        result = ingest_study_material(
            session_id=session_id,
            text=material.content,
            source_id=material.id,
        )
        material.chunk_count = result["chunks_indexed"]
        material.status = "indexed"
    for source in get_sources(session_id):
        ingest_study_material(
            session_id=session_id,
            text=source.text,
            source_id=source.id,
        )
    db.session.commit()


def _add_source_titles(chunks):
    material_ids = {chunk["source_id"] for chunk in chunks}
    materials = StudyMaterial.query.filter(StudyMaterial.id.in_(material_ids)).all()
    titles = {material.id: material.title for material in materials}
    if chunks:
        titles.update({source.id: source.title for source in get_sources(chunks[0]["session_id"])})
    return [
        {**chunk, "title": titles.get(chunk["source_id"], "Study material")}
        for chunk in chunks
    ]


def _delete_session_data(session):
    clear_session_index(session.id)
    clear_sources(session.id)
    quiz_links = SessionQuizLink.query.filter_by(session_id=session.id).all()
    flashcard_links = SessionFlashcardLink.query.filter_by(session_id=session.id).all()
    for link in quiz_links:
        quiz = db.session.get(QuizSession, link.quiz_id)
        db.session.delete(link)
        if quiz is not None:
            db.session.delete(quiz)
    for link in flashcard_links:
        flashcard = db.session.get(FlashcardSet, link.flashcard_id)
        db.session.delete(link)
        if flashcard is not None:
            db.session.delete(flashcard)
    StudyMessage.query.filter_by(session_id=session.id).delete()
    StudyMaterial.query.filter_by(session_id=session.id).delete()
    db.session.delete(session)
    db.session.commit()


def _seed_demo(visitor_id):
    session = StudySession(
        id=_demo_session_id(visitor_id),
        visitor_id=visitor_id,
        title=DEMO_TITLE,
        domain=DEMO_DOMAIN,
        is_demo=True,
        created_at=datetime(2026, 7, 1, 14, 0),
        updated_at=datetime.utcnow(),
    )
    db.session.add(session)
    db.session.flush()

    materials = []
    for index, item in enumerate(DEMO_MATERIALS):
        material = StudyMaterial(
            id=f"{session.id[:8]}-0000-4000-8000-{index + 1:012d}",
            session_id=session.id,
            title=item["title"],
            content=item["content"],
            chunk_count=1,
            status="indexed",
        )
        materials.append(material)
        db.session.add(material)
    db.session.flush()

    source_ids = {
        "demo-evaluation": materials[1].id,
        "demo-leakage": materials[2].id,
    }
    for item in DEMO_MESSAGES:
        sources = [
            {**source, "source_id": source_ids.get(source["source_id"], source["source_id"])}
            for source in item["sources"]
        ]
        db.session.add(StudyMessage(
            session_id=session.id,
            role=item["role"],
            content=item["content"],
            grounded=item["grounded"],
            sources_json=json.dumps(sources),
            retrieval_latency_ms=item.get("latency"),
        ))

    quiz_specs = [
        ("Evaluation metrics", 3, 5, datetime(2026, 7, 8, 10, 15)),
        ("Data leakage", 4, 5, datetime(2026, 7, 16, 13, 40)),
        ("Generalization", 5, 5, datetime(2026, 7, 25, 17, 20)),
    ]
    for topic, score, total, timestamp in quiz_specs:
        quiz = QuizSession(
            timestamp=timestamp,
            topic=topic,
            num_questions=total,
            quiz_json=json.dumps(_demo_quiz(topic, total)),
            user_answers_json=json.dumps({str(index): "A" for index in range(total)}),
            correct_answers_json=json.dumps(["A"] * total),
            score=score,
        )
        db.session.add(quiz)
        db.session.flush()
        db.session.add(SessionQuizLink(session_id=session.id, quiz_id=quiz.id))

    flashcard = FlashcardSet(
        timestamp=datetime(2026, 7, 22, 11, 5),
        topic="Machine Learning Foundations",
        num_cards=5,
        cards_json=json.dumps([
            {"term": "Generalization", "definition": "Performance on unseen data."},
            {"term": "Overfitting", "definition": "Learning training noise instead of reusable patterns."},
            {"term": "Recall", "definition": "The fraction of actual positives correctly identified."},
            {"term": "L2 regularization", "definition": "A penalty that smoothly shrinks model coefficients."},
            {"term": "Data leakage", "definition": "Using information during training that would be unavailable at prediction time."},
        ]),
    )
    db.session.add(flashcard)
    db.session.flush()
    db.session.add(SessionFlashcardLink(session_id=session.id, flashcard_id=flashcard.id))
    db.session.commit()
    return session


def _demo_session_id(visitor_id):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"learnloop-demo:{visitor_id}"))


def cleanup_duplicate_demos(visitor_id=None):
    query = StudySession.query.filter_by(is_demo=True)
    if visitor_id is not None:
        query = query.filter_by(visitor_id=visitor_id)
    visitor_ids = {session.visitor_id for session in query.all()}
    removed = 0
    for current_visitor_id in visitor_ids:
        demos = (
            StudySession.query.filter_by(visitor_id=current_visitor_id, is_demo=True)
            .order_by(StudySession.updated_at.desc(), StudySession.created_at.asc())
            .all()
        )
        for duplicate in demos[1:]:
            _delete_session_data(duplicate)
            removed += 1
    return removed


def _demo_quiz(topic, total):
    return [
        {
            "type": "MCQ",
            "question": f"{topic}: sample question {index + 1}",
            "options": ["A. Correct concept", "B. Distractor", "C. Distractor", "D. Distractor"],
            "correct_answer": "A",
            "explanation": "This seeded attempt demonstrates the saved quiz review flow.",
        }
        for index in range(total)
    ]


def _empty_progress():
    return {
        "sessions": 0,
        "materials": 0,
        "quizzes": 0,
        "average_score": 0,
        "flashcard_sets": 0,
        "score_trend": [],
        "strong_topics": [],
        "needs_review": [],
    }

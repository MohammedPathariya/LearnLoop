import json
from datetime import datetime

from flask import jsonify, request
from sqlalchemy import func, or_

from .extensions import db
from .models import Conversation, FlashcardSet, QuizSession
from .services.generation import generate_convo, generate_flashcards, generate_grounded_answer, generate_quiz
from .services.rag import ingest_study_material, retrieve_chunks


def register_routes(app):
    @app.route("/healthz")
    def healthz():
        return "OK", 200

    @app.route("/conversations/<int:conv_id>", methods=["DELETE"])
    def delete_conversation(conv_id):
        conv = db.get_or_404(Conversation, conv_id)
        db.session.delete(conv)
        db.session.commit()
        return jsonify({"success": True})

    @app.route("/quiz_results/<int:quiz_id>", methods=["DELETE"])
    def delete_quiz(quiz_id):
        q = db.get_or_404(QuizSession, quiz_id)
        db.session.delete(q)
        db.session.commit()
        return jsonify({"success": True})

    @app.route("/flashcards/<int:id>", methods=["DELETE"])
    def delete_flashcard(id):
        s = db.get_or_404(FlashcardSet, id)
        db.session.delete(s)
        db.session.commit()
        return jsonify({"success": True})

    @app.route("/chat", methods=["POST"])
    def chat():
        data = request.get_json(force=True)
        topic = data.get("topic", "").strip()
        if not topic:
            return jsonify({"error": "Missing 'topic'"}), 400

        try:
            turns = int(data.get("turns", 3))
        except ValueError:
            return jsonify({"error": "'turns' must be an integer"}), 400

        style = data.get("style", "natural")
        mode = data.get("mode", "student-first")

        convo = generate_convo(topic, turns=turns, style=style, mode=mode)

        new_chat = Conversation(topic=topic, style=style, mode=mode, turns=turns, result=convo)
        db.session.add(new_chat)
        db.session.commit()

        return jsonify({
            "topic": topic,
            "turns": turns,
            "style": style,
            "mode": mode,
            "conversation": convo,
        })

    @app.route("/history", methods=["GET"])
    def history():
        chats = Conversation.query.order_by(Conversation.timestamp.desc()).limit(20).all()
        return jsonify([
            {
                "id": chat.id,
                "timestamp": chat.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "topic": chat.topic,
                "style": chat.style,
                "mode": chat.mode,
                "turns": chat.turns,
                "result": chat.result,
            }
            for chat in chats
        ])

    @app.route("/conversations/<int:conv_id>", methods=["GET"])
    def get_conversation(conv_id):
        conv = db.get_or_404(Conversation, conv_id)
        return jsonify({
            "id": conv.id,
            "timestamp": conv.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "topic": conv.topic,
            "style": conv.style,
            "mode": conv.mode,
            "turns": conv.turns,
            "result": conv.result,
        })

    @app.route("/search", methods=["GET"])
    def search_conversations():
        query = request.args.get("query", "").strip()
        if not query:
            return jsonify([])

        results = Conversation.query.filter(
            or_(
                Conversation.topic.ilike(f"%{query}%"),
                Conversation.result.ilike(f"%{query}%"),
            )
        ).order_by(Conversation.timestamp.desc()).limit(10).all()

        return jsonify([
            {
                "id": conv.id,
                "timestamp": conv.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "topic": conv.topic,
                "style": conv.style,
                "mode": conv.mode,
                "turns": conv.turns,
                "result": conv.result,
            }
            for conv in results
        ])

    @app.route("/rag/ingest", methods=["POST"])
    def rag_ingest():
        data = request.get_json(force=True)
        session_id = data.get("session_id", "")
        text = data.get("text", "")
        source_id = data.get("source_id")

        try:
            result = ingest_study_material(session_id=session_id, text=text, source_id=source_id)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify(result), 201

    @app.route("/rag/retrieve", methods=["POST"])
    def rag_retrieve():
        data = request.get_json(force=True)
        try:
            top_k = int(data.get("top_k", 5))
        except (ValueError, TypeError):
            return jsonify({"error": "top_k must be an integer"}), 400

        try:
            result = retrieve_chunks(
                session_id=data.get("session_id", ""),
                query=data.get("query", ""),
                top_k=top_k,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify(result)

    @app.route("/rag/answer", methods=["POST"])
    def rag_answer():
        data = request.get_json(force=True)
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "question is required"}), 400
        try:
            top_k = int(data.get("top_k", 5))
        except (ValueError, TypeError):
            return jsonify({"error": "top_k must be an integer"}), 400

        try:
            retrieval = retrieve_chunks(
                session_id=data.get("session_id", ""),
                query=question,
                top_k=top_k,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        answer = generate_grounded_answer(question, retrieval["chunks"])

        return jsonify({
            "answer": answer,
            "chunks": retrieval["chunks"],
            "retrieval_latency_ms": retrieval["latency_ms"],
        })

    @app.route("/analytics/stats", methods=["GET"])
    def get_stats():
        total_conversations = Conversation.query.count()
        total_turns = db.session.query(func.sum(Conversation.turns)).scalar() or 0
        unique_topics = db.session.query(func.count(func.distinct(Conversation.topic))).scalar()
        today_sessions = Conversation.query.filter(
            func.date(Conversation.timestamp) == datetime.utcnow().date()
        ).count()

        return jsonify({
            "total_conversations": total_conversations,
            "total_turns": total_turns,
            "unique_topics": unique_topics,
            "today_sessions": today_sessions,
        })

    @app.route("/quiz", methods=["POST"])
    def quiz():
        data = request.get_json(force=True)
        topic = data.get("topic", "").strip()
        content = data.get("content", "").strip()
        try:
            num_q = int(data.get("num_questions", 5))
        except (ValueError, TypeError):
            return jsonify({"error": "num_questions must be an integer"}), 400

        if not topic and not content:
            return jsonify({"error": "Provide either 'topic' or 'content'"}), 400
        if not 1 <= num_q <= 20:
            return jsonify({"error": "num_questions must be between 1 and 20"}), 400

        quiz_data = generate_quiz(
            content=content if content else None,
            topic=topic if topic else None,
            num_questions=num_q,
        )

        status_code = 502 if "error" in quiz_data else 200
        return jsonify(quiz_data), status_code

    @app.route("/quiz_results", methods=["POST"])
    def save_quiz_results():
        data = request.get_json(force=True)

        num_q = data.get("num_questions")
        quiz_arr = data.get("quiz")
        user_answers = data.get("user_answers")
        correct_answers = data.get("correct_answers")
        score = data.get("score")

        if quiz_arr is None or user_answers is None or correct_answers is None or score is None:
            return jsonify({"error": "Missing one of required fields: quiz, user_answers, correct_answers, score"}), 400

        quiz_session = QuizSession(
            topic=data.get("topic", None),
            content=data.get("content", None),
            num_questions=num_q,
            quiz_json=json.dumps(quiz_arr),
            user_answers_json=json.dumps(user_answers),
            correct_answers_json=json.dumps(correct_answers),
            score=score,
        )
        db.session.add(quiz_session)
        db.session.commit()

        return jsonify({"success": True, "quiz_session_id": quiz_session.id}), 201

    @app.route("/quiz_history", methods=["GET"])
    def get_quiz_history():
        quizzes = QuizSession.query.order_by(QuizSession.timestamp.desc()).limit(20).all()
        result = []
        for q in quizzes:
            result.append({
                "id": q.id,
                "timestamp": q.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "topic": q.topic,
                "content": (q.content[:100] + "...") if q.content and len(q.content) > 100 else q.content,
                "num_questions": q.num_questions,
                "score": q.score,
            })
        return jsonify(result)

    @app.route("/analytics/quiz_stats", methods=["GET"])
    def get_quiz_stats():
        total_quizzes = QuizSession.query.count()
        total_questions_given = db.session.query(func.sum(QuizSession.num_questions)).scalar() or 0
        total_score_sum = db.session.query(func.sum(QuizSession.score)).scalar() or 0

        average_score = (
            float(total_score_sum) / float(total_quizzes)
            if total_quizzes > 0
            else 0.0
        )

        today = datetime.utcnow().date()
        quizzes_today = QuizSession.query.filter(
            func.date(QuizSession.timestamp) == today
        ).count()

        return jsonify({
            "total_quizzes": total_quizzes,
            "total_questions": total_questions_given,
            "average_score": round(average_score, 2),
            "quizzes_today": quizzes_today,
        })

    @app.route("/quiz_results/<int:quiz_id>", methods=["GET"])
    def get_quiz_by_id(quiz_id):
        session = db.get_or_404(QuizSession, quiz_id)

        return jsonify({
            "id": session.id,
            "timestamp": session.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "topic": session.topic,
            "content": session.content,
            "num_questions": session.num_questions,
            "quiz": json.loads(session.quiz_json),
            "user_answers": json.loads(session.user_answers_json),
            "correct_answers": json.loads(session.correct_answers_json),
            "score": session.score,
        })

    @app.route("/flashcards", methods=["POST"])
    def flashcards():
        data = request.get_json(force=True)
        topic = data.get("topic", "").strip()
        if not topic:
            return jsonify({"error": "Missing 'topic'"}), 400
        try:
            num = int(data.get("num_cards", 5))
        except (ValueError, TypeError):
            return jsonify({"error": "num_cards must be an integer"}), 400
        if not 1 <= num <= 10:
            return jsonify({"error": "num_cards must be between 1 and 10"}), 400

        cards = generate_flashcards(topic, num_cards=num)

        if "flashcards" in cards and isinstance(cards["flashcards"], list):
            cards_json_str = json.dumps(cards["flashcards"])
            fc = FlashcardSet(topic=topic, num_cards=len(cards["flashcards"]), cards_json=cards_json_str)
            db.session.add(fc)
            db.session.commit()
            cards["id"] = fc.id
        status_code = 502 if "error" in cards else 200
        return jsonify(cards), status_code

    @app.route("/flashcards_history", methods=["GET"])
    def flashcards_history():
        sets = FlashcardSet.query.order_by(FlashcardSet.timestamp.desc()).limit(20).all()
        return jsonify([
            {
                "id": s.id,
                "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "topic": s.topic,
                "num_cards": s.num_cards,
            }
            for s in sets
        ])

    @app.route("/flashcards/<int:id>", methods=["GET"])
    def get_flashcard_set(id):
        s = db.get_or_404(FlashcardSet, id)
        return jsonify({
            "id": s.id,
            "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "topic": s.topic,
            "num_cards": s.num_cards,
            "flashcards": json.loads(s.cards_json),
        })

    @app.route("/analytics/flashcard_stats", methods=["GET"])
    def get_flashcard_stats():
        total_sets = FlashcardSet.query.count()
        total_cards = db.session.query(func.sum(FlashcardSet.num_cards)).scalar() or 0
        today = datetime.utcnow().date()
        today_sets = FlashcardSet.query.filter(func.date(FlashcardSet.timestamp) == today).count()

        return jsonify({
            "total_flashcard_sets": total_sets,
            "total_flashcards_generated": total_cards,
            "sets_created_today": today_sets,
        })

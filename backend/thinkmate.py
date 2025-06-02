from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from datetime import datetime
import os
import re
import json
from dotenv import load_dotenv
from sqlalchemy import func, or_

load_dotenv()

# ─── Setup ───────────────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment")

client = OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'conversations.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ─── Models ──────────────────────────────────────────
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    topic = db.Column(db.String(255), nullable=False)
    style = db.Column(db.String(50))
    mode = db.Column(db.String(50))
    turns = db.Column(db.Integer)
    result = db.Column(db.Text)

class QuizSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    topic = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=True)
    num_questions = db.Column(db.Integer, nullable=False)
    quiz_json = db.Column(db.Text, nullable=False)
    user_answers_json = db.Column(db.Text, nullable=False)
    correct_answers_json = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)


# ─── Generation Helpers ──────────────────────────────────────

def generate_convo(topic: str, turns=3, style="natural", mode="student-first") -> str:
    """
    Existing conversation generator: returns a Teacher-Student dialogue.
    """
    style_desc = {
        "natural": "in a friendly, conversational tone",
        "formal":  "in a formal, academic tone",
        "humorous":"with light humor and wit",
        "technical":"with precise, technical language"
    }.get(style, "in a friendly, conversational tone")

    starter = {
        "student-first": "The student starts by asking about the topic.",
        "teacher-first": "The teacher begins with a question or prompt to the student."
    }[mode]

    system_prompt = (
        f"You are simulating a {style_desc} conversation between a curious student and a knowledgeable teacher. "
        f"{starter} "
        f"Have exactly {turns} back-and-forth exchanges (so {turns*2} messages), "
        "and end with a warm wrap-up."
    )

    user_message = f"Topic: {topic}"

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=512,
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip()


def generate_quiz(content: str = None, topic: str = None, num_questions: int = 5) -> dict:
    """
    Generates a quiz in JSON form. If GPT returns trailing commas,
    we strip them out before parsing.
    """
    if content:
        prompt_source = f"Here is a piece of content:\n\n{content}\n\n"
    else:
        prompt_source = f"Create a quiz about the following topic:\n\n{topic}\n\n"

    system_prompt = (
        "You are an AI quiz generator. *Respond with exactly one JSON object and nothing else—no additional text.*\n"
        f"Produce exactly {num_questions} questions in JSON format. "
        "Include a mix of MCQ, True/False, and Fill-in-the-blank questions. "
        "For each question, provide:\n"
        "  • type (\"MCQ\" / \"True/False\" / \"Fill-in-the-blank\"),\n"
        "  • question text,\n"
        "  • for MCQ: a list of exactly 4 options and the correct answer letter,\n"
        "  • for True/False: answer \"True\" or \"False\",\n"
        "  • for Fill-in-the-blank: the correct word/phrase,\n"
        "  • a short explanation (rationale) for the correct answer.\n"
        "Return a single JSON object with one key \"quiz\" whose value is a list of those question objects."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # you can revert to "gpt-4o-mini" if desired
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_source}
        ],
        max_tokens=800,
        temperature=0.7,
    )
    raw_text = resp.choices[0].message.content.strip()

    # --- Sanitize any trailing commas in arrays/objects ---
    # 1) Remove commas before a closing bracket ]
    sanitized = re.sub(r',\s*]', ']', raw_text)
    # 2) Remove commas before a closing brace }
    sanitized = re.sub(r',\s*}', '}', sanitized)

    try:
        quiz_json = json.loads(sanitized)
    except Exception:
        # If it still fails, return the raw text for debugging
        quiz_json = {"error": "Failed to parse GPT output as JSON", "raw_output": raw_text}

    return quiz_json


# ─── Routes ──────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    """
    Existing chat endpoint: topic + style + mode → teacher/student conversation
    """
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
        "conversation": convo
    })


@app.route("/history", methods=["GET"])
def history():
    chats = Conversation.query.order_by(Conversation.timestamp.desc()).limit(20).all()
    return jsonify([
        {
            "id": chat.id,
            "timestamp": chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "topic": chat.topic,
            "style": chat.style,
            "mode": chat.mode,
            "turns": chat.turns,
            "result": chat.result
        }
        for chat in chats
    ])


@app.route("/conversations/<int:conv_id>", methods=["GET"])
def get_conversation(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    return jsonify({
        "id": conv.id,
        "timestamp": conv.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "topic": conv.topic,
        "style": conv.style,
        "mode": conv.mode,
        "turns": conv.turns,
        "result": conv.result
    })


@app.route("/search", methods=["GET"])
def search_conversations():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])

    results = Conversation.query.filter(
        or_(
            Conversation.topic.ilike(f"%{query}%"),
            Conversation.result.ilike(f"%{query}%")
        )
    ).order_by(Conversation.timestamp.desc()).limit(10).all()

    return jsonify([
        {
            "id": conv.id,
            "timestamp": conv.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "topic": conv.topic,
            "style": conv.style,
            "mode": conv.mode,
            "turns": conv.turns,
            "result": conv.result
        }
        for conv in results
    ])


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
        "today_sessions": today_sessions
    })


@app.route("/quiz", methods=["POST"])
def quiz():
    """
    New endpoint: generate a quiz from either:
      • request.json['topic']   (a short topic string), or
      • request.json['content'] (a longer block of text),
    Optionally you can include "num_questions" in the body.
    """
    data = request.get_json(force=True)
    topic = data.get("topic", "").strip()
    content = data.get("content", "").strip()
    try:
        num_q = int(data.get("num_questions", 5))
    except (ValueError, TypeError):
        num_q = 5

    if not topic and not content:
        return jsonify({"error": "Provide either 'topic' or 'content'"}), 400

    quiz_data = generate_quiz(content=content if content else None,
                              topic=(topic if topic else None),
                              num_questions=num_q)

    return jsonify(quiz_data)


@app.route("/quiz_results", methods=["POST"])
def save_quiz_results():
    """
    Expects a JSON body with keys:
    {
      "topic": "...",            # optional if content‐based
      "content": "...",          # optional if topic‐based
      "num_questions": 5,
      "quiz": [ { ... }, { ... }, ... ],           # the full quiz array
      "user_answers": { "0": "B", "1": "True", ... },  # as an object
      "correct_answers": ["B", "True", "tuning", ...],
      "score": 3
    }
    """
    data = request.get_json(force=True)

    # Basic validation
    num_q = data.get("num_questions")
    quiz_arr = data.get("quiz")
    user_answers = data.get("user_answers")
    correct_answers = data.get("correct_answers")
    score = data.get("score")

    if quiz_arr is None or user_answers is None or correct_answers is None or score is None:
        return jsonify({"error": "Missing one of required fields: quiz, user_answers, correct_answers, score"}), 400

    # Extract optional fields
    topic = data.get("topic", None)
    content = data.get("content", None)

    # Stringify all JSON blobs
    quiz_json_str = json.dumps(quiz_arr)
    user_answers_json_str = json.dumps(user_answers)
    correct_answers_json_str = json.dumps(correct_answers)

    # Save to DB
    quiz_session = QuizSession(
        topic=topic,
        content=content,
        num_questions=num_q,
        quiz_json=quiz_json_str,
        user_answers_json=user_answers_json_str,
        correct_answers_json=correct_answers_json_str,
        score=score
    )
    db.session.add(quiz_session)
    db.session.commit()

    return jsonify({"success": True, "quiz_session_id": quiz_session.id}), 201

@app.route("/quiz_history", methods=["GET"])
def get_quiz_history():
    """
    Returns the most recent 20 quiz sessions, ordered by timestamp desc.
    """
    quizzes = QuizSession.query.order_by(QuizSession.timestamp.desc()).limit(20).all()
    result = []
    for q in quizzes:
        result.append({
            "id": q.id,
            "timestamp": q.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "topic": q.topic,
            "content": (q.content[:100] + "...") if q.content and len(q.content) > 100 else q.content,
            "num_questions": q.num_questions,
            "score": q.score
        })
    return jsonify(result)

@app.route("/analytics/quiz_stats", methods=["GET"])
def get_quiz_stats():
    """
    Returns overall statistics for quizzes:
      • total_quizzes
      • total_questions_given (sum of num_questions over all quiz sessions)
      • average_score (float)
      • quizzes_today (count where timestamp is today)
    """
    from sqlalchemy import func

    total_quizzes = QuizSession.query.count()
    total_questions_given = db.session.query(func.sum(QuizSession.num_questions)).scalar() or 0
    total_score_sum = db.session.query(func.sum(QuizSession.score)).scalar() or 0

    # Avoid division by zero
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
        "quizzes_today": quizzes_today
    })
    
@app.route("/quiz_results/<int:quiz_id>", methods=["GET"])
def get_quiz_by_id(quiz_id):
    """
    Fetch a single QuizSession by ID and return:
      {
        "id": <int>,
        "timestamp": "YYYY-MM-DD HH:MM:SS",
        "topic": <string> or null,
        "content": <string> or null,
        "num_questions": <int>,
        "quiz": [ { question, type, options, explanation, … }, … ],
        "user_answers": { "0": "B", "1": "True", … },
        "correct_answers": [ "B", "True", "tuning", … ],
        "score": <int>
      }
    """
    session = QuizSession.query.get_or_404(quiz_id)

    # Parse stored JSON strings back into Python objects
    quiz_list = json.loads(session.quiz_json)
    user_answers_obj = json.loads(session.user_answers_json)
    correct_answers_arr = json.loads(session.correct_answers_json)

    return jsonify({
        "id": session.id,
        "timestamp": session.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "topic": session.topic,
        "content": session.content,
        "num_questions": session.num_questions,
        "quiz": quiz_list,
        "user_answers": user_answers_obj,
        "correct_answers": correct_answers_arr,
        "score": session.score
    })

# ─── Init & Run ─────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
from datetime import datetime
import uuid

from .extensions import db


def new_uuid():
    return str(uuid.uuid4())


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


class FlashcardSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    topic = db.Column(db.String(255), nullable=False)
    num_cards = db.Column(db.Integer, nullable=False)
    cards_json = db.Column(db.Text, nullable=False)


class StudySession(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=new_uuid)
    visitor_id = db.Column(db.String(64), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=True)
    is_demo = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class StudyMaterial(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=new_uuid)
    session_id = db.Column(
        db.String(36),
        db.ForeignKey("study_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(32), nullable=False, default="indexed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class StudyMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.String(36),
        db.ForeignKey("study_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(16), nullable=False)
    content = db.Column(db.Text, nullable=False)
    grounded = db.Column(db.Boolean, nullable=False, default=False)
    sources_json = db.Column(db.Text, nullable=False, default="[]")
    retrieval_latency_ms = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SessionQuizLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.String(36),
        db.ForeignKey("study_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz_session.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )


class SessionFlashcardLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.String(36),
        db.ForeignKey("study_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flashcard_id = db.Column(
        db.Integer,
        db.ForeignKey("flashcard_set.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

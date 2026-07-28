from datetime import datetime

from .extensions import db


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

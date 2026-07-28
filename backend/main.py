import os

from dotenv import load_dotenv

from app import create_app, db
from app.models import Conversation, FlashcardSet, QuizSession
from app.study_routes import cleanup_duplicate_demos
from app.services.generation import generate_convo, generate_flashcards, generate_quiz

load_dotenv()

if __name__ == "__main__" and os.getenv("LEARNLOOP_USE_REMOTE_DB") != "1":
    os.environ.pop("SUPABASE_DB_URI", None)

app = create_app()

__all__ = [
    "app",
    "create_app",
    "db",
    "Conversation",
    "QuizSession",
    "FlashcardSet",
    "generate_convo",
    "generate_quiz",
    "generate_flashcards",
]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))

    with app.app_context():
        db.create_all()
        cleanup_duplicate_demos()

    print("Flask app starting")
    print("Listening on port:", port)
    print("DB URI:", app.config.get("SQLALCHEMY_DATABASE_URI", "Not set"))

    app.run(host="0.0.0.0", port=port)

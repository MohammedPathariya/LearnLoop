import os


def build_database_uri() -> str:
    db_url = os.getenv("SUPABASE_DB_URI")
    if db_url:
        return db_url

    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_path = os.path.join(backend_dir, "conversations.db")
    return f"sqlite:///{db_path}"


class Config:
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = [
        "http://localhost:3000",
        "https://learnloop-deployment-frontend.vercel.app",
    ]

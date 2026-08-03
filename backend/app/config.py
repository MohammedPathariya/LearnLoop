import json
import os


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} must be a JSON array of origins") from exc
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeError(f"{name} must be a JSON array of origins")
    return value


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
    CORS_ORIGINS = _env_list(
        "CORS_ORIGINS",
        [
            "http://localhost:3000",
            "https://learnloop-deployment-frontend.vercel.app",
        ],
    )

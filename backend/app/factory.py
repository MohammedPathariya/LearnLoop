from flask import Flask
from flask_cors import CORS
from sqlalchemy import event

from .config import Config
from .extensions import db
from .auth import register_auth
from .routes import register_routes
from .study_routes import register_study_routes


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        from .config import build_database_uri

        app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()

    CORS(app, origins=app.config["CORS_ORIGINS"])
    db.init_app(app)
    _configure_sqlite(app)
    register_auth(app)
    register_routes(app)
    register_study_routes(app)

    return app


def _configure_sqlite(app):
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not uri.startswith("sqlite:"):
        return

    with app.app_context():
        engine = db.engine

    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout=5000")
        journal_mode = cursor.execute("PRAGMA journal_mode").fetchone()[0]
        if journal_mode.lower() != "wal":
            cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

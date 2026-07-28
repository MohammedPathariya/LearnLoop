from app import create_app, db
from app.study_routes import cleanup_duplicate_demos


app = create_app()

with app.app_context():
    db.create_all()
    cleanup_duplicate_demos()

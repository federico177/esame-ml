"""Entrypoint for feedback-service. Run with: python -m app"""
from flask import Flask
from .config import PORT, STORAGE_BACKEND, DATA_DIR
from .routes import feedbacks_bp


def create_app(repository=None):
    app = Flask(__name__)
    if repository is None:
        repository = _build_repository()
    app.config["REPOSITORY"] = repository
    app.register_blueprint(feedbacks_bp)
    return app


def _build_repository():
    if STORAGE_BACKEND == "json":
        from .storage.json_store import JsonRepository
        return JsonRepository(DATA_DIR)
    elif STORAGE_BACKEND == "sqlite":
        from .storage.sqlite_store import SqliteRepository
        return SqliteRepository(DATA_DIR)
    else:
        from .storage.memory import MemoryRepository
        return MemoryRepository()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=PORT)

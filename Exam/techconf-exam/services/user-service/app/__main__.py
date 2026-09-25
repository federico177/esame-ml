"""
Entrypoint for user-service.
Run with:  python -m app
"""
from flask import Flask
from .config import PORT, STORAGE_BACKEND, DATA_DIR
from .routes import users_bp


def create_app(repository=None):
    """
    Application factory.
    If `repository` is provided (e.g. in tests), it is used directly.
    Otherwise the backend is selected from STORAGE_BACKEND env var.
    """
    app = Flask(__name__)

    if repository is None:
        repository = _build_repository()

    # Make the repository available to the service layer via the app context
    app.config["REPOSITORY"] = repository

    app.register_blueprint(users_bp)
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

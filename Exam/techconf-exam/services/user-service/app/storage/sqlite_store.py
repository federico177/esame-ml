"""
SQLite repository backend for user-service.
Uses only stdlib sqlite3. Table is created on init if it doesn't exist.
"""
import os
import sqlite3
from ..repository import UserRepository

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    email       TEXT NOT NULL,
    company     TEXT,
    role        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

_COLUMNS = ["id", "first_name", "last_name", "email", "company", "role", "created_at", "updated_at"]


def _row_to_dict(row) -> dict:
    return dict(zip(_COLUMNS, row))


class SqliteRepository(UserRepository):

    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self._db_path = os.path.join(data_dir, "users.db")
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, user: dict) -> dict:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO users (id, first_name, last_name, email, company, role, created_at, updated_at)
                   VALUES (:id, :first_name, :last_name, :email, :company, :role, :created_at, :updated_at)""",
                user,
            )
        return dict(user)

    def get(self, user_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def update(self, user_id: str, data: dict) -> dict | None:
        existing = self.get(user_id)
        if existing is None:
            return None
        existing.update(data)
        with self._connect() as conn:
            conn.execute(
                """UPDATE users SET first_name=:first_name, last_name=:last_name, email=:email,
                   company=:company, role=:role, updated_at=:updated_at WHERE id=:id""",
                existing,
            )
        return existing

    def delete(self, user_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        query = "SELECT * FROM users WHERE 1=1"
        params: list = []

        if filters.get("role"):
            query += " AND role = ?"
            params.append(filters["role"])

        if filters.get("email"):
            query += " AND LOWER(email) = ?"
            params.append(filters["email"].lower())

        with self._connect() as conn:
            all_rows = conn.execute(query, params).fetchall()

        total = len(all_rows)
        start = (page - 1) * page_size
        end = start + page_size
        return [dict(r) for r in all_rows[start:end]], total

    def get_by_email(self, email: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE LOWER(email) = ?", (email.lower(),)
            ).fetchone()
        return dict(row) if row else None

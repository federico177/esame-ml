"""SQLite repository backend for feedback-service."""
import os, sqlite3
from ..repository import FeedbackRepository

_CREATE = """
CREATE TABLE IF NOT EXISTS feedbacks (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    event_id   TEXT NOT NULL,
    rating     INTEGER NOT NULL,
    comment    TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class SqliteRepository(FeedbackRepository):
    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self._db = os.path.join(data_dir, "feedbacks.db")
        with self._conn() as c:
            c.execute(_CREATE)

    def _conn(self):
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, fb: dict) -> dict:
        with self._conn() as c:
            c.execute("INSERT INTO feedbacks (id,user_id,event_id,rating,comment,created_at,updated_at)"
                      " VALUES (:id,:user_id,:event_id,:rating,:comment,:created_at,:updated_at)", fb)
        return dict(fb)

    def get(self, fb_id: str) -> "dict | None":
        with self._conn() as c:
            row = c.execute("SELECT * FROM feedbacks WHERE id=?", (fb_id,)).fetchone()
        return dict(row) if row else None

    def update(self, fb_id: str, data: dict) -> "dict | None":
        existing = self.get(fb_id)
        if not existing:
            return None
        existing.update(data)
        with self._conn() as c:
            c.execute("UPDATE feedbacks SET rating=:rating,comment=:comment,updated_at=:updated_at WHERE id=:id", existing)
        return existing

    def delete(self, fb_id: str) -> bool:
        with self._conn() as c:
            cur = c.execute("DELETE FROM feedbacks WHERE id=?", (fb_id,))
        return cur.rowcount > 0

    def list(self, filters: dict, page: int, page_size: int) -> tuple:
        q = "SELECT * FROM feedbacks WHERE 1=1"; p = []
        if filters.get("event_id"):
            q += " AND event_id=?"; p.append(filters["event_id"])
        if filters.get("user_id"):
            q += " AND user_id=?"; p.append(filters["user_id"])
        with self._conn() as c:
            rows = c.execute(q, p).fetchall()
        total = len(rows)
        start = (page - 1) * page_size
        return [dict(r) for r in rows[start:start + page_size]], total

    def find_by_user_event(self, user_id: str, event_id: str) -> "dict | None":
        with self._conn() as c:
            row = c.execute("SELECT * FROM feedbacks WHERE user_id=? AND event_id=?", (user_id, event_id)).fetchone()
        return dict(row) if row else None

    def list_by_event(self, event_id: str) -> list:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM feedbacks WHERE event_id=?", (event_id,)).fetchall()
        return [dict(r) for r in rows]


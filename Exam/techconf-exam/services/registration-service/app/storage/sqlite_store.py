"""SQLite repository backend for registration-service."""
import os, sqlite3
from ..repository import RegistrationRepository

_CREATE = """
CREATE TABLE IF NOT EXISTS registrations (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    event_id   TEXT NOT NULL,
    amount     REAL NOT NULL,
    status     TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class SqliteRepository(RegistrationRepository):

    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self._db = os.path.join(data_dir, "registrations.db")
        with self._conn() as c:
            c.execute(_CREATE)

    def _conn(self):
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, reg: dict) -> dict:
        with self._conn() as c:
            c.execute(
                "INSERT INTO registrations (id,user_id,event_id,amount,status,created_at,updated_at)"
                " VALUES (:id,:user_id,:event_id,:amount,:status,:created_at,:updated_at)", reg)
        return dict(reg)

    def get(self, reg_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM registrations WHERE id=?", (reg_id,)).fetchone()
        return dict(row) if row else None

    def update(self, reg_id: str, data: dict) -> dict | None:
        existing = self.get(reg_id)
        if not existing:
            return None
        existing.update(data)
        with self._conn() as c:
            c.execute("UPDATE registrations SET status=:status,updated_at=:updated_at WHERE id=:id", existing)
        return existing

    def delete(self, reg_id: str) -> bool:
        with self._conn() as c:
            cur = c.execute("DELETE FROM registrations WHERE id=?", (reg_id,))
        return cur.rowcount > 0

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        q = "SELECT * FROM registrations WHERE 1=1"
        p: list = []
        if filters.get("user_id"):
            q += " AND user_id=?"; p.append(filters["user_id"])
        if filters.get("event_id"):
            q += " AND event_id=?"; p.append(filters["event_id"])
        if filters.get("status"):
            q += " AND status=?"; p.append(filters["status"])
        with self._conn() as c:
            rows = c.execute(q, p).fetchall()
        total = len(rows)
        start = (page - 1) * page_size
        return [dict(r) for r in rows[start:start + page_size]], total

    def count_confirmed(self, event_id: str) -> int:
        with self._conn() as c:
            row = c.execute(
                "SELECT COUNT(*) FROM registrations WHERE event_id=? AND status='confirmed'",
                (event_id,)).fetchone()
        return row[0]

    def find_confirmed(self, user_id: str, event_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM registrations WHERE user_id=? AND event_id=? AND status='confirmed'",
                (user_id, event_id)).fetchone()
        return dict(row) if row else None

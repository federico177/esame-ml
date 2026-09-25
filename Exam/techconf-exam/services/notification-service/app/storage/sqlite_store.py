"""SQLite repository backend for notification-service."""
import os, sqlite3
from ..repository import NotificationRepository

_CREATE = """
CREATE TABLE IF NOT EXISTS notifications (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    channel    TEXT NOT NULL,
    subject    TEXT NOT NULL,
    body       TEXT NOT NULL,
    status     TEXT NOT NULL,
    sent_at    TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class SqliteRepository(NotificationRepository):
    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        self._db = os.path.join(data_dir, "notifications.db")
        with self._conn() as c:
            c.execute(_CREATE)

    def _conn(self):
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, n):
        with self._conn() as c:
            c.execute("INSERT INTO notifications (id,user_id,channel,subject,body,status,sent_at,created_at,updated_at)"
                      " VALUES (:id,:user_id,:channel,:subject,:body,:status,:sent_at,:created_at,:updated_at)", n)
        return dict(n)

    def get(self, n_id):
        with self._conn() as c:
            row = c.execute("SELECT * FROM notifications WHERE id=?", (n_id,)).fetchone()
        return dict(row) if row else None

    def update(self, n_id, data):
        existing = self.get(n_id)
        if not existing:
            return None
        existing.update(data)
        with self._conn() as c:
            c.execute("UPDATE notifications SET status=:status,sent_at=:sent_at,updated_at=:updated_at WHERE id=:id", existing)
        return existing

    def delete(self, n_id):
        with self._conn() as c:
            cur = c.execute("DELETE FROM notifications WHERE id=?", (n_id,))
        return cur.rowcount > 0

    def list(self, filters, page, page_size):
        q = "SELECT * FROM notifications WHERE 1=1"; p = []
        if filters.get("user_id"):
            q += " AND user_id=?"; p.append(filters["user_id"])
        if filters.get("status"):
            q += " AND status=?"; p.append(filters["status"])
        with self._conn() as c:
            rows = c.execute(q, p).fetchall()
        total = len(rows)
        start = (page - 1) * page_size
        return [dict(r) for r in rows[start:start + page_size]], total

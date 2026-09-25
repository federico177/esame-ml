"""SQLite repository backend for event-service."""
import os
import sqlite3
from ..repository import EventRepository

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT,
    organizer_id TEXT NOT NULL,
    venue        TEXT NOT NULL,
    city         TEXT NOT NULL,
    start_date   TEXT NOT NULL,
    end_date     TEXT NOT NULL,
    capacity     INTEGER NOT NULL,
    price        REAL NOT NULL,
    status       TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
"""

_COLUMNS = ["id", "title", "description", "organizer_id", "venue", "city",
            "start_date", "end_date", "capacity", "price", "status", "created_at", "updated_at"]


class SqliteRepository(EventRepository):

    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self._db_path = os.path.join(data_dir, "events.db")
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, event: dict) -> dict:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO events (id,title,description,organizer_id,venue,city,
                   start_date,end_date,capacity,price,status,created_at,updated_at)
                   VALUES (:id,:title,:description,:organizer_id,:venue,:city,
                   :start_date,:end_date,:capacity,:price,:status,:created_at,:updated_at)""",
                event,
            )
        return dict(event)

    def get(self, event_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        return dict(row) if row else None

    def update(self, event_id: str, data: dict) -> dict | None:
        existing = self.get(event_id)
        if existing is None:
            return None
        existing.update(data)
        with self._connect() as conn:
            conn.execute(
                """UPDATE events SET title=:title,description=:description,
                   organizer_id=:organizer_id,venue=:venue,city=:city,
                   start_date=:start_date,end_date=:end_date,capacity=:capacity,
                   price=:price,status=:status,updated_at=:updated_at WHERE id=:id""",
                existing,
            )
        return existing

    def delete(self, event_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM events WHERE id=?", (event_id,))
        return cur.rowcount > 0

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        query = "SELECT * FROM events WHERE 1=1"
        params: list = []

        if filters.get("status"):
            query += " AND status=?"
            params.append(filters["status"])

        if filters.get("city"):
            query += " AND LOWER(city)=?"
            params.append(filters["city"].lower())

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        total = len(rows)
        start = (page - 1) * page_size
        return [dict(r) for r in rows[start:start + page_size]], total

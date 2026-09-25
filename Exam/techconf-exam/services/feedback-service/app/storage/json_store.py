"""JSON file-based repository backend for feedback-service."""
import json, os
from ..repository import FeedbackRepository


class JsonRepository(FeedbackRepository):
    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "feedbacks.json")
        if not os.path.exists(self._path):
            self._write({})

    def _read(self) -> dict:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, store: dict):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)

    def create(self, fb: dict) -> dict:
        store = self._read(); store[fb["id"]] = fb; self._write(store)
        return dict(fb)

    def get(self, fb_id: str) -> "dict | None":
        f = self._read().get(fb_id)
        return dict(f) if f else None

    def update(self, fb_id: str, data: dict) -> "dict | None":
        store = self._read()
        if fb_id not in store:
            return None
        store[fb_id].update(data); self._write(store)
        return dict(store[fb_id])

    def delete(self, fb_id: str) -> bool:
        store = self._read()
        if fb_id not in store:
            return False
        del store[fb_id]; self._write(store)
        return True

    def list(self, filters: dict, page: int, page_size: int) -> tuple:
        items = list(self._read().values())
        if filters.get("event_id"):
            items = [f for f in items if f["event_id"] == filters["event_id"]]
        if filters.get("user_id"):
            items = [f for f in items if f["user_id"] == filters["user_id"]]
        total = len(items)
        start = (page - 1) * page_size
        return [dict(f) for f in items[start:start + page_size]], total

    def find_by_user_event(self, user_id: str, event_id: str) -> "dict | None":
        for f in self._read().values():
            if f["user_id"] == user_id and f["event_id"] == event_id:
                return dict(f)
        return None

    def list_by_event(self, event_id: str) -> list:
        return [dict(f) for f in self._read().values() if f["event_id"] == event_id]


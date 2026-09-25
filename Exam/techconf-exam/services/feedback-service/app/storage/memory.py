"""In-memory repository backend for feedback-service."""
from ..repository import FeedbackRepository


class MemoryRepository(FeedbackRepository):
    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self, fb: dict) -> dict:
        self._store[fb["id"]] = fb
        return dict(fb)

    def get(self, fb_id: str) -> "dict | None":
        f = self._store.get(fb_id)
        return dict(f) if f else None

    def update(self, fb_id: str, data: dict) -> "dict | None":
        f = self._store.get(fb_id)
        if f is None:
            return None
        f.update(data)
        self._store[fb_id] = f
        return dict(f)

    def delete(self, fb_id: str) -> bool:
        if fb_id in self._store:
            del self._store[fb_id]
            return True
        return False

    def list(self, filters: dict, page: int, page_size: int) -> tuple:
        items = list(self._store.values())
        if filters.get("event_id"):
            items = [f for f in items if f["event_id"] == filters["event_id"]]
        if filters.get("user_id"):
            items = [f for f in items if f["user_id"] == filters["user_id"]]
        total = len(items)
        start = (page - 1) * page_size
        return [dict(f) for f in items[start:start + page_size]], total

    def find_by_user_event(self, user_id: str, event_id: str) -> "dict | None":
        for f in self._store.values():
            if f["user_id"] == user_id and f["event_id"] == event_id:
                return dict(f)
        return None

    def list_by_event(self, event_id: str) -> list:
        return [dict(f) for f in self._store.values() if f["event_id"] == event_id]


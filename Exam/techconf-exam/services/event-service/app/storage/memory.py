"""In-memory repository backend for event-service."""
from ..repository import EventRepository


class MemoryRepository(EventRepository):

    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self, event: dict) -> dict:
        self._store[event["id"]] = event
        return dict(event)

    def get(self, event_id: str) -> dict | None:
        e = self._store.get(event_id)
        return dict(e) if e else None

    def update(self, event_id: str, data: dict) -> dict | None:
        e = self._store.get(event_id)
        if e is None:
            return None
        e.update(data)
        self._store[event_id] = e
        return dict(e)

    def delete(self, event_id: str) -> bool:
        if event_id in self._store:
            del self._store[event_id]
            return True
        return False

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        items = list(self._store.values())

        if filters.get("status"):
            items = [e for e in items if e.get("status") == filters["status"]]

        if filters.get("city"):
            city_lower = filters["city"].lower()
            items = [e for e in items if e.get("city", "").lower() == city_lower]

        total = len(items)
        start = (page - 1) * page_size
        return [dict(e) for e in items[start:start + page_size]], total

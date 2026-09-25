"""JSON file-based repository backend for event-service."""
import json
import os
from ..repository import EventRepository


class JsonRepository(EventRepository):

    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "events.json")
        if not os.path.exists(self._path):
            self._write({})

    def _read(self) -> dict:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, store: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)

    def create(self, event: dict) -> dict:
        store = self._read()
        store[event["id"]] = event
        self._write(store)
        return dict(event)

    def get(self, event_id: str) -> dict | None:
        store = self._read()
        e = store.get(event_id)
        return dict(e) if e else None

    def update(self, event_id: str, data: dict) -> dict | None:
        store = self._read()
        if event_id not in store:
            return None
        store[event_id].update(data)
        self._write(store)
        return dict(store[event_id])

    def delete(self, event_id: str) -> bool:
        store = self._read()
        if event_id not in store:
            return False
        del store[event_id]
        self._write(store)
        return True

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        items = list(self._read().values())

        if filters.get("status"):
            items = [e for e in items if e.get("status") == filters["status"]]

        if filters.get("city"):
            city_lower = filters["city"].lower()
            items = [e for e in items if e.get("city", "").lower() == city_lower]

        total = len(items)
        start = (page - 1) * page_size
        return [dict(e) for e in items[start:start + page_size]], total

"""JSON file-based repository backend for notification-service."""
import json, os
from ..repository import NotificationRepository


class JsonRepository(NotificationRepository):
    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "notifications.json")
        if not os.path.exists(self._path):
            self._write({})

    def _read(self):
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, store):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)

    def create(self, n):
        store = self._read(); store[n["id"]] = n; self._write(store)
        return dict(n)

    def get(self, n_id):
        x = self._read().get(n_id)
        return dict(x) if x else None

    def update(self, n_id, data):
        store = self._read()
        if n_id not in store:
            return None
        store[n_id].update(data); self._write(store)
        return dict(store[n_id])

    def delete(self, n_id):
        store = self._read()
        if n_id not in store:
            return False
        del store[n_id]; self._write(store)
        return True

    def list(self, filters, page, page_size):
        items = list(self._read().values())
        if filters.get("user_id"):
            items = [x for x in items if x["user_id"] == filters["user_id"]]
        if filters.get("status"):
            items = [x for x in items if x["status"] == filters["status"]]
        total = len(items)
        start = (page - 1) * page_size
        return [dict(x) for x in items[start:start + page_size]], total

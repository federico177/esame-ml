"""In-memory repository backend for notification-service."""
from ..repository import NotificationRepository


class MemoryRepository(NotificationRepository):
    def __init__(self):
        self._store = {}

    def create(self, n):
        self._store[n["id"]] = n
        return dict(n)

    def get(self, n_id):
        x = self._store.get(n_id)
        return dict(x) if x else None

    def update(self, n_id, data):
        x = self._store.get(n_id)
        if x is None:
            return None
        x.update(data)
        self._store[n_id] = x
        return dict(x)

    def delete(self, n_id):
        if n_id in self._store:
            del self._store[n_id]
            return True
        return False

    def list(self, filters, page, page_size):
        items = list(self._store.values())
        if filters.get("user_id"):
            items = [x for x in items if x["user_id"] == filters["user_id"]]
        if filters.get("status"):
            items = [x for x in items if x["status"] == filters["status"]]
        total = len(items)
        start = (page - 1) * page_size
        return [dict(x) for x in items[start:start + page_size]], total

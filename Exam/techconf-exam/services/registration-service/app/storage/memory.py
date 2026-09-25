"""In-memory repository backend for registration-service."""
from ..repository import RegistrationRepository


class MemoryRepository(RegistrationRepository):

    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self, reg: dict) -> dict:
        self._store[reg["id"]] = reg
        return dict(reg)

    def get(self, reg_id: str) -> dict | None:
        r = self._store.get(reg_id)
        return dict(r) if r else None

    def update(self, reg_id: str, data: dict) -> dict | None:
        r = self._store.get(reg_id)
        if r is None:
            return None
        r.update(data)
        self._store[reg_id] = r
        return dict(r)

    def delete(self, reg_id: str) -> bool:
        if reg_id in self._store:
            del self._store[reg_id]
            return True
        return False

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        items = list(self._store.values())
        if filters.get("user_id"):
            items = [r for r in items if r["user_id"] == filters["user_id"]]
        if filters.get("event_id"):
            items = [r for r in items if r["event_id"] == filters["event_id"]]
        if filters.get("status"):
            items = [r for r in items if r["status"] == filters["status"]]
        total = len(items)
        start = (page - 1) * page_size
        return [dict(r) for r in items[start:start + page_size]], total

    def count_confirmed(self, event_id: str) -> int:
        return sum(1 for r in self._store.values()
                   if r["event_id"] == event_id and r["status"] == "confirmed")

    def find_confirmed(self, user_id: str, event_id: str) -> dict | None:
        for r in self._store.values():
            if r["user_id"] == user_id and r["event_id"] == event_id and r["status"] == "confirmed":
                return dict(r)
        return None

"""JSON file-based repository backend for registration-service."""
import json, os
from ..repository import RegistrationRepository


class JsonRepository(RegistrationRepository):

    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "registrations.json")
        if not os.path.exists(self._path):
            self._write({})

    def _read(self) -> dict:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, store: dict):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)

    def create(self, reg: dict) -> dict:
        store = self._read()
        store[reg["id"]] = reg
        self._write(store)
        return dict(reg)

    def get(self, reg_id: str) -> dict | None:
        r = self._read().get(reg_id)
        return dict(r) if r else None

    def update(self, reg_id: str, data: dict) -> dict | None:
        store = self._read()
        if reg_id not in store:
            return None
        store[reg_id].update(data)
        self._write(store)
        return dict(store[reg_id])

    def delete(self, reg_id: str) -> bool:
        store = self._read()
        if reg_id not in store:
            return False
        del store[reg_id]
        self._write(store)
        return True

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        items = list(self._read().values())
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
        return sum(1 for r in self._read().values()
                   if r["event_id"] == event_id and r["status"] == "confirmed")

    def find_confirmed(self, user_id: str, event_id: str) -> dict | None:
        for r in self._read().values():
            if r["user_id"] == user_id and r["event_id"] == event_id and r["status"] == "confirmed":
                return dict(r)
        return None

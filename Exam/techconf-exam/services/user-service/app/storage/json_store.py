"""
JSON file-based repository backend for user-service.
Reads and writes DATA_DIR/users.json on every operation.
Uses only stdlib json.
"""
import json
import os
from ..repository import UserRepository


class JsonRepository(UserRepository):

    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "users.json")
        if not os.path.exists(self._path):
            self._write({})

    # ------------------------------------------------------------------ helpers

    def _read(self) -> dict:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, store: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------ interface

    def create(self, user: dict) -> dict:
        store = self._read()
        store[user["id"]] = user
        self._write(store)
        return dict(user)

    def get(self, user_id: str) -> dict | None:
        store = self._read()
        user = store.get(user_id)
        return dict(user) if user else None

    def update(self, user_id: str, data: dict) -> dict | None:
        store = self._read()
        if user_id not in store:
            return None
        store[user_id].update(data)
        self._write(store)
        return dict(store[user_id])

    def delete(self, user_id: str) -> bool:
        store = self._read()
        if user_id not in store:
            return False
        del store[user_id]
        self._write(store)
        return True

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        store = self._read()
        items = list(store.values())

        if filters.get("role"):
            items = [u for u in items if u.get("role") == filters["role"]]

        if filters.get("email"):
            email_lower = filters["email"].lower()
            items = [u for u in items if u.get("email", "").lower() == email_lower]

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return [dict(u) for u in items[start:end]], total

    def get_by_email(self, email: str) -> dict | None:
        store = self._read()
        email_lower = email.lower()
        for user in store.values():
            if user.get("email", "").lower() == email_lower:
                return dict(user)
        return None

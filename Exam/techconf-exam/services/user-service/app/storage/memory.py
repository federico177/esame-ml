"""
In-memory repository backend for user-service.
Data is lost on restart. Used by default and in unit tests.
"""
from ..repository import UserRepository


class MemoryRepository(UserRepository):

    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self, user: dict) -> dict:
        self._store[user["id"]] = user
        return dict(user)

    def get(self, user_id: str) -> dict | None:
        user = self._store.get(user_id)
        return dict(user) if user else None

    def update(self, user_id: str, data: dict) -> dict | None:
        user = self._store.get(user_id)
        if user is None:
            return None
        user.update(data)
        self._store[user_id] = user
        return dict(user)

    def delete(self, user_id: str) -> bool:
        if user_id in self._store:
            del self._store[user_id]
            return True
        return False

    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]:
        items = list(self._store.values())

        if "role" in filters and filters["role"]:
            items = [u for u in items if u.get("role") == filters["role"]]

        if "email" in filters and filters["email"]:
            email_lower = filters["email"].lower()
            items = [u for u in items if u.get("email", "").lower() == email_lower]

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return [dict(u) for u in items[start:end]], total

    def get_by_email(self, email: str) -> dict | None:
        email_lower = email.lower()
        for user in self._store.values():
            if user.get("email", "").lower() == email_lower:
                return dict(user)
        return None

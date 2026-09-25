"""
Abstract repository interface for user-service.
All storage backends must implement this class.
"""
from abc import ABC, abstractmethod


class UserRepository(ABC):

    @abstractmethod
    def create(self, user: dict) -> dict:
        """Persist a new user and return it."""

    @abstractmethod
    def get(self, user_id: str) -> dict | None:
        """Return a user by id, or None if not found."""

    @abstractmethod
    def update(self, user_id: str, data: dict) -> dict | None:
        """
        Merge `data` into the existing user, update `updated_at`,
        and return the updated user. Return None if not found.
        """

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Delete user by id. Return True if deleted, False if not found."""

    @abstractmethod
    def list(
        self,
        filters: dict,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """
        Return (items, total) where items is the paginated slice
        and total is the count of all matching users.

        Supported filters keys: 'role', 'email'.
        """

    @abstractmethod
    def get_by_email(self, email: str) -> dict | None:
        """Return a user whose stored (lowercase) email matches, or None."""

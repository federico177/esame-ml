"""Abstract repository interface for registration-service."""
from abc import ABC, abstractmethod


class RegistrationRepository(ABC):

    @abstractmethod
    def create(self, reg: dict) -> dict: ...

    @abstractmethod
    def get(self, reg_id: str) -> dict | None: ...

    @abstractmethod
    def update(self, reg_id: str, data: dict) -> dict | None: ...

    @abstractmethod
    def delete(self, reg_id: str) -> bool: ...

    @abstractmethod
    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]: ...

    @abstractmethod
    def count_confirmed(self, event_id: str) -> int:
        """Count registrations with status=confirmed for the given event."""

    @abstractmethod
    def find_confirmed(self, user_id: str, event_id: str) -> dict | None:
        """Return existing confirmed registration for (user_id, event_id), or None."""

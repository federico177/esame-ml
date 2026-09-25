"""
Abstract repository interface for event-service.
"""
from abc import ABC, abstractmethod


class EventRepository(ABC):

    @abstractmethod
    def create(self, event: dict) -> dict: ...

    @abstractmethod
    def get(self, event_id: str) -> dict | None: ...

    @abstractmethod
    def update(self, event_id: str, data: dict) -> dict | None: ...

    @abstractmethod
    def delete(self, event_id: str) -> bool: ...

    @abstractmethod
    def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]: ...

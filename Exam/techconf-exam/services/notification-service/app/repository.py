"""Abstract repository interface for notification-service."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class NotificationRepository(ABC):

    @abstractmethod
    def create(self, n: dict) -> dict: ...

    @abstractmethod
    def get(self, n_id: str) -> Optional[dict]: ...

    @abstractmethod
    def update(self, n_id: str, data: dict) -> Optional[dict]: ...

    @abstractmethod
    def delete(self, n_id: str) -> bool: ...

    @abstractmethod
    def list(self, filters: dict, page: int, page_size: int) -> Tuple[List[dict], int]: ...

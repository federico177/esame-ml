"""Abstract repository interface for feedback-service."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class FeedbackRepository(ABC):

    @abstractmethod
    def create(self, fb: dict) -> dict: ...

    @abstractmethod
    def get(self, fb_id: str) -> Optional[dict]: ...

    @abstractmethod
    def update(self, fb_id: str, data: dict) -> Optional[dict]: ...

    @abstractmethod
    def delete(self, fb_id: str) -> bool: ...

    @abstractmethod
    def list(self, filters: dict, page: int, page_size: int) -> Tuple[List[dict], int]: ...

    @abstractmethod
    def find_by_user_event(self, user_id: str, event_id: str) -> Optional[dict]: ...

    @abstractmethod
    def list_by_event(self, event_id: str) -> List[dict]: ...

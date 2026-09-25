"""HTTP clients for user-service and event-service."""
import requests as _requests
from .config import USER_SERVICE_URL, EVENT_SERVICE_URL


class DependencyError(Exception):
    pass


def get_user(user_id: str) -> dict | None:
    url = f"{USER_SERVICE_URL}/api/v1/users/{user_id}"
    try:
        r = _requests.get(url, timeout=2)
    except _requests.exceptions.RequestException as e:
        raise DependencyError(f"user-service unreachable: {e}") from e
    if r.status_code == 200:
        return r.json()
    if r.status_code == 404:
        return None
    raise DependencyError(f"user-service returned {r.status_code}")


def get_event(event_id: str) -> dict | None:
    url = f"{EVENT_SERVICE_URL}/api/v1/events/{event_id}"
    try:
        r = _requests.get(url, timeout=2)
    except _requests.exceptions.RequestException as e:
        raise DependencyError(f"event-service unreachable: {e}") from e
    if r.status_code == 200:
        return r.json()
    if r.status_code == 404:
        return None
    raise DependencyError(f"event-service returned {r.status_code}")

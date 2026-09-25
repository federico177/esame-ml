"""HTTP clients for registration-service and event-service."""
import requests as _requests
from .config import REGISTRATION_SERVICE_URL, EVENT_SERVICE_URL


class DependencyError(Exception):
    pass


def has_confirmed_registration(user_id: str, event_id: str) -> bool:
    url = f"{REGISTRATION_SERVICE_URL}/api/v1/registrations"
    params = {"user_id": user_id, "event_id": event_id, "status": "confirmed"}
    try:
        r = _requests.get(url, params=params, timeout=2)
    except _requests.exceptions.RequestException as e:
        raise DependencyError(f"registration-service unreachable: {e}") from e
    if r.status_code == 200:
        return r.json().get("total", 0) > 0
    raise DependencyError(f"registration-service returned {r.status_code}")


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

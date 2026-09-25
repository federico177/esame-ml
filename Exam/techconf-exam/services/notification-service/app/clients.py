"""HTTP clients for user-service and registration-service."""
import requests as _requests
from .config import USER_SERVICE_URL, REGISTRATION_SERVICE_URL


class DependencyError(Exception):
    pass


def get_user(user_id):
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


def list_confirmed_registrations(event_id):
    """Return the list of confirmed registrations for an event."""
    url = f"{REGISTRATION_SERVICE_URL}/api/v1/registrations"
    params = {"event_id": event_id, "status": "confirmed", "page_size": 100}
    try:
        r = _requests.get(url, params=params, timeout=2)
    except _requests.exceptions.RequestException as e:
        raise DependencyError(f"registration-service unreachable: {e}") from e
    if r.status_code == 200:
        return r.json().get("items", [])
    raise DependencyError(f"registration-service returned {r.status_code}")

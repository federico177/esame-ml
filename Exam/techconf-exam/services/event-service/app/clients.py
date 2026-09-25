"""
HTTP client for external service calls.
All inter-service URLs come from config.py — never hardcoded.
"""
import requests
from .config import USER_SERVICE_URL


class DependencyError(Exception):
    """Raised when a dependency service is unreachable or returns 5xx."""
    pass


def get_user(user_id: str) -> dict | None:
    """
    Call user-service GET /api/v1/users/{user_id}.
    Returns the user dict on 200, None on 404.
    Raises DependencyError on timeout, connection error, or 5xx.
    """
    url = f"{USER_SERVICE_URL}/api/v1/users/{user_id}"
    try:
        resp = requests.get(url, timeout=2)
    except requests.exceptions.RequestException as exc:
        raise DependencyError(f"user-service unreachable: {exc}") from exc

    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 404:
        return None
    raise DependencyError(f"user-service returned {resp.status_code}")

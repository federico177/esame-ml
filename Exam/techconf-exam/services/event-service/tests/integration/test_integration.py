"""
Integration tests for event-service.
Starts user-service as a real subprocess on a free port, then
starts event-service pointing at it — no mocks.
"""
import os
import sys
import time
import socket
import subprocess
import requests
import pytest

# Path to services root
SERVICES_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_ready(url: str, timeout: int = 10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"Service did not become ready at {url}")


@pytest.fixture(scope="module")
def user_service_url():
    """Start user-service on a free port; yield its base URL; stop it after tests."""
    port = _free_port()
    env = {**os.environ, "PORT": str(port), "STORAGE_BACKEND": "memory"}
    proc = subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=os.path.join(SERVICES_ROOT, "user-service"),
        env=env,
    )
    base_url = f"http://localhost:{port}"
    try:
        _wait_ready(f"{base_url}/health")
        yield base_url
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.fixture(scope="module")
def event_service_url(user_service_url):
    """Start event-service pointing at the real user-service."""
    port = _free_port()
    env = {
        **os.environ,
        "PORT": str(port),
        "STORAGE_BACKEND": "memory",
        "USER_SERVICE_URL": user_service_url,
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=os.path.join(SERVICES_ROOT, "event-service"),
        env=env,
    )
    base_url = f"http://localhost:{port}"
    try:
        _wait_ready(f"{base_url}/health")
        yield base_url
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def _create_organizer(user_service_url: str) -> dict:
    resp = requests.post(f"{user_service_url}/api/v1/users", json={
        "first_name": "Org",
        "last_name": "Test",
        "email": f"org_{int(time.time()*1000)}@test.com",
        "role": "organizer",
    })
    assert resp.status_code == 201
    return resp.json()


def _event_body(organizer_id: str) -> dict:
    return {
        "title": "Integration Test Conf",
        "organizer_id": organizer_id,
        "venue": "Auditorium",
        "city": "Roma",
        "start_date": "2026-11-01",
        "end_date": "2026-11-02",
        "capacity": 50,
        "price": 99.0,
    }


# ---------------------------------------------------------------------------
# Test 1: positive case
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-EVT-B01")
def test_create_event_with_valid_organizer(user_service_url, event_service_url):
    organizer = _create_organizer(user_service_url)
    resp = requests.post(
        f"{event_service_url}/api/v1/events",
        json=_event_body(organizer["id"]),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert data["organizer_id"] == organizer["id"]
    assert "Location" in resp.headers


# ---------------------------------------------------------------------------
# Test 2: non-existent organizer → 422
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-EVT-B01")
def test_create_event_organizer_not_found(event_service_url):
    resp = requests.post(
        f"{event_service_url}/api/v1/events",
        json=_event_body("00000000-0000-0000-0000-000000000000"),
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "REFERENCE_NOT_FOUND"


# ---------------------------------------------------------------------------
# Test 3: user-service down → 503
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-EVT-B05")
def test_create_event_dependency_unavailable():
    """Start event-service with USER_SERVICE_URL pointing to a closed port."""
    dead_port = _free_port()   # bind and immediately release — nothing listening
    svc_port = _free_port()
    env = {
        **os.environ,
        "PORT": str(svc_port),
        "STORAGE_BACKEND": "memory",
        "USER_SERVICE_URL": f"http://localhost:{dead_port}",
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=os.path.join(SERVICES_ROOT, "event-service"),
        env=env,
    )
    base_url = f"http://localhost:{svc_port}"
    try:
        _wait_ready(f"{base_url}/health")
        resp = requests.post(
            f"{base_url}/api/v1/events",
            json=_event_body("any-organizer-id"),
        )
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    finally:
        proc.terminate()
        proc.wait(timeout=5)

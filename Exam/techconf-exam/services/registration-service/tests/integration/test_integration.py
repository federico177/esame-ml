"""
Integration tests for registration-service.
Starts user-service and event-service as real subprocesses, no mocks.
"""
import os
import sys
import time
import socket
import subprocess
import requests
import pytest

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
            if requests.get(url, timeout=1).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"Service not ready at {url}")


def _start(service_dir: str, env_extra: dict):
    port = _free_port()
    env = {**os.environ, "PORT": str(port), "STORAGE_BACKEND": "memory", **env_extra}
    proc = subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=os.path.join(SERVICES_ROOT, service_dir),
        env=env,
    )
    return proc, f"http://localhost:{port}"


@pytest.fixture(scope="module")
def stack():
    """Start user, event, registration services wired together."""
    user_proc, user_url = _start("user-service", {})
    _wait_ready(f"{user_url}/health")

    event_proc, event_url = _start("event-service", {"USER_SERVICE_URL": user_url})
    _wait_ready(f"{event_url}/health")

    reg_proc, reg_url = _start("registration-service",
                               {"USER_SERVICE_URL": user_url, "EVENT_SERVICE_URL": event_url})
    _wait_ready(f"{reg_url}/health")

    try:
        yield {"user": user_url, "event": event_url, "registration": reg_url}
    finally:
        for p in (reg_proc, event_proc, user_proc):
            p.terminate()
            p.wait(timeout=5)


def _make_user(user_url, role="attendee"):
    r = requests.post(f"{user_url}/api/v1/users", json={
        "first_name": "T", "last_name": "U",
        "email": f"u_{int(time.time()*1000000)}@t.com", "role": role})
    assert r.status_code == 201
    return r.json()


def _make_published_event(event_url, organizer_id, capacity=5):
    r = requests.post(f"{event_url}/api/v1/events", json={
        "title": "Integration Conf", "organizer_id": organizer_id,
        "venue": "Aula", "city": "Roma",
        "start_date": "2026-11-01", "end_date": "2026-11-02",
        "capacity": capacity, "price": 99.0})
    assert r.status_code == 201
    eid = r.json()["id"]
    r2 = requests.patch(f"{event_url}/api/v1/events/{eid}", json={"status": "published"})
    assert r2.status_code == 200
    return r2.json()


@pytest.mark.req("REQ-REG-E01")
def test_register_positive(stack):
    organizer = _make_user(stack["user"], role="organizer")
    attendee = _make_user(stack["user"])
    event = _make_published_event(stack["event"], organizer["id"])
    r = requests.post(f"{stack['registration']}/api/v1/registrations",
                      json={"user_id": attendee["id"], "event_id": event["id"]})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "confirmed"
    assert body["amount"] == 99.0


@pytest.mark.req("REQ-REG-B01")
def test_register_user_not_found(stack):
    organizer = _make_user(stack["user"], role="organizer")
    event = _make_published_event(stack["event"], organizer["id"])
    r = requests.post(f"{stack['registration']}/api/v1/registrations",
                      json={"user_id": "00000000-0000-0000-0000-000000000000",
                            "event_id": event["id"]})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "REFERENCE_NOT_FOUND"


@pytest.mark.req("REQ-REG-B09")
def test_register_dependency_unavailable():
    """registration-service with USER_SERVICE_URL pointing to a closed port."""
    dead_port = _free_port()
    proc, base_url = _start("registration-service", {
        "USER_SERVICE_URL": f"http://localhost:{dead_port}",
        "EVENT_SERVICE_URL": f"http://localhost:{dead_port}",
    })
    try:
        _wait_ready(f"{base_url}/health")
        r = requests.post(f"{base_url}/api/v1/registrations",
                          json={"user_id": "u", "event_id": "e"})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    finally:
        proc.terminate()
        proc.wait(timeout=5)

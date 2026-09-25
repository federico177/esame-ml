"""Integration tests for notification-service — real user + registration services."""
import os, sys, time, socket, subprocess, requests, pytest

SERVICES_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def _free_port():
    with socket.socket() as s:
        s.bind(("", 0)); return s.getsockname()[1]


def _wait(url, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(url, timeout=1).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"not ready: {url}")


def _start(service_dir, env_extra):
    port = _free_port()
    env = {**os.environ, "PORT": str(port), "STORAGE_BACKEND": "memory", **env_extra}
    proc = subprocess.Popen([sys.executable, "-m", "app"],
                            cwd=os.path.join(SERVICES_ROOT, service_dir), env=env)
    return proc, f"http://localhost:{port}"


@pytest.fixture(scope="module")
def stack():
    up, uu = _start("user-service", {}); _wait(f"{uu}/health")
    ep, eu = _start("event-service", {"USER_SERVICE_URL": uu}); _wait(f"{eu}/health")
    rp, ru = _start("registration-service", {"USER_SERVICE_URL": uu, "EVENT_SERVICE_URL": eu}); _wait(f"{ru}/health")
    np_, nu = _start("notification-service", {"USER_SERVICE_URL": uu, "REGISTRATION_SERVICE_URL": ru}); _wait(f"{nu}/health")
    try:
        yield {"user": uu, "event": eu, "registration": ru, "notification": nu}
    finally:
        for p in (np_, rp, ep, up):
            p.terminate(); p.wait(timeout=5)


def _mk_user(uu, role="attendee"):
    return requests.post(f"{uu}/api/v1/users", json={"first_name": "T", "last_name": "U",
        "email": f"u_{int(time.time()*1000000)}@t.com", "role": role}).json()


@pytest.mark.req("REQ-NTF-E01")
def test_create_positive(stack):
    user = _mk_user(stack["user"])
    r = requests.post(f"{stack['notification']}/api/v1/notifications",
                      json={"user_id": user["id"], "channel": "email", "subject": "Hi", "body": "Hello"})
    assert r.status_code == 201
    assert r.json()["status"] == "queued"


@pytest.mark.req("REQ-NTF-B01")
def test_create_user_not_found(stack):
    r = requests.post(f"{stack['notification']}/api/v1/notifications",
                      json={"user_id": "00000000-0000-0000-0000-000000000000",
                            "channel": "email", "subject": "Hi", "body": "Hello"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "REFERENCE_NOT_FOUND"


@pytest.mark.req("REQ-NTF-B03")
def test_broadcast(stack):
    org = _mk_user(stack["user"], "organizer")
    a1 = _mk_user(stack["user"])
    a2 = _mk_user(stack["user"])
    ev = requests.post(f"{stack['event']}/api/v1/events", json={"title": "Broadcast Conf",
        "organizer_id": org["id"], "venue": "A", "city": "Roma", "start_date": "2026-11-01",
        "end_date": "2026-11-02", "capacity": 10, "price": 0.0}).json()
    requests.patch(f"{stack['event']}/api/v1/events/{ev['id']}", json={"status": "published"})
    for a in (a1, a2):
        requests.post(f"{stack['registration']}/api/v1/registrations",
                      json={"user_id": a["id"], "event_id": ev["id"]})
    r = requests.post(f"{stack['notification']}/api/v1/notifications/broadcast",
                      json={"event_id": ev["id"], "channel": "email", "subject": "Thanks", "body": "Bye"})
    assert r.status_code == 201
    assert r.json()["created"] == 2


@pytest.mark.req("REQ-NTF-B04")
def test_dependency_unavailable():
    dead = _free_port()
    proc, base = _start("notification-service", {
        "USER_SERVICE_URL": f"http://localhost:{dead}",
        "REGISTRATION_SERVICE_URL": f"http://localhost:{dead}"})
    try:
        _wait(f"{base}/health")
        r = requests.post(f"{base}/api/v1/notifications",
                          json={"user_id": "u", "channel": "email", "subject": "s", "body": "b"})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    finally:
        proc.terminate(); proc.wait(timeout=5)

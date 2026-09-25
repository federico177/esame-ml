"""Integration tests for feedback-service — starts real user/event/registration services."""
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
    rp, ru = _start("registration-service",
                    {"USER_SERVICE_URL": uu, "EVENT_SERVICE_URL": eu}); _wait(f"{ru}/health")
    fp, fu = _start("feedback-service",
                    {"REGISTRATION_SERVICE_URL": ru, "EVENT_SERVICE_URL": eu}); _wait(f"{fu}/health")
    try:
        yield {"user": uu, "event": eu, "registration": ru, "feedback": fu}
    finally:
        for p in (fp, rp, ep, up):
            p.terminate(); p.wait(timeout=5)


def _mk_user(uu, role="attendee"):
    r = requests.post(f"{uu}/api/v1/users", json={"first_name": "T", "last_name": "U",
        "email": f"u_{int(time.time()*1000000)}@t.com", "role": role})
    return r.json()


def _mk_event(eu, org):
    r = requests.post(f"{eu}/api/v1/events", json={"title": "Feedback Conf", "organizer_id": org,
        "venue": "A", "city": "Roma", "start_date": "2026-11-01", "end_date": "2026-11-02",
        "capacity": 10, "price": 20.0})
    eid = r.json()["id"]
    requests.patch(f"{eu}/api/v1/events/{eid}", json={"status": "published"})
    return eid


@pytest.mark.req("REQ-FBK-B01")
def test_feedback_positive(stack):
    org = _mk_user(stack["user"], "organizer")
    att = _mk_user(stack["user"])
    eid = _mk_event(stack["event"], org["id"])
    requests.post(f"{stack['registration']}/api/v1/registrations",
                  json={"user_id": att["id"], "event_id": eid})
    r = requests.post(f"{stack['feedback']}/api/v1/feedbacks",
                      json={"user_id": att["id"], "event_id": eid, "rating": 5, "comment": "top"})
    assert r.status_code == 201
    assert r.json()["rating"] == 5


@pytest.mark.req("REQ-FBK-B01")
def test_feedback_not_registered(stack):
    org = _mk_user(stack["user"], "organizer")
    att = _mk_user(stack["user"])
    eid = _mk_event(stack["event"], org["id"])
    # no registration created
    r = requests.post(f"{stack['feedback']}/api/v1/feedbacks",
                      json={"user_id": att["id"], "event_id": eid, "rating": 4})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "NOT_REGISTERED"


@pytest.mark.req("REQ-FBK-B04")
def test_feedback_dependency_unavailable():
    dead = _free_port()
    proc, base = _start("feedback-service", {
        "REGISTRATION_SERVICE_URL": f"http://localhost:{dead}",
        "EVENT_SERVICE_URL": f"http://localhost:{dead}"})
    try:
        _wait(f"{base}/health")
        r = requests.post(f"{base}/api/v1/feedbacks",
                          json={"user_id": "u", "event_id": "e", "rating": 3})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    finally:
        proc.terminate(); proc.wait(timeout=5)

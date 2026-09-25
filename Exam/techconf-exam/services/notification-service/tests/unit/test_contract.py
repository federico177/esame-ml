"""Contract tests for notification-service."""
import sys, os, pytest
import responses as rsps

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "contracts"))
from validator import assert_matches_contract

from app.__main__ import create_app
from app.storage.memory import MemoryRepository
from app.config import USER_SERVICE_URL, REGISTRATION_SERVICE_URL

USER_ID = "u-1"
EVENT_ID = "e-1"
USER = {"id": USER_ID, "first_name": "A", "last_name": "B", "email": "a@b.com", "role": "attendee",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}


class Adapter:
    def __init__(self, resp):
        self.status_code = resp.status_code; self.headers = resp.headers
        self.text = resp.get_data(as_text=True)
    def json(self):
        import json; return json.loads(self.text)


@pytest.fixture
def client():
    app = create_app(repository=MemoryRepository())
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _w(r):
    return Adapter(r)


def _mock_user():
    rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/{USER_ID}", json=USER, status=200)


def _create(client):
    return client.post("/api/v1/notifications",
                       json={"user_id": USER_ID, "channel": "email", "subject": "Hi", "body": "Hello"})


@pytest.mark.req("REQ-NTF-E07")
def test_health_contract(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert_matches_contract("notification", "get", "/health", _w(r))


@pytest.mark.req("REQ-NTF-E01")
@rsps.activate
def test_create_201_contract(client):
    _mock_user()
    r = _create(client)
    assert r.status_code == 201
    assert_matches_contract("notification", "post", "/api/v1/notifications", _w(r))


@pytest.mark.req("REQ-NTF-E01")
def test_create_422_contract(client):
    r = client.post("/api/v1/notifications", json={"user_id": USER_ID})
    assert r.status_code == 422
    assert_matches_contract("notification", "post", "/api/v1/notifications", _w(r))


@pytest.mark.req("REQ-NTF-E02")
@rsps.activate
def test_list_200_contract(client):
    _mock_user(); _create(client)
    r = client.get("/api/v1/notifications")
    assert r.status_code == 200
    assert_matches_contract("notification", "get", "/api/v1/notifications", _w(r))


@pytest.mark.req("REQ-NTF-E03")
@rsps.activate
def test_get_200_contract(client):
    _mock_user()
    created = _create(client).get_json()
    r = client.get(f"/api/v1/notifications/{created['id']}")
    assert r.status_code == 200
    assert_matches_contract("notification", "get", "/api/v1/notifications/{id}", _w(r))


@pytest.mark.req("REQ-NTF-E03")
def test_get_404_contract(client):
    r = client.get("/api/v1/notifications/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert_matches_contract("notification", "get", "/api/v1/notifications/{id}", _w(r))


@pytest.mark.req("REQ-NTF-E04")
@rsps.activate
def test_patch_200_contract(client):
    _mock_user()
    created = _create(client).get_json()
    r = client.patch(f"/api/v1/notifications/{created['id']}", json={"status": "sent"})
    assert r.status_code == 200
    assert_matches_contract("notification", "patch", "/api/v1/notifications/{id}", _w(r))


@pytest.mark.req("REQ-NTF-E05")
@rsps.activate
def test_delete_204_contract(client):
    _mock_user()
    created = _create(client).get_json()
    r = client.delete(f"/api/v1/notifications/{created['id']}")
    assert r.status_code == 204
    assert_matches_contract("notification", "delete", "/api/v1/notifications/{id}", _w(r))


@pytest.mark.req("REQ-NTF-B03")
@rsps.activate
def test_broadcast_201_contract(client):
    rsps.add(rsps.GET, f"{REGISTRATION_SERVICE_URL}/api/v1/registrations",
             json={"items": [{"user_id": "u1"}, {"user_id": "u2"}], "page": 1, "page_size": 100, "total": 2},
             status=200)
    r = client.post("/api/v1/notifications/broadcast",
                    json={"event_id": EVENT_ID, "channel": "email", "subject": "Thanks", "body": "Bye"})
    assert r.status_code == 201
    assert_matches_contract("notification", "post", "/api/v1/notifications/broadcast", _w(r))

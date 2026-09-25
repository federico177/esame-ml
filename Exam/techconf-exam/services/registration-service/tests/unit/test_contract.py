"""Contract tests — validate responses against registration-service.yaml."""
import sys
import os
import pytest
import responses as rsps

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "contracts"))
from validator import assert_matches_contract

from app.__main__ import create_app
from app.storage.memory import MemoryRepository
from app.config import USER_SERVICE_URL, EVENT_SERVICE_URL

USER_ID = "11111111-0000-0000-0000-000000000001"
EVENT_ID = "22222222-0000-0000-0000-000000000001"

USER = {"id": USER_ID, "first_name": "A", "last_name": "B", "email": "a@b.com",
        "role": "attendee", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}

EVENT = {"id": EVENT_ID, "title": "Conf", "organizer_id": "org", "venue": "v", "city": "Roma",
         "start_date": "2026-10-01", "end_date": "2026-10-02", "capacity": 5, "price": 49.0,
         "status": "published", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}


class FlaskTestResponseAdapter:
    def __init__(self, resp):
        self.status_code = resp.status_code
        self.headers = resp.headers
        self.text = resp.get_data(as_text=True)

    def json(self):
        import json
        return json.loads(self.text)


@pytest.fixture
def client():
    app = create_app(repository=MemoryRepository())
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _wrap(resp):
    return FlaskTestResponseAdapter(resp)


def _mock_deps():
    rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/{USER_ID}", json=USER, status=200)
    rsps.add(rsps.GET, f"{EVENT_SERVICE_URL}/api/v1/events/{EVENT_ID}", json=EVENT, status=200)


def _create(client):
    return client.post("/api/v1/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID})


@pytest.mark.req("REQ-REG-E08")
def test_health_contract(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert_matches_contract("registration", "get", "/health", _wrap(resp))


@pytest.mark.req("REQ-REG-E01")
@rsps.activate
def test_create_201_contract(client):
    _mock_deps()
    resp = _create(client)
    assert resp.status_code == 201
    assert "Location" in resp.headers
    assert_matches_contract("registration", "post", "/api/v1/registrations", _wrap(resp))


@pytest.mark.req("REQ-REG-E01")
def test_create_422_contract(client):
    resp = client.post("/api/v1/registrations", json={"user_id": USER_ID})
    assert resp.status_code == 422
    assert_matches_contract("registration", "post", "/api/v1/registrations", _wrap(resp))


@pytest.mark.req("REQ-REG-B09")
@rsps.activate
def test_create_503_contract(client):
    rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/{USER_ID}", json={}, status=503)
    resp = _create(client)
    assert resp.status_code == 503
    assert_matches_contract("registration", "post", "/api/v1/registrations", _wrap(resp))


@pytest.mark.req("REQ-REG-E02")
@rsps.activate
def test_list_200_contract(client):
    _mock_deps()
    _create(client)
    resp = client.get("/api/v1/registrations")
    assert resp.status_code == 200
    assert_matches_contract("registration", "get", "/api/v1/registrations", _wrap(resp))


@pytest.mark.req("REQ-REG-E03")
@rsps.activate
def test_get_200_contract(client):
    _mock_deps()
    created = _create(client).get_json()
    resp = client.get(f"/api/v1/registrations/{created['id']}")
    assert resp.status_code == 200
    assert_matches_contract("registration", "get", "/api/v1/registrations/{id}", _wrap(resp))


@pytest.mark.req("REQ-REG-E03")
def test_get_404_contract(client):
    resp = client.get("/api/v1/registrations/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert_matches_contract("registration", "get", "/api/v1/registrations/{id}", _wrap(resp))


@pytest.mark.req("REQ-REG-E04")
@rsps.activate
def test_patch_200_contract(client):
    _mock_deps()
    created = _create(client).get_json()
    resp = client.patch(f"/api/v1/registrations/{created['id']}", json={"status": "cancelled"})
    assert resp.status_code == 200
    assert_matches_contract("registration", "patch", "/api/v1/registrations/{id}", _wrap(resp))


@pytest.mark.req("REQ-REG-E05")
@rsps.activate
def test_delete_204_contract(client):
    _mock_deps()
    created = _create(client).get_json()
    resp = client.delete(f"/api/v1/registrations/{created['id']}")
    assert resp.status_code == 204
    assert_matches_contract("registration", "delete", "/api/v1/registrations/{id}", _wrap(resp))


@pytest.mark.req("REQ-REG-E07")
def test_put_405_contract(client):
    resp = client.put("/api/v1/registrations/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 405
    assert_matches_contract("registration", "put", "/api/v1/registrations/{id}", _wrap(resp))


@pytest.mark.req("REQ-REG-B08")
@rsps.activate
def test_stats_200_contract(client):
    _mock_deps()
    _create(client)
    rsps.add(rsps.GET, f"{EVENT_SERVICE_URL}/api/v1/events/{EVENT_ID}", json=EVENT, status=200)
    resp = client.get(f"/api/v1/registrations/stats?event_id={EVENT_ID}")
    assert resp.status_code == 200
    assert_matches_contract("registration", "get", "/api/v1/registrations/stats", _wrap(resp))

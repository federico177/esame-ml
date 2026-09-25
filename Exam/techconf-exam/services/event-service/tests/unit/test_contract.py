"""Contract tests — validate responses against contracts/openapi/event-service.yaml."""
import sys
import os
import pytest
import responses as rsps_lib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "contracts"))
from validator import assert_matches_contract

from app.__main__ import create_app
from app.storage.memory import MemoryRepository
from app.config import USER_SERVICE_URL

ORGANIZER = {
    "id": "aaaaaaaa-0000-0000-0000-000000000001",
    "first_name": "Org", "last_name": "One",
    "email": "org@test.com", "role": "organizer",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

VALID_BODY = {
    "title": "CloudConf 2026",
    "organizer_id": ORGANIZER["id"],
    "venue": "Auditorium Roma",
    "city": "Roma",
    "start_date": "2026-10-01",
    "end_date": "2026-10-02",
    "capacity": 100,
    "price": 49.00,
}


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


def _mock_organizer():
    rsps_lib.add(rsps_lib.GET,
                 f"{USER_SERVICE_URL}/api/v1/users/{ORGANIZER['id']}",
                 json=ORGANIZER, status=200)


@pytest.mark.req("REQ-EVT-E07")
def test_health_contract(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert_matches_contract("event", "get", "/health", _wrap(resp))


@pytest.mark.req("REQ-EVT-E01")
@rsps_lib.activate
def test_create_event_201_contract(client):
    _mock_organizer()
    resp = client.post("/api/v1/events", json=VALID_BODY)
    assert resp.status_code == 201
    assert "Location" in resp.headers
    assert_matches_contract("event", "post", "/api/v1/events", _wrap(resp))


@pytest.mark.req("REQ-EVT-E01")
def test_create_event_422_contract(client):
    resp = client.post("/api/v1/events", json={"title": "only"})
    assert resp.status_code == 422
    assert_matches_contract("event", "post", "/api/v1/events", _wrap(resp))


@pytest.mark.req("REQ-EVT-B05")
@rsps_lib.activate
def test_create_event_503_contract(client):
    rsps_lib.add(rsps_lib.GET,
                 f"{USER_SERVICE_URL}/api/v1/users/{ORGANIZER['id']}",
                 json={}, status=503)
    resp = client.post("/api/v1/events", json=VALID_BODY)
    assert resp.status_code == 503
    assert_matches_contract("event", "post", "/api/v1/events", _wrap(resp))


@pytest.mark.req("REQ-EVT-E02")
@rsps_lib.activate
def test_list_events_200_contract(client):
    _mock_organizer()
    client.post("/api/v1/events", json=VALID_BODY)
    resp = client.get("/api/v1/events")
    assert resp.status_code == 200
    assert_matches_contract("event", "get", "/api/v1/events", _wrap(resp))


@pytest.mark.req("REQ-EVT-E03")
@rsps_lib.activate
def test_get_event_200_contract(client):
    _mock_organizer()
    created = client.post("/api/v1/events", json=VALID_BODY).get_json()
    resp = client.get(f"/api/v1/events/{created['id']}")
    assert resp.status_code == 200
    assert_matches_contract("event", "get", "/api/v1/events/{id}", _wrap(resp))


@pytest.mark.req("REQ-EVT-E03")
def test_get_event_404_contract(client):
    resp = client.get("/api/v1/events/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert_matches_contract("event", "get", "/api/v1/events/{id}", _wrap(resp))


@pytest.mark.req("REQ-EVT-E04")
@rsps_lib.activate
def test_replace_event_200_contract(client):
    _mock_organizer()
    _mock_organizer()
    created = client.post("/api/v1/events", json=VALID_BODY).get_json()
    resp = client.put(f"/api/v1/events/{created['id']}", json=VALID_BODY)
    assert resp.status_code == 200
    assert_matches_contract("event", "put", "/api/v1/events/{id}", _wrap(resp))


@pytest.mark.req("REQ-EVT-E05")
@rsps_lib.activate
def test_patch_event_200_contract(client):
    _mock_organizer()
    created = client.post("/api/v1/events", json=VALID_BODY).get_json()
    resp = client.patch(f"/api/v1/events/{created['id']}", json={"title": "Patched Title"})
    assert resp.status_code == 200
    assert_matches_contract("event", "patch", "/api/v1/events/{id}", _wrap(resp))


@pytest.mark.req("REQ-EVT-E06")
@rsps_lib.activate
def test_delete_event_204_contract(client):
    _mock_organizer()
    created = client.post("/api/v1/events", json=VALID_BODY).get_json()
    resp = client.delete(f"/api/v1/events/{created['id']}")
    assert resp.status_code == 204
    assert_matches_contract("event", "delete", "/api/v1/events/{id}", _wrap(resp))

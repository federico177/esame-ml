"""Contract tests for feedback-service."""
import sys, os, pytest
import responses as rsps

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "contracts"))
from validator import assert_matches_contract

from app.__main__ import create_app
from app.storage.memory import MemoryRepository
from app.config import REGISTRATION_SERVICE_URL, EVENT_SERVICE_URL

USER_ID = "u-1"
EVENT_ID = "e-1"
EVENT = {"id": EVENT_ID, "title": "Conf", "organizer_id": "o", "venue": "v", "city": "Roma",
         "start_date": "2026-10-01", "end_date": "2026-10-02", "capacity": 5, "price": 10.0,
         "status": "published", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}


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


def _mock_registered():
    rsps.add(rsps.GET, f"{REGISTRATION_SERVICE_URL}/api/v1/registrations",
             json={"items": [], "page": 1, "page_size": 20, "total": 1}, status=200)


def _mock_event():
    rsps.add(rsps.GET, f"{EVENT_SERVICE_URL}/api/v1/events/{EVENT_ID}", json=EVENT, status=200)


def _create(client):
    return client.post("/api/v1/feedbacks", json={"user_id": USER_ID, "event_id": EVENT_ID, "rating": 5})


@pytest.mark.req("REQ-FBK-E07")
def test_health_contract(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert_matches_contract("feedback", "get", "/health", _w(r))


@pytest.mark.req("REQ-FBK-E01")
@rsps.activate
def test_create_201_contract(client):
    _mock_registered()
    r = _create(client)
    assert r.status_code == 201
    assert_matches_contract("feedback", "post", "/api/v1/feedbacks", _w(r))


@pytest.mark.req("REQ-FBK-E01")
def test_create_422_contract(client):
    r = client.post("/api/v1/feedbacks", json={"user_id": USER_ID})
    assert r.status_code == 422
    assert_matches_contract("feedback", "post", "/api/v1/feedbacks", _w(r))


@pytest.mark.req("REQ-FBK-E02")
@rsps.activate
def test_list_200_contract(client):
    _mock_registered(); _create(client)
    r = client.get("/api/v1/feedbacks")
    assert r.status_code == 200
    assert_matches_contract("feedback", "get", "/api/v1/feedbacks", _w(r))


@pytest.mark.req("REQ-FBK-E03")
@rsps.activate
def test_get_200_contract(client):
    _mock_registered()
    created = _create(client).get_json()
    r = client.get(f"/api/v1/feedbacks/{created['id']}")
    assert r.status_code == 200
    assert_matches_contract("feedback", "get", "/api/v1/feedbacks/{id}", _w(r))


@pytest.mark.req("REQ-FBK-E03")
def test_get_404_contract(client):
    r = client.get("/api/v1/feedbacks/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert_matches_contract("feedback", "get", "/api/v1/feedbacks/{id}", _w(r))


@pytest.mark.req("REQ-FBK-E04")
@rsps.activate
def test_patch_200_contract(client):
    _mock_registered()
    created = _create(client).get_json()
    r = client.patch(f"/api/v1/feedbacks/{created['id']}", json={"rating": 3})
    assert r.status_code == 200
    assert_matches_contract("feedback", "patch", "/api/v1/feedbacks/{id}", _w(r))


@pytest.mark.req("REQ-FBK-E05")
@rsps.activate
def test_delete_204_contract(client):
    _mock_registered()
    created = _create(client).get_json()
    r = client.delete(f"/api/v1/feedbacks/{created['id']}")
    assert r.status_code == 204
    assert_matches_contract("feedback", "delete", "/api/v1/feedbacks/{id}", _w(r))


@pytest.mark.req("REQ-FBK-B03")
@rsps.activate
def test_summary_200_contract(client):
    _mock_registered(); _create(client)
    _mock_event()
    r = client.get(f"/api/v1/feedbacks/summary?event_id={EVENT_ID}")
    assert r.status_code == 200
    assert_matches_contract("feedback", "get", "/api/v1/feedbacks/summary", _w(r))

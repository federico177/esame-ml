"""
Contract tests — validate HTTP responses against contracts/openapi/user-service.yaml.
At least 1 test per endpoint.
REQ-USR-E01 through REQ-USR-E07
"""
import sys
import os
import pytest

# Make the contracts validator importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "contracts"))
from validator import assert_matches_contract

from app.__main__ import create_app
from app.storage.memory import MemoryRepository


class FlaskTestResponseAdapter:
    """
    Wraps a Flask test client response so that validator.py can call
    response.json() as a method (like requests.Response) instead of accessing
    the .json attribute that the test client exposes.
    """
    def __init__(self, resp):
        self._resp = resp
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


def _create_user(client, email="contract@test.com"):
    return client.post("/api/v1/users", json={
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "role": "attendee",
    })


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E07")
def test_health_contract(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert_matches_contract("user", "get", "/health", _wrap(resp))


# ---------------------------------------------------------------------------
# POST /api/v1/users
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E01")
def test_create_user_201_contract(client):
    resp = _create_user(client)
    assert resp.status_code == 201
    assert "Location" in resp.headers
    assert_matches_contract("user", "post", "/api/v1/users", _wrap(resp))


@pytest.mark.req("REQ-USR-E01")
def test_create_user_422_contract(client):
    resp = client.post("/api/v1/users", json={"first_name": "Only"})
    assert resp.status_code == 422
    assert_matches_contract("user", "post", "/api/v1/users", _wrap(resp))


@pytest.mark.req("REQ-USR-B01")
def test_create_user_409_contract(client):
    _create_user(client, "dup@test.com")
    resp = _create_user(client, "dup@test.com")
    assert resp.status_code == 409
    assert_matches_contract("user", "post", "/api/v1/users", _wrap(resp))


# ---------------------------------------------------------------------------
# GET /api/v1/users
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E02")
def test_list_users_200_contract(client):
    _create_user(client)
    resp = client.get("/api/v1/users")
    assert resp.status_code == 200
    assert_matches_contract("user", "get", "/api/v1/users", _wrap(resp))


# ---------------------------------------------------------------------------
# GET /api/v1/users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E03")
def test_get_user_200_contract(client):
    created = _create_user(client).get_json()
    resp = client.get(f"/api/v1/users/{created['id']}")
    assert resp.status_code == 200
    assert_matches_contract("user", "get", "/api/v1/users/{id}", _wrap(resp))


@pytest.mark.req("REQ-USR-E03")
def test_get_user_404_contract(client):
    resp = client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert_matches_contract("user", "get", "/api/v1/users/{id}", _wrap(resp))


# ---------------------------------------------------------------------------
# PUT /api/v1/users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E04")
def test_replace_user_200_contract(client):
    created = _create_user(client, "put@test.com").get_json()
    resp = client.put(f"/api/v1/users/{created['id']}", json={
        "first_name": "New", "last_name": "Name", "email": "put2@test.com"
    })
    assert resp.status_code == 200
    assert_matches_contract("user", "put", "/api/v1/users/{id}", _wrap(resp))


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E05")
def test_patch_user_200_contract(client):
    created = _create_user(client, "patch@test.com").get_json()
    resp = client.patch(f"/api/v1/users/{created['id']}", json={"first_name": "Patched"})
    assert resp.status_code == 200
    assert_matches_contract("user", "patch", "/api/v1/users/{id}", _wrap(resp))


# ---------------------------------------------------------------------------
# DELETE /api/v1/users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E06")
def test_delete_user_204_contract(client):
    created = _create_user(client, "del@test.com").get_json()
    resp = client.delete(f"/api/v1/users/{created['id']}")
    assert resp.status_code == 204
    assert_matches_contract("user", "delete", "/api/v1/users/{id}", _wrap(resp))

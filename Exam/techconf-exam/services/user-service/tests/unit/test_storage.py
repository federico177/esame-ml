"""
Unit tests for all three storage backends — parametrized.
REQ-USR-E01
"""
import pytest
from app.storage.memory import MemoryRepository
from app.storage.json_store import JsonRepository
from app.storage.sqlite_store import SqliteRepository


def _make_user(n=1):
    return {
        "id": f"00000000-0000-0000-0000-{n:012d}",
        "first_name": f"First{n}",
        "last_name": f"Last{n}",
        "email": f"user{n}@test.com",
        "company": None,
        "role": "attendee",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


@pytest.fixture(params=["memory", "json", "sqlite"])
def repo(request, tmp_path):
    backend = request.param
    if backend == "memory":
        return MemoryRepository()
    elif backend == "json":
        return JsonRepository(str(tmp_path))
    else:
        return SqliteRepository(str(tmp_path))


@pytest.mark.req("REQ-USR-E01")
def test_create_and_get(repo):
    user = _make_user(1)
    created = repo.create(user)
    assert created["id"] == user["id"]
    fetched = repo.get(user["id"])
    assert fetched is not None
    assert fetched["email"] == user["email"]


@pytest.mark.req("REQ-USR-E01")
def test_get_not_found(repo):
    assert repo.get("nonexistent-id") is None


@pytest.mark.req("REQ-USR-E01")
def test_update(repo):
    user = _make_user(2)
    repo.create(user)
    updated = repo.update(user["id"], {"first_name": "Changed", "updated_at": "2026-06-01T00:00:00Z"})
    assert updated["first_name"] == "Changed"
    assert repo.get(user["id"])["first_name"] == "Changed"


@pytest.mark.req("REQ-USR-E01")
def test_update_not_found(repo):
    result = repo.update("nonexistent-id", {"first_name": "X"})
    assert result is None


@pytest.mark.req("REQ-USR-E01")
def test_delete(repo):
    user = _make_user(3)
    repo.create(user)
    assert repo.delete(user["id"]) is True
    assert repo.get(user["id"]) is None


@pytest.mark.req("REQ-USR-E01")
def test_delete_not_found(repo):
    assert repo.delete("nonexistent-id") is False


@pytest.mark.req("REQ-USR-B03")
def test_list_pagination(repo):
    for i in range(1, 6):
        repo.create(_make_user(i))
    items, total = repo.list({}, page=1, page_size=3)
    assert total == 5
    assert len(items) == 3
    items2, _ = repo.list({}, page=2, page_size=3)
    assert len(items2) == 2


@pytest.mark.req("REQ-USR-B03")
def test_list_filter_role(repo):
    u1 = {**_make_user(10), "role": "organizer"}
    u2 = {**_make_user(11), "role": "attendee"}
    repo.create(u1)
    repo.create(u2)
    items, total = repo.list({"role": "organizer"}, page=1, page_size=20)
    assert total == 1
    assert items[0]["role"] == "organizer"


@pytest.mark.req("REQ-USR-B03")
def test_list_filter_email(repo):
    repo.create(_make_user(20))
    repo.create(_make_user(21))
    items, total = repo.list({"email": "user20@test.com"}, page=1, page_size=20)
    assert total == 1
    assert items[0]["email"] == "user20@test.com"


@pytest.mark.req("REQ-USR-B01")
def test_get_by_email(repo):
    user = _make_user(30)
    repo.create(user)
    found = repo.get_by_email("USER30@TEST.COM")
    assert found is not None
    assert found["id"] == user["id"]


@pytest.mark.req("REQ-USR-B01")
def test_get_by_email_not_found(repo):
    assert repo.get_by_email("nobody@nowhere.com") is None

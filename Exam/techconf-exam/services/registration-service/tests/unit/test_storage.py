"""Unit tests for all three storage backends — parametrized."""
import pytest
from app.storage.memory import MemoryRepository
from app.storage.json_store import JsonRepository
from app.storage.sqlite_store import SqliteRepository


def _make_reg(n=1, user_id="user-1", event_id="event-1", status="confirmed"):
    return {
        "id": f"00000000-0000-0000-0000-{n:012d}",
        "user_id": user_id,
        "event_id": event_id,
        "amount": 49.0,
        "status": status,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


@pytest.fixture(params=["memory", "json", "sqlite"])
def repo(request, tmp_path):
    if request.param == "memory":
        return MemoryRepository()
    elif request.param == "json":
        return JsonRepository(str(tmp_path))
    else:
        return SqliteRepository(str(tmp_path))


@pytest.mark.req("REQ-REG-E01")
def test_create_and_get(repo):
    r = _make_reg(1)
    repo.create(r)
    fetched = repo.get(r["id"])
    assert fetched is not None
    assert fetched["user_id"] == r["user_id"]


@pytest.mark.req("REQ-REG-E03")
def test_get_not_found(repo):
    assert repo.get("nonexistent") is None


@pytest.mark.req("REQ-REG-B07")
def test_update(repo):
    r = _make_reg(2)
    repo.create(r)
    updated = repo.update(r["id"], {"status": "cancelled", "updated_at": "2026-06-01T00:00:00Z"})
    assert updated["status"] == "cancelled"


@pytest.mark.req("REQ-REG-E05")
def test_delete(repo):
    r = _make_reg(3)
    repo.create(r)
    assert repo.delete(r["id"]) is True
    assert repo.get(r["id"]) is None


@pytest.mark.req("REQ-REG-E05")
def test_delete_not_found(repo):
    assert repo.delete("nonexistent") is False


@pytest.mark.req("REQ-REG-B05")
def test_count_confirmed(repo):
    repo.create(_make_reg(10, event_id="ev-A", status="confirmed"))
    repo.create(_make_reg(11, event_id="ev-A", status="confirmed"))
    repo.create(_make_reg(12, event_id="ev-A", status="cancelled"))
    repo.create(_make_reg(13, event_id="ev-B", status="confirmed"))
    assert repo.count_confirmed("ev-A") == 2
    assert repo.count_confirmed("ev-B") == 1


@pytest.mark.req("REQ-REG-B04")
def test_find_confirmed(repo):
    repo.create(_make_reg(20, user_id="u1", event_id="ev-X", status="confirmed"))
    found = repo.find_confirmed("u1", "ev-X")
    assert found is not None
    assert repo.find_confirmed("u1", "ev-Y") is None


@pytest.mark.req("REQ-REG-B04")
def test_find_confirmed_ignores_cancelled(repo):
    repo.create(_make_reg(21, user_id="u2", event_id="ev-Z", status="cancelled"))
    assert repo.find_confirmed("u2", "ev-Z") is None


@pytest.mark.req("REQ-REG-E02")
def test_list_filters(repo):
    repo.create(_make_reg(30, user_id="ua", event_id="ea", status="confirmed"))
    repo.create(_make_reg(31, user_id="ua", event_id="eb", status="cancelled"))
    repo.create(_make_reg(32, user_id="ub", event_id="ea", status="confirmed"))

    items, total = repo.list({"user_id": "ua"}, 1, 20)
    assert total == 2

    items, total = repo.list({"event_id": "ea"}, 1, 20)
    assert total == 2

    items, total = repo.list({"status": "confirmed"}, 1, 20)
    assert total == 2

    items, total = repo.list({"user_id": "ua", "status": "confirmed"}, 1, 20)
    assert total == 1


@pytest.mark.req("REQ-REG-E02")
def test_list_pagination(repo):
    for i in range(1, 6):
        repo.create(_make_reg(i + 100))
    items, total = repo.list({}, 1, 3)
    assert total == 5
    assert len(items) == 3

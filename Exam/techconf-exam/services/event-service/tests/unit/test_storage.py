"""Unit tests for all three storage backends — parametrized."""
import pytest
from app.storage.memory import MemoryRepository
from app.storage.json_store import JsonRepository
from app.storage.sqlite_store import SqliteRepository


def _make_event(n=1, city="Roma", status="draft"):
    return {
        "id": f"00000000-0000-0000-0000-{n:012d}",
        "title": f"Event {n}",
        "description": None,
        "organizer_id": "org-00000001",
        "venue": "Auditorium",
        "city": city,
        "start_date": "2026-10-01",
        "end_date": "2026-10-02",
        "capacity": 100,
        "price": 49.0,
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


@pytest.mark.req("REQ-EVT-E01")
def test_create_and_get(repo):
    e = _make_event(1)
    repo.create(e)
    fetched = repo.get(e["id"])
    assert fetched is not None
    assert fetched["title"] == e["title"]


@pytest.mark.req("REQ-EVT-E01")
def test_get_not_found(repo):
    assert repo.get("nonexistent") is None


@pytest.mark.req("REQ-EVT-E01")
def test_update(repo):
    e = _make_event(2)
    repo.create(e)
    updated = repo.update(e["id"], {"title": "Changed", "updated_at": "2026-06-01T00:00:00Z"})
    assert updated["title"] == "Changed"


@pytest.mark.req("REQ-EVT-E01")
def test_update_not_found(repo):
    assert repo.update("nonexistent", {"title": "X"}) is None


@pytest.mark.req("REQ-EVT-E01")
def test_delete(repo):
    e = _make_event(3)
    repo.create(e)
    assert repo.delete(e["id"]) is True
    assert repo.get(e["id"]) is None


@pytest.mark.req("REQ-EVT-E01")
def test_delete_not_found(repo):
    assert repo.delete("nonexistent") is False


@pytest.mark.req("REQ-EVT-B06")
def test_list_filter_status(repo):
    repo.create(_make_event(10, status="draft"))
    repo.create(_make_event(11, status="published"))
    items, total = repo.list({"status": "draft"}, 1, 20)
    assert total == 1
    assert items[0]["status"] == "draft"


@pytest.mark.req("REQ-EVT-B06")
def test_list_filter_city(repo):
    repo.create(_make_event(20, city="Roma"))
    repo.create(_make_event(21, city="Milano"))
    items, total = repo.list({"city": "roma"}, 1, 20)
    assert total == 1
    assert items[0]["city"] == "Roma"


@pytest.mark.req("REQ-EVT-E02")
def test_list_pagination(repo):
    for i in range(1, 6):
        repo.create(_make_event(i + 100))
    items, total = repo.list({}, 1, 3)
    assert total == 5
    assert len(items) == 3

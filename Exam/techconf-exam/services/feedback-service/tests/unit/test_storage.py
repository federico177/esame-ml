"""Unit tests for all three feedback storage backends."""
import pytest
from app.storage.memory import MemoryRepository
from app.storage.json_store import JsonRepository
from app.storage.sqlite_store import SqliteRepository


def _make_fb(n=1, user_id="u-1", event_id="e-1", rating=5):
    return {"id": f"00000000-0000-0000-0000-{n:012d}", "user_id": user_id, "event_id": event_id,
            "rating": rating, "comment": None,
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}


@pytest.fixture(params=["memory", "json", "sqlite"])
def repo(request, tmp_path):
    if request.param == "memory":
        return MemoryRepository()
    elif request.param == "json":
        return JsonRepository(str(tmp_path))
    else:
        return SqliteRepository(str(tmp_path))


@pytest.mark.req("REQ-FBK-E01")
def test_create_and_get(repo):
    fb = _make_fb(1); repo.create(fb)
    assert repo.get(fb["id"])["rating"] == 5


@pytest.mark.req("REQ-FBK-E03")
def test_get_not_found(repo):
    assert repo.get("nope") is None


@pytest.mark.req("REQ-FBK-E04")
def test_update(repo):
    fb = _make_fb(2); repo.create(fb)
    updated = repo.update(fb["id"], {"rating": 3, "comment": "ok", "updated_at": "2026-06-01T00:00:00Z"})
    assert updated["rating"] == 3


@pytest.mark.req("REQ-FBK-E05")
def test_delete(repo):
    fb = _make_fb(3); repo.create(fb)
    assert repo.delete(fb["id"]) is True
    assert repo.get(fb["id"]) is None


@pytest.mark.req("REQ-FBK-E05")
def test_delete_not_found(repo):
    assert repo.delete("nope") is False


@pytest.mark.req("REQ-FBK-B02")
def test_find_by_user_event(repo):
    repo.create(_make_fb(10, user_id="ua", event_id="ex"))
    assert repo.find_by_user_event("ua", "ex") is not None
    assert repo.find_by_user_event("ua", "ey") is None


@pytest.mark.req("REQ-FBK-B03")
def test_list_by_event(repo):
    repo.create(_make_fb(20, event_id="ez", rating=4))
    repo.create(_make_fb(21, event_id="ez", rating=2))
    repo.create(_make_fb(22, event_id="other", rating=5))
    fbs = repo.list_by_event("ez")
    assert len(fbs) == 2


@pytest.mark.req("REQ-FBK-E02")
def test_list_filters_and_pagination(repo):
    for i in range(1, 6):
        repo.create(_make_fb(i + 100, user_id="uu", event_id="ee"))
    items, total = repo.list({"event_id": "ee"}, 1, 3)
    assert total == 5
    assert len(items) == 3

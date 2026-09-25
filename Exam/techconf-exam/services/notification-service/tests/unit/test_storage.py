"""Unit tests for all three notification storage backends."""
import pytest
from app.storage.memory import MemoryRepository
from app.storage.json_store import JsonRepository
from app.storage.sqlite_store import SqliteRepository


def _make(n=1, user_id="u-1", status="queued"):
    return {"id": f"00000000-0000-0000-0000-{n:012d}", "user_id": user_id, "channel": "email",
            "subject": "s", "body": "b", "status": status, "sent_at": None,
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}


@pytest.fixture(params=["memory", "json", "sqlite"])
def repo(request, tmp_path):
    if request.param == "memory":
        return MemoryRepository()
    elif request.param == "json":
        return JsonRepository(str(tmp_path))
    else:
        return SqliteRepository(str(tmp_path))


@pytest.mark.req("REQ-NTF-E01")
def test_create_and_get(repo):
    n = _make(1); repo.create(n)
    assert repo.get(n["id"])["subject"] == "s"


@pytest.mark.req("REQ-NTF-E03")
def test_get_not_found(repo):
    assert repo.get("nope") is None


@pytest.mark.req("REQ-NTF-B02")
def test_update(repo):
    n = _make(2); repo.create(n)
    updated = repo.update(n["id"], {"status": "sent", "sent_at": "2026-06-01T00:00:00Z", "updated_at": "2026-06-01T00:00:00Z"})
    assert updated["status"] == "sent"
    assert updated["sent_at"] == "2026-06-01T00:00:00Z"


@pytest.mark.req("REQ-NTF-E05")
def test_delete(repo):
    n = _make(3); repo.create(n)
    assert repo.delete(n["id"]) is True
    assert repo.get(n["id"]) is None


@pytest.mark.req("REQ-NTF-E05")
def test_delete_not_found(repo):
    assert repo.delete("nope") is False


@pytest.mark.req("REQ-NTF-E02")
def test_list_filters(repo):
    repo.create(_make(10, user_id="ua", status="queued"))
    repo.create(_make(11, user_id="ua", status="sent"))
    repo.create(_make(12, user_id="ub", status="queued"))
    items, total = repo.list({"user_id": "ua"}, 1, 20)
    assert total == 2
    items, total = repo.list({"status": "queued"}, 1, 20)
    assert total == 2
    items, total = repo.list({"user_id": "ua", "status": "sent"}, 1, 20)
    assert total == 1


@pytest.mark.req("REQ-NTF-E02")
def test_list_pagination(repo):
    for i in range(1, 6):
        repo.create(_make(i + 100))
    items, total = repo.list({}, 1, 3)
    assert total == 5
    assert len(items) == 3

"""Unit tests for notification service.py with mocked clients."""
import pytest
import responses as rsps
from app.storage.memory import MemoryRepository
from app import service as svc
from app.config import USER_SERVICE_URL, REGISTRATION_SERVICE_URL

USER_ID = "u-1"
EVENT_ID = "e-1"
USER = {"id": USER_ID, "first_name": "A", "last_name": "B", "email": "a@b.com", "role": "attendee",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}


@pytest.fixture
def repo():
    return MemoryRepository()


def _mock_user(user=USER):
    rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/{USER_ID}",
             json=user if user else {}, status=200 if user else 404)


def _valid():
    return {"user_id": USER_ID, "channel": "email", "subject": "Hi", "body": "Hello"}


@pytest.mark.req("REQ-NTF-E01")
@rsps.activate
def test_create_valid(repo):
    _mock_user()
    n = svc.create_notification(repo, _valid())
    assert n["status"] == "queued"
    assert n["sent_at"] is None


@pytest.mark.req("REQ-NTF-E01")
def test_create_missing_field(repo):
    with pytest.raises(svc.ValidationError):
        svc.create_notification(repo, {"user_id": USER_ID, "channel": "email"})


@pytest.mark.req("REQ-NTF-E01")
def test_create_invalid_channel(repo):
    with pytest.raises(svc.ValidationError):
        svc.create_notification(repo, {**_valid(), "channel": "carrier-pigeon"})


@pytest.mark.req("REQ-NTF-B01")
@rsps.activate
def test_create_user_not_found(repo):
    _mock_user(user=None)
    with pytest.raises(svc.ReferenceNotFoundError):
        svc.create_notification(repo, _valid())


@pytest.mark.req("REQ-NTF-B04")
@rsps.activate
def test_create_dependency_unavailable(repo):
    rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/{USER_ID}", json={}, status=503)
    with pytest.raises(svc.DependencyError):
        svc.create_notification(repo, _valid())


@pytest.mark.req("REQ-NTF-B02")
@rsps.activate
def test_patch_queued_to_sent_sets_sent_at(repo):
    _mock_user()
    n = svc.create_notification(repo, _valid())
    patched = svc.patch_notification(repo, n["id"], {"status": "sent"})
    assert patched["status"] == "sent"
    assert patched["sent_at"] is not None


@pytest.mark.req("REQ-NTF-B02")
@rsps.activate
def test_patch_sent_to_queued_forbidden(repo):
    _mock_user()
    n = svc.create_notification(repo, _valid())
    svc.patch_notification(repo, n["id"], {"status": "sent"})
    with pytest.raises(svc.InvalidStatusTransitionError):
        svc.patch_notification(repo, n["id"], {"status": "queued"})


@pytest.mark.req("REQ-NTF-B02")
@rsps.activate
def test_patch_queued_to_failed(repo):
    _mock_user()
    n = svc.create_notification(repo, _valid())
    patched = svc.patch_notification(repo, n["id"], {"status": "failed"})
    assert patched["status"] == "failed"


@pytest.mark.req("REQ-NTF-E03")
def test_get_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.get_notification(repo, "nope")


@pytest.mark.req("REQ-NTF-E05")
@rsps.activate
def test_delete(repo):
    _mock_user()
    n = svc.create_notification(repo, _valid())
    svc.delete_notification(repo, n["id"])
    with pytest.raises(svc.NotFoundError):
        svc.get_notification(repo, n["id"])


@pytest.mark.req("REQ-NTF-B03")
@rsps.activate
def test_broadcast_only_confirmed(repo):
    rsps.add(rsps.GET, f"{REGISTRATION_SERVICE_URL}/api/v1/registrations",
             json={"items": [{"user_id": "u1"}, {"user_id": "u2"}, {"user_id": "u3"}],
                   "page": 1, "page_size": 100, "total": 3}, status=200)
    result = svc.broadcast(repo, {"event_id": EVENT_ID, "channel": "email",
                                  "subject": "Thanks", "body": "See you"})
    assert result == {"event_id": EVENT_ID, "created": 3}
    items, total = repo.list({}, 1, 100)
    assert total == 3


@pytest.mark.req("REQ-NTF-B04")
@rsps.activate
def test_broadcast_dependency_unavailable(repo):
    rsps.add(rsps.GET, f"{REGISTRATION_SERVICE_URL}/api/v1/registrations", json={}, status=503)
    with pytest.raises(svc.DependencyError):
        svc.broadcast(repo, {"event_id": EVENT_ID, "channel": "email", "subject": "s", "body": "b"})

"""Unit tests for service.py — all business rules with mocked clients."""
import pytest
import responses as rsps
from app.storage.memory import MemoryRepository
from app import service as svc
from app.config import USER_SERVICE_URL, EVENT_SERVICE_URL

USER_ID = "11111111-0000-0000-0000-000000000001"
EVENT_ID = "22222222-0000-0000-0000-000000000001"

USER = {"id": USER_ID, "first_name": "A", "last_name": "B", "email": "a@b.com",
        "role": "attendee", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}

EVENT = {"id": EVENT_ID, "title": "Conf", "organizer_id": "org", "venue": "v", "city": "Roma",
         "start_date": "2026-10-01", "end_date": "2026-10-02", "capacity": 2, "price": 49.0,
         "status": "published", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}

@pytest.fixture
def repo():
    return MemoryRepository()

def _mock_user(user=USER, uid=USER_ID):
    rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/{uid}",
             json=user if user else {}, status=200 if user else 404)

def _mock_event(event=EVENT, eid=EVENT_ID):
    rsps.add(rsps.GET, f"{EVENT_SERVICE_URL}/api/v1/events/{eid}",
             json=event if event else {}, status=200 if event else 404)

# --- create_registration ---

@pytest.mark.req("REQ-REG-E01")
@rsps.activate
def test_create_valid(repo):
    _mock_user(); _mock_event()
    reg = svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    assert reg["status"] == "confirmed"
    assert reg["amount"] == 49.0
    assert reg["id"]

@pytest.mark.req("REQ-REG-E01")
def test_create_missing_field(repo):
    with pytest.raises(svc.ValidationError):
        svc.create_registration(repo, {"user_id": USER_ID})

@pytest.mark.req("REQ-REG-B01")
@rsps.activate
def test_create_user_not_found(repo):
    _mock_user(user=None)
    with pytest.raises(svc.ReferenceNotFoundError):
        svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})

@pytest.mark.req("REQ-REG-B02")
@rsps.activate
def test_create_event_not_found(repo):
    _mock_user(); _mock_event(event=None)
    with pytest.raises(svc.ReferenceNotFoundError):
        svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})

@pytest.mark.req("REQ-REG-B03")
@rsps.activate
def test_create_event_not_published(repo):
    _mock_user()
    _mock_event(event={**EVENT, "status": "draft"})
    with pytest.raises(svc.EventNotOpenError):
        svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})

@pytest.mark.req("REQ-REG-B04")
@rsps.activate
def test_create_duplicate(repo):
    for _ in range(2):
        _mock_user(); _mock_event()
    svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    with pytest.raises(svc.ConflictError) as e:
        svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    assert e.value.code == "ALREADY_REGISTERED"

@pytest.mark.req("REQ-REG-B05")
@rsps.activate
def test_create_event_full(repo):
    for i in range(2):
        rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/user{i}",
                 json={**USER, "id": f"user{i}"}, status=200)
        _mock_event()
        svc.create_registration(repo, {"user_id": f"user{i}", "event_id": EVENT_ID})
    rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/user2",
             json={**USER, "id": "user2"}, status=200)
    _mock_event()
    with pytest.raises(svc.ConflictError) as e:
        svc.create_registration(repo, {"user_id": "user2", "event_id": EVENT_ID})
    assert e.value.code == "EVENT_FULL"

@pytest.mark.req("REQ-REG-B09")
@rsps.activate
def test_create_dependency_unavailable(repo):
    rsps.add(rsps.GET, f"{USER_SERVICE_URL}/api/v1/users/{USER_ID}", json={}, status=503)
    with pytest.raises(svc.DependencyError):
        svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})

# --- patch (status transition) ---

@pytest.mark.req("REQ-REG-B07")
@rsps.activate
def test_patch_confirmed_to_cancelled(repo):
    _mock_user(); _mock_event()
    reg = svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    patched = svc.patch_registration(repo, reg["id"], {"status": "cancelled"})
    assert patched["status"] == "cancelled"

@pytest.mark.req("REQ-REG-B07")
@rsps.activate
def test_patch_cancelled_to_confirmed_forbidden(repo):
    _mock_user(); _mock_event()
    reg = svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    svc.patch_registration(repo, reg["id"], {"status": "cancelled"})
    with pytest.raises(svc.InvalidStatusTransitionError):
        svc.patch_registration(repo, reg["id"], {"status": "confirmed"})

@pytest.mark.req("REQ-REG-B05")
@rsps.activate
def test_cancel_frees_seat(repo):
    _mock_user(); _mock_event()
    reg = svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    assert repo.count_confirmed(EVENT_ID) == 1
    svc.patch_registration(repo, reg["id"], {"status": "cancelled"})
    assert repo.count_confirmed(EVENT_ID) == 0

# --- get / delete ---

@pytest.mark.req("REQ-REG-E03")
def test_get_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.get_registration(repo, "nope")

@pytest.mark.req("REQ-REG-E05")
@rsps.activate
def test_delete(repo):
    _mock_user(); _mock_event()
    reg = svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    svc.delete_registration(repo, reg["id"])
    with pytest.raises(svc.NotFoundError):
        svc.get_registration(repo, reg["id"])

@pytest.mark.req("REQ-REG-E05")
def test_delete_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.delete_registration(repo, "nope")

# --- stats ---

@pytest.mark.req("REQ-REG-B08")
@rsps.activate
def test_stats(repo):
    _mock_user(); _mock_event()
    svc.create_registration(repo, {"user_id": USER_ID, "event_id": EVENT_ID})
    _mock_event()
    stats = svc.get_stats(repo, EVENT_ID)
    assert stats == {"event_id": EVENT_ID, "capacity": 2, "confirmed": 1, "available": 1}

@pytest.mark.req("REQ-REG-B08")
@rsps.activate
def test_stats_event_not_found(repo):
    _mock_event(event=None)
    with pytest.raises(svc.NotFoundError):
        svc.get_stats(repo, EVENT_ID)

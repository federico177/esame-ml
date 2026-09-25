"""Unit tests for feedback service.py with mocked clients."""
import pytest
import responses as rsps
from app.storage.memory import MemoryRepository
from app import service as svc
from app.config import REGISTRATION_SERVICE_URL, EVENT_SERVICE_URL

USER_ID = "u-1"
EVENT_ID = "e-1"

EVENT = {"id": EVENT_ID, "title": "Conf", "organizer_id": "o", "venue": "v", "city": "Roma",
         "start_date": "2026-10-01", "end_date": "2026-10-02", "capacity": 5, "price": 10.0,
         "status": "published", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}


@pytest.fixture
def repo():
    return MemoryRepository()


def _mock_registered(total=1):
    rsps.add(rsps.GET, f"{REGISTRATION_SERVICE_URL}/api/v1/registrations",
             json={"items": [], "page": 1, "page_size": 20, "total": total}, status=200)


def _mock_event(event=EVENT):
    rsps.add(rsps.GET, f"{EVENT_SERVICE_URL}/api/v1/events/{EVENT_ID}",
             json=event if event else {}, status=200 if event else 404)


@pytest.mark.req("REQ-FBK-E01")
@rsps.activate
def test_create_valid(repo):
    _mock_registered()
    fb = svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 5, "comment": "great"})
    assert fb["rating"] == 5
    assert fb["id"]


@pytest.mark.req("REQ-FBK-E01")
def test_create_missing_field(repo):
    with pytest.raises(svc.ValidationError):
        svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID})


@pytest.mark.req("REQ-FBK-E01")
def test_create_rating_out_of_range(repo):
    with pytest.raises(svc.ValidationError):
        svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 6})


@pytest.mark.req("REQ-FBK-B01")
@rsps.activate
def test_create_not_registered(repo):
    _mock_registered(total=0)
    with pytest.raises(svc.NotRegisteredError):
        svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 4})


@pytest.mark.req("REQ-FBK-B02")
@rsps.activate
def test_create_duplicate(repo):
    _mock_registered(); _mock_registered()
    svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 4})
    with pytest.raises(svc.ConflictError) as e:
        svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 3})
    assert e.value.code == "FEEDBACK_ALREADY_EXISTS"


@pytest.mark.req("REQ-FBK-B04")
@rsps.activate
def test_create_dependency_unavailable(repo):
    rsps.add(rsps.GET, f"{REGISTRATION_SERVICE_URL}/api/v1/registrations", json={}, status=503)
    with pytest.raises(svc.DependencyError):
        svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 4})


@pytest.mark.req("REQ-FBK-E04")
@rsps.activate
def test_patch(repo):
    _mock_registered()
    fb = svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 3})
    patched = svc.patch_feedback(repo, fb["id"], {"rating": 5})
    assert patched["rating"] == 5


@pytest.mark.req("REQ-FBK-E03")
def test_get_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.get_feedback(repo, "nope")


@pytest.mark.req("REQ-FBK-E05")
@rsps.activate
def test_delete(repo):
    _mock_registered()
    fb = svc.create_feedback(repo, {"user_id": USER_ID, "event_id": EVENT_ID, "rating": 3})
    svc.delete_feedback(repo, fb["id"])
    with pytest.raises(svc.NotFoundError):
        svc.get_feedback(repo, fb["id"])


@pytest.mark.req("REQ-FBK-B03")
@rsps.activate
def test_summary(repo):
    for u, r in [("ua", 4), ("ub", 5)]:
        rsps.add(rsps.GET, f"{REGISTRATION_SERVICE_URL}/api/v1/registrations",
                 json={"items": [], "page": 1, "page_size": 20, "total": 1}, status=200)
        svc.create_feedback(repo, {"user_id": u, "event_id": EVENT_ID, "rating": r})
    _mock_event()
    summary = svc.get_summary(repo, EVENT_ID)
    assert summary["count"] == 2
    assert summary["average_rating"] == 4.5


@pytest.mark.req("REQ-FBK-B03")
@rsps.activate
def test_summary_empty(repo):
    _mock_event()
    summary = svc.get_summary(repo, EVENT_ID)
    assert summary["count"] == 0
    assert summary["average_rating"] is None


@pytest.mark.req("REQ-FBK-B03")
@rsps.activate
def test_summary_event_not_found(repo):
    _mock_event(event=None)
    with pytest.raises(svc.NotFoundError):
        svc.get_summary(repo, EVENT_ID)

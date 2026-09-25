"""
Unit tests for service.py — all business rules with mocked clients.
"""
import pytest
import responses as rsps_lib
from app.storage.memory import MemoryRepository
from app import service as svc
from app.config import USER_SERVICE_URL

BASE_URL = USER_SERVICE_URL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ORGANIZER = {
    "id": "aaaaaaaa-0000-0000-0000-000000000001",
    "first_name": "Org",
    "last_name": "One",
    "email": "org@test.com",
    "role": "organizer",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

ATTENDEE = {**ORGANIZER, "id": "aaaaaaaa-0000-0000-0000-000000000002",
            "email": "att@test.com", "role": "attendee"}

VALID_DATA = {
    "title": "CloudConf 2026",
    "organizer_id": ORGANIZER["id"],
    "venue": "Auditorium Roma",
    "city": "Roma",
    "start_date": "2026-10-01",
    "end_date": "2026-10-02",
    "capacity": 100,
    "price": 49.00,
}


@pytest.fixture
def repo():
    return MemoryRepository()


def _mock_user_ok(user=None):
    """Register a successful user-service response."""
    u = user or ORGANIZER
    rsps_lib.add(rsps_lib.GET,
                 f"{BASE_URL}/api/v1/users/{u['id']}",
                 json=u, status=200)


def _mock_user_404(user_id):
    rsps_lib.add(rsps_lib.GET,
                 f"{BASE_URL}/api/v1/users/{user_id}",
                 json={"error": {"code": "NOT_FOUND", "message": "not found"}}, status=404)


def _mock_user_503(user_id):
    rsps_lib.add(rsps_lib.GET,
                 f"{BASE_URL}/api/v1/users/{user_id}",
                 json={}, status=503)


# ---------------------------------------------------------------------------
# create_event
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-EVT-E01")
@rsps_lib.activate
def test_create_event_valid(repo):
    _mock_user_ok()
    event = svc.create_event(repo, VALID_DATA)
    assert event["id"]
    assert event["status"] == "draft"
    assert event["price"] == 49.0
    assert event["created_at"] == event["updated_at"]


@pytest.mark.req("REQ-EVT-E01")
@rsps_lib.activate
def test_create_event_missing_field(repo):
    _mock_user_ok()
    bad = {k: v for k, v in VALID_DATA.items() if k != "title"}
    with pytest.raises(svc.ValidationError):
        svc.create_event(repo, bad)


@pytest.mark.req("REQ-EVT-B01")
@rsps_lib.activate
def test_create_event_organizer_not_found(repo):
    _mock_user_404(ORGANIZER["id"])
    with pytest.raises(svc.ReferenceNotFoundError):
        svc.create_event(repo, VALID_DATA)


@pytest.mark.req("REQ-EVT-B02")
@rsps_lib.activate
def test_create_event_organizer_wrong_role(repo):
    _mock_user_ok(ATTENDEE)
    data = {**VALID_DATA, "organizer_id": ATTENDEE["id"]}
    with pytest.raises(svc.InvalidOrganizerError):
        svc.create_event(repo, data)


@pytest.mark.req("REQ-EVT-B03")
@rsps_lib.activate
def test_create_event_end_before_start(repo):
    _mock_user_ok()
    data = {**VALID_DATA, "start_date": "2026-10-05", "end_date": "2026-10-01"}
    with pytest.raises(svc.ValidationError):
        svc.create_event(repo, data)


@pytest.mark.req("REQ-EVT-B03")
@rsps_lib.activate
def test_create_event_same_start_end(repo):
    """Single-day event is valid."""
    _mock_user_ok()
    data = {**VALID_DATA, "start_date": "2026-10-01", "end_date": "2026-10-01"}
    event = svc.create_event(repo, data)
    assert event["id"]


@pytest.mark.req("REQ-EVT-B05")
@rsps_lib.activate
def test_create_event_dependency_unavailable(repo):
    _mock_user_503(ORGANIZER["id"])
    with pytest.raises(svc.DependencyError):
        svc.create_event(repo, VALID_DATA)


# ---------------------------------------------------------------------------
# list_events
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_with_events(repo):
    for city, status in [("Roma", "draft"), ("Milano", "published"), ("Roma", "cancelled")]:
        repo.create({
            "id": f"evt-{city}-{status}",
            "title": f"Event {city}",
            "description": None,
            "organizer_id": ORGANIZER["id"],
            "venue": "v", "city": city,
            "start_date": "2026-10-01", "end_date": "2026-10-02",
            "capacity": 100, "price": 10.0,
            "status": status,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
    return repo


@pytest.mark.req("REQ-EVT-B06")
def test_list_filter_status(repo_with_events):
    items, total = svc.list_events(repo_with_events, 1, 20, status="draft")
    assert total == 1
    assert items[0]["status"] == "draft"


@pytest.mark.req("REQ-EVT-B06")
def test_list_filter_city(repo_with_events):
    items, total = svc.list_events(repo_with_events, 1, 20, city="roma")
    assert total == 2


@pytest.mark.req("REQ-EVT-E02")
def test_list_pagination(repo_with_events):
    items, total = svc.list_events(repo_with_events, 1, 2)
    assert total == 3
    assert len(items) == 2


@pytest.mark.req("REQ-EVT-E02")
def test_list_invalid_page_size(repo):
    with pytest.raises(svc.ValidationError):
        svc.list_events(repo, 1, 200)


# ---------------------------------------------------------------------------
# get_event
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-EVT-E03")
@rsps_lib.activate
def test_get_event_found(repo):
    _mock_user_ok()
    created = svc.create_event(repo, VALID_DATA)
    found = svc.get_event(repo, created["id"])
    assert found["id"] == created["id"]


@pytest.mark.req("REQ-EVT-E03")
def test_get_event_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.get_event(repo, "nonexistent")


# ---------------------------------------------------------------------------
# Status transitions (REQ-EVT-B04)
# ---------------------------------------------------------------------------

@pytest.fixture
def draft_event(repo):
    repo.create({
        "id": "evt-draft",
        "title": "Draft Event",
        "description": None,
        "organizer_id": ORGANIZER["id"],
        "venue": "v", "city": "Roma",
        "start_date": "2026-10-01", "end_date": "2026-10-02",
        "capacity": 100, "price": 10.0,
        "status": "draft",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    })
    return repo


@pytest.mark.req("REQ-EVT-B04")
@rsps_lib.activate
def test_patch_draft_to_published(draft_event):
    _mock_user_ok()
    event = svc.patch_event(draft_event, "evt-draft", {"status": "published"})
    assert event["status"] == "published"


@pytest.mark.req("REQ-EVT-B04")
@rsps_lib.activate
def test_patch_published_to_draft_forbidden(draft_event):
    _mock_user_ok()
    svc.patch_event(draft_event, "evt-draft", {"status": "published"})
    with pytest.raises(svc.InvalidStatusTransitionError):
        svc.patch_event(draft_event, "evt-draft", {"status": "draft"})


@pytest.mark.req("REQ-EVT-B04")
@rsps_lib.activate
def test_patch_published_to_cancelled(draft_event):
    _mock_user_ok()
    rsps_lib.add(rsps_lib.GET,
                 f"{BASE_URL}/api/v1/users/{ORGANIZER['id']}",
                 json=ORGANIZER, status=200)
    svc.patch_event(draft_event, "evt-draft", {"status": "published"})
    event = svc.patch_event(draft_event, "evt-draft", {"status": "cancelled"})
    assert event["status"] == "cancelled"


# ---------------------------------------------------------------------------
# delete_event
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-EVT-E06")
@rsps_lib.activate
def test_delete_event(repo):
    _mock_user_ok()
    created = svc.create_event(repo, VALID_DATA)
    svc.delete_event(repo, created["id"])
    with pytest.raises(svc.NotFoundError):
        svc.get_event(repo, created["id"])


@pytest.mark.req("REQ-EVT-E06")
def test_delete_event_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.delete_event(repo, "nonexistent")

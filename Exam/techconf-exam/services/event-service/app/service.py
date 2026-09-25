"""
Business logic for event-service.
All REQ-EVT-B* rules live here.
"""
import uuid
from datetime import datetime, timezone
from .repository import EventRepository
from . import clients

# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class NotFoundError(Exception):
    pass

class ReferenceNotFoundError(Exception):
    pass

class InvalidOrganizerError(Exception):
    pass

class InvalidStatusTransitionError(Exception):
    pass

class DependencyError(Exception):
    pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_STATUSES = {"draft", "published", "cancelled"}
ALLOWED_TRANSITIONS = {
    ("draft", "published"),
    ("draft", "cancelled"),
    ("published", "cancelled"),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_fields(data: dict, require_all: bool = True) -> dict:
    errors = {}

    title = data.get("title")
    description = data.get("description")
    organizer_id = data.get("organizer_id")
    venue = data.get("venue")
    city = data.get("city")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    capacity = data.get("capacity")
    price = data.get("price")
    status = data.get("status")

    if require_all:
        for field in ["title", "organizer_id", "venue", "city", "start_date", "end_date", "capacity", "price"]:
            if data.get(field) is None:
                errors[field] = "required"

    if title is not None:
        if not isinstance(title, str) or not (3 <= len(title) <= 120):
            errors["title"] = "must be 3-120 characters"

    if description is not None and description != "":
        if not isinstance(description, str) or len(description) > 2000:
            errors["description"] = "must be max 2000 characters"

    if venue is not None:
        if not isinstance(venue, str) or len(venue) > 100:
            errors["venue"] = "must be max 100 characters"

    if city is not None:
        if not isinstance(city, str) or len(city) > 60:
            errors["city"] = "must be max 60 characters"

    if capacity is not None:
        if not isinstance(capacity, int) or not (1 <= capacity <= 10000):
            errors["capacity"] = "must be integer 1-10000"

    if price is not None:
        if not isinstance(price, (int, float)) or price < 0:
            errors["price"] = "must be >= 0"

    if status is not None and status not in VALID_STATUSES:
        errors["status"] = f"must be one of {sorted(VALID_STATUSES)}"

    # Date format validation
    if start_date is not None:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            errors["start_date"] = "must be YYYY-MM-DD"

    if end_date is not None:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            errors["end_date"] = "must be YYYY-MM-DD"

    if errors:
        raise ValidationError("Validation failed", details=errors)

    # REQ-EVT-B03: end_date >= start_date
    sd = data.get("start_date")
    ed = data.get("end_date")
    if sd and ed and "start_date" not in errors and "end_date" not in errors:
        if ed < sd:
            raise ValidationError("end_date must be >= start_date",
                                   details={"end_date": "must be >= start_date"})

    cleaned = {k: v for k, v in data.items()
               if k in {"title", "description", "organizer_id", "venue", "city",
                        "start_date", "end_date", "capacity", "price", "status"}}
    return cleaned


def _validate_organizer(organizer_id: str):
    """REQ-EVT-B01, REQ-EVT-B02"""
    try:
        user = clients.get_user(organizer_id)
    except clients.DependencyError as exc:
        raise DependencyError(str(exc)) from exc

    if user is None:
        raise ReferenceNotFoundError(f"organizer_id {organizer_id} not found")

    if user.get("role") != "organizer":
        raise InvalidOrganizerError(f"User {organizer_id} has role '{user.get('role')}', expected 'organizer'")


def _check_status_transition(current: str, new: str):
    """REQ-EVT-B04"""
    if current == new:
        return
    if (current, new) not in ALLOWED_TRANSITIONS:
        raise InvalidStatusTransitionError(
            f"Transition {current}→{new} is not allowed"
        )

# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def create_event(repo: EventRepository, data: dict) -> dict:
    """REQ-EVT-E01, REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B03"""
    cleaned = _validate_fields(data, require_all=True)
    _validate_organizer(cleaned["organizer_id"])

    now = _now_iso()
    event = {
        "id": str(uuid.uuid4()),
        "title": cleaned["title"],
        "description": cleaned.get("description"),
        "organizer_id": cleaned["organizer_id"],
        "venue": cleaned["venue"],
        "city": cleaned["city"],
        "start_date": cleaned["start_date"],
        "end_date": cleaned["end_date"],
        "capacity": cleaned["capacity"],
        "price": round(float(cleaned["price"]), 2),
        "status": cleaned.get("status", "draft"),
        "created_at": now,
        "updated_at": now,
    }
    return repo.create(event)


def list_events(repo: EventRepository, page: int, page_size: int,
                status: str = None, city: str = None) -> tuple[list, int]:
    """REQ-EVT-E02, REQ-EVT-B06"""
    if page < 1 or page_size < 1 or page_size > 100:
        raise ValidationError("Invalid pagination parameters")
    if status and status not in VALID_STATUSES:
        raise ValidationError("Invalid status filter",
                               details={"status": f"must be one of {sorted(VALID_STATUSES)}"})
    filters = {}
    if status:
        filters["status"] = status
    if city:
        filters["city"] = city
    return repo.list(filters, page, page_size)


def get_event(repo: EventRepository, event_id: str) -> dict:
    """REQ-EVT-E03"""
    event = repo.get(event_id)
    if event is None:
        raise NotFoundError(f"Event {event_id} not found")
    return event


def replace_event(repo: EventRepository, event_id: str, data: dict) -> dict:
    """REQ-EVT-E04, REQ-EVT-B01..B04"""
    existing = repo.get(event_id)
    if existing is None:
        raise NotFoundError(f"Event {event_id} not found")

    cleaned = _validate_fields(data, require_all=True)

    if "organizer_id" in cleaned:
        _validate_organizer(cleaned["organizer_id"])

    if "status" in cleaned:
        _check_status_transition(existing["status"], cleaned["status"])

    updated = {**existing, **cleaned, "updated_at": _now_iso()}
    if "price" in updated:
        updated["price"] = round(float(updated["price"]), 2)
    return repo.update(event_id, updated)


def patch_event(repo: EventRepository, event_id: str, data: dict) -> dict:
    """REQ-EVT-E05, REQ-EVT-B01..B04"""
    existing = repo.get(event_id)
    if existing is None:
        raise NotFoundError(f"Event {event_id} not found")

    cleaned = _validate_fields(data, require_all=False)

    if "organizer_id" in cleaned:
        _validate_organizer(cleaned["organizer_id"])

    if "status" in cleaned:
        _check_status_transition(existing["status"], cleaned["status"])

    cleaned["updated_at"] = _now_iso()
    if "price" in cleaned:
        cleaned["price"] = round(float(cleaned["price"]), 2)
    return repo.update(event_id, cleaned)


def delete_event(repo: EventRepository, event_id: str) -> None:
    """REQ-EVT-E06"""
    if not repo.delete(event_id):
        raise NotFoundError(f"Event {event_id} not found")

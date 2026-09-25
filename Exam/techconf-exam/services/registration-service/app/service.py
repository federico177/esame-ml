"""Business logic for registration-service. All REQ-REG-B* rules live here."""
import uuid
from datetime import datetime, timezone
from .repository import RegistrationRepository
from . import clients

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class NotFoundError(Exception):
    pass

class ConflictError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

class DependencyError(Exception):
    pass

class ReferenceNotFoundError(Exception):
    pass

class EventNotOpenError(Exception):
    pass

class InvalidStatusTransitionError(Exception):
    pass

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def create_registration(repo: RegistrationRepository, data: dict) -> dict:
    """REQ-REG-B01..B06"""
    user_id = data.get("user_id")
    event_id = data.get("event_id")

    if not user_id or not event_id:
        raise ValidationError("user_id and event_id are required",
                               details={f: "required" for f in ["user_id", "event_id"] if not data.get(f)})

    # REQ-REG-B01 — user must exist
    try:
        user = clients.get_user(user_id)
    except clients.DependencyError as e:
        raise DependencyError(str(e)) from e
    if user is None:
        raise ReferenceNotFoundError(f"user_id {user_id} not found")

    # REQ-REG-B02 — event must exist
    try:
        event = clients.get_event(event_id)
    except clients.DependencyError as e:
        raise DependencyError(str(e)) from e
    if event is None:
        raise ReferenceNotFoundError(f"event_id {event_id} not found")

    # REQ-REG-B03 — event must be published
    if event.get("status") != "published":
        raise EventNotOpenError(f"Event {event_id} is not published (status={event.get('status')})")

    # REQ-REG-B04 — no duplicate confirmed registration
    if repo.find_confirmed(user_id, event_id):
        raise ConflictError("ALREADY_REGISTERED", f"User {user_id} is already registered for event {event_id}")

    # REQ-REG-B05 — capacity check
    confirmed = repo.count_confirmed(event_id)
    if confirmed >= event["capacity"]:
        raise ConflictError("EVENT_FULL", f"Event {event_id} is full ({confirmed}/{event['capacity']})")

    # REQ-REG-B06 — amount from event.price
    now = _now()
    reg = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "event_id": event_id,
        "amount": round(float(event["price"]), 2),
        "status": "confirmed",
        "created_at": now,
        "updated_at": now,
    }
    return repo.create(reg)


def list_registrations(repo: RegistrationRepository, page: int, page_size: int,
                       user_id: str = None, event_id: str = None, status: str = None) -> tuple[list, int]:
    if page < 1 or page_size < 1 or page_size > 100:
        raise ValidationError("Invalid pagination parameters")
    if status and status not in ("confirmed", "cancelled"):
        raise ValidationError("Invalid status filter")
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if event_id:
        filters["event_id"] = event_id
    if status:
        filters["status"] = status
    return repo.list(filters, page, page_size)


def get_registration(repo: RegistrationRepository, reg_id: str) -> dict:
    reg = repo.get(reg_id)
    if reg is None:
        raise NotFoundError(f"Registration {reg_id} not found")
    return reg


def patch_registration(repo: RegistrationRepository, reg_id: str, data: dict) -> dict:
    """REQ-REG-B07 — only confirmed→cancelled allowed"""
    reg = repo.get(reg_id)
    if reg is None:
        raise NotFoundError(f"Registration {reg_id} not found")

    new_status = data.get("status")
    if not new_status:
        raise ValidationError("status is required", details={"status": "required"})

    if new_status not in ("confirmed", "cancelled"):
        raise ValidationError("Invalid status value")

    current = reg["status"]
    if current == new_status:
        return reg  # idempotent same-value patch
    if (current, new_status) != ("confirmed", "cancelled"):
        raise InvalidStatusTransitionError(f"Transition {current}→{new_status} is not allowed")

    return repo.update(reg_id, {"status": "cancelled", "updated_at": _now()})


def delete_registration(repo: RegistrationRepository, reg_id: str) -> None:
    if not repo.delete(reg_id):
        raise NotFoundError(f"Registration {reg_id} not found")


def get_stats(repo: RegistrationRepository, event_id: str) -> dict:
    """REQ-REG-B08"""
    try:
        event = clients.get_event(event_id)
    except clients.DependencyError as e:
        raise DependencyError(str(e)) from e
    if event is None:
        raise NotFoundError(f"Event {event_id} not found")

    confirmed = repo.count_confirmed(event_id)
    capacity = event["capacity"]
    return {
        "event_id": event_id,
        "capacity": capacity,
        "confirmed": confirmed,
        "available": max(0, capacity - confirmed),
    }

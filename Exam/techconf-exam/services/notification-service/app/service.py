"""Business logic for notification-service. All REQ-NTF-B* rules live here."""
import uuid
from datetime import datetime, timezone
from .repository import NotificationRepository
from . import clients


class ValidationError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message); self.message = message; self.details = details or {}

class NotFoundError(Exception):
    pass

class DependencyError(Exception):
    pass

class ReferenceNotFoundError(Exception):
    pass

class InvalidStatusTransitionError(Exception):
    pass


VALID_CHANNELS = {"email", "sms", "push"}
VALID_STATUSES = {"queued", "sent", "failed"}
ALLOWED_TRANSITIONS = {("queued", "sent"), ("queued", "failed")}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate(data):
    errors = {}
    for f in ["user_id", "channel", "subject", "body"]:
        if not data.get(f):
            errors[f] = "required"
    ch = data.get("channel")
    if ch is not None and ch not in VALID_CHANNELS:
        errors["channel"] = f"must be one of {sorted(VALID_CHANNELS)}"
    subj = data.get("subject")
    if subj is not None and (not isinstance(subj, str) or not (1 <= len(subj) <= 150)):
        errors["subject"] = "1-150 chars"
    body = data.get("body")
    if body is not None and (not isinstance(body, str) or not (1 <= len(body) <= 5000)):
        errors["body"] = "1-5000 chars"
    if errors:
        raise ValidationError("Validation failed", details=errors)


def _new_notification(user_id, channel, subject, body):
    now = _now()
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "channel": channel,
        "subject": subject,
        "body": body,
        "status": "queued",
        "sent_at": None,
        "created_at": now,
        "updated_at": now,
    }


def create_notification(repo, data):
    """REQ-NTF-E01, B01"""
    _validate(data)
    try:
        user = clients.get_user(data["user_id"])
    except clients.DependencyError as e:
        raise DependencyError(str(e)) from e
    if user is None:
        raise ReferenceNotFoundError(f"user_id {data['user_id']} not found")
    n = _new_notification(data["user_id"], data["channel"], data["subject"], data["body"])
    return repo.create(n)


def list_notifications(repo, page, page_size, user_id=None, status=None):
    if page < 1 or page_size < 1 or page_size > 100:
        raise ValidationError("Invalid pagination parameters")
    if status and status not in VALID_STATUSES:
        raise ValidationError("Invalid status filter")
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if status:
        filters["status"] = status
    return repo.list(filters, page, page_size)


def get_notification(repo, n_id):
    n = repo.get(n_id)
    if n is None:
        raise NotFoundError(f"Notification {n_id} not found")
    return n


def patch_notification(repo, n_id, data):
    """REQ-NTF-B02"""
    n = repo.get(n_id)
    if n is None:
        raise NotFoundError(f"Notification {n_id} not found")
    new_status = data.get("status")
    if not new_status:
        raise ValidationError("status is required", details={"status": "required"})
    if new_status not in VALID_STATUSES:
        raise ValidationError("Invalid status value")
    current = n["status"]
    if current == new_status:
        return n
    if (current, new_status) not in ALLOWED_TRANSITIONS:
        raise InvalidStatusTransitionError(f"Transition {current}->{new_status} is not allowed")
    updates = {"status": new_status, "updated_at": _now()}
    if new_status == "sent":
        updates["sent_at"] = _now()
    return repo.update(n_id, updates)


def delete_notification(repo, n_id):
    if not repo.delete(n_id):
        raise NotFoundError(f"Notification {n_id} not found")


def broadcast(repo, data):
    """REQ-NTF-B03"""
    for f in ["event_id", "channel", "subject", "body"]:
        if not data.get(f):
            raise ValidationError("Missing required field", details={f: "required"})
    if data["channel"] not in VALID_CHANNELS:
        raise ValidationError("Invalid channel", details={"channel": "invalid"})
    try:
        regs = clients.list_confirmed_registrations(data["event_id"])
    except clients.DependencyError as e:
        raise DependencyError(str(e)) from e
    created = 0
    for reg in regs:
        n = _new_notification(reg["user_id"], data["channel"], data["subject"], data["body"])
        repo.create(n)
        created += 1
    return {"event_id": data["event_id"], "created": created}

"""Business logic for feedback-service. All REQ-FBK-B* rules live here."""
import uuid
from datetime import datetime, timezone
from .repository import FeedbackRepository
from . import clients


class ValidationError(Exception):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message); self.message = message; self.details = details or {}

class NotFoundError(Exception):
    pass

class ConflictError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message); self.code = code; self.message = message

class DependencyError(Exception):
    pass

class NotRegisteredError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_rating(rating):
    if not isinstance(rating, int) or isinstance(rating, bool) or not (1 <= rating <= 5):
        raise ValidationError("rating must be an integer 1-5", details={"rating": "1-5"})


def _validate_comment(comment):
    if comment is not None and comment != "":
        if not isinstance(comment, str) or len(comment) > 500:
            raise ValidationError("comment must be max 500 characters", details={"comment": "max 500"})


def create_feedback(repo: FeedbackRepository, data: dict) -> dict:
    """REQ-FBK-E01, B01, B02"""
    user_id = data.get("user_id")
    event_id = data.get("event_id")
    rating = data.get("rating")
    comment = data.get("comment")

    if not user_id or not event_id or rating is None:
        raise ValidationError("user_id, event_id and rating are required",
                               details={f: "required" for f in ["user_id", "event_id", "rating"]
                                        if data.get(f) is None})
    _validate_rating(rating)
    _validate_comment(comment)

    # REQ-FBK-B01 — confirmed registration must exist
    try:
        registered = clients.has_confirmed_registration(user_id, event_id)
    except clients.DependencyError as e:
        raise DependencyError(str(e)) from e
    if not registered:
        raise NotRegisteredError(f"User {user_id} has no confirmed registration for event {event_id}")

    # REQ-FBK-B02 — one feedback per (user, event)
    if repo.find_by_user_event(user_id, event_id):
        raise ConflictError("FEEDBACK_ALREADY_EXISTS", "Feedback already exists for this user and event")

    now = _now()
    fb = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "event_id": event_id,
        "rating": rating,
        "comment": comment if comment else None,
        "created_at": now,
        "updated_at": now,
    }
    return repo.create(fb)


def list_feedbacks(repo, page, page_size, event_id=None, user_id=None):
    if page < 1 or page_size < 1 or page_size > 100:
        raise ValidationError("Invalid pagination parameters")
    filters = {}
    if event_id:
        filters["event_id"] = event_id
    if user_id:
        filters["user_id"] = user_id
    return repo.list(filters, page, page_size)


def get_feedback(repo, fb_id):
    fb = repo.get(fb_id)
    if fb is None:
        raise NotFoundError(f"Feedback {fb_id} not found")
    return fb


def patch_feedback(repo, fb_id, data):
    fb = repo.get(fb_id)
    if fb is None:
        raise NotFoundError(f"Feedback {fb_id} not found")
    updates = {}
    if "rating" in data:
        _validate_rating(data["rating"]); updates["rating"] = data["rating"]
    if "comment" in data:
        _validate_comment(data["comment"]); updates["comment"] = data["comment"] if data["comment"] else None
    updates["updated_at"] = _now()
    return repo.update(fb_id, updates)


def delete_feedback(repo, fb_id):
    if not repo.delete(fb_id):
        raise NotFoundError(f"Feedback {fb_id} not found")


def get_summary(repo, event_id):
    """REQ-FBK-B03"""
    try:
        event = clients.get_event(event_id)
    except clients.DependencyError as e:
        raise DependencyError(str(e)) from e
    if event is None:
        raise NotFoundError(f"Event {event_id} not found")

    feedbacks = repo.list_by_event(event_id)
    count = len(feedbacks)
    if count == 0:
        average = None
    else:
        average = round(sum(f["rating"] for f in feedbacks) / count, 2)
    return {"event_id": event_id, "count": count, "average_rating": average}

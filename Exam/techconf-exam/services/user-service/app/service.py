"""
Business logic for user-service.
All REQ-USR-B* rules live here.
"""
import re
import uuid
from datetime import datetime, timezone

from .repository import UserRepository

# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConflictError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class NotFoundError(Exception):
    pass


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_ROLES = {"attendee", "speaker", "organizer"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_user_fields(data: dict, require_all: bool = True) -> dict:
    """
    Validate and normalise user input fields.
    If require_all=True, all required fields must be present (POST / PUT).
    Returns cleaned data dict. Raises ValidationError on failure.
    """
    errors = {}

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    company = data.get("company")
    role = data.get("role")

    if require_all:
        if not first_name:
            errors["first_name"] = "required"
        if not last_name:
            errors["last_name"] = "required"
        if not email:
            errors["email"] = "required"

    if first_name is not None:
        if not isinstance(first_name, str) or not (1 <= len(first_name.strip()) <= 50):
            errors["first_name"] = "must be 1-50 characters"

    if last_name is not None:
        if not isinstance(last_name, str) or not (1 <= len(last_name.strip()) <= 50):
            errors["last_name"] = "must be 1-50 characters"

    if email is not None:
        if not isinstance(email, str) or not EMAIL_RE.match(email):
            errors["email"] = "must be a valid email address"

    if company is not None and company != "" and company is not None:
        if not isinstance(company, str) or len(company) > 100:
            errors["company"] = "must be max 100 characters"

    if role is not None:
        if role not in VALID_ROLES:
            errors["role"] = f"must be one of {sorted(VALID_ROLES)}"

    if errors:
        raise ValidationError("Validation failed", details=errors)

    cleaned = {}
    if first_name is not None:
        cleaned["first_name"] = first_name.strip()
    if last_name is not None:
        cleaned["last_name"] = last_name.strip()
    if email is not None:
        cleaned["email"] = email.lower()           # REQ-USR-B02
    if "company" in data:
        cleaned["company"] = company if company else None
    if role is not None:
        cleaned["role"] = role

    return cleaned


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def create_user(repo: UserRepository, data: dict) -> dict:
    """REQ-USR-E01, REQ-USR-B01, REQ-USR-B02"""
    cleaned = _validate_user_fields(data, require_all=True)

    # REQ-USR-B01 — email uniqueness
    if repo.get_by_email(cleaned["email"]):
        raise ConflictError("EMAIL_ALREADY_EXISTS", "Email already registered")

    now = _now_iso()
    user = {
        "id": str(uuid.uuid4()),
        "first_name": cleaned["first_name"],
        "last_name": cleaned["last_name"],
        "email": cleaned["email"],
        "company": cleaned.get("company"),
        "role": cleaned.get("role", "attendee"),
        "created_at": now,
        "updated_at": now,
    }
    return repo.create(user)


def list_users(repo: UserRepository, page: int, page_size: int, role: str = None, email: str = None) -> tuple[list, int]:
    """REQ-USR-E02, REQ-USR-B03"""
    if page < 1 or page_size < 1 or page_size > 100:
        raise ValidationError("Invalid pagination parameters")
    filters = {}
    if role:
        if role not in VALID_ROLES:
            raise ValidationError("Invalid role filter", details={"role": f"must be one of {sorted(VALID_ROLES)}"})
        filters["role"] = role
    if email:
        filters["email"] = email
    return repo.list(filters, page, page_size)


def get_user(repo: UserRepository, user_id: str) -> dict:
    """REQ-USR-E03"""
    user = repo.get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    return user


def replace_user(repo: UserRepository, user_id: str, data: dict) -> dict:
    """REQ-USR-E04, REQ-USR-B01, REQ-USR-B02"""
    existing = repo.get(user_id)
    if existing is None:
        raise NotFoundError(f"User {user_id} not found")

    cleaned = _validate_user_fields(data, require_all=True)

    # REQ-USR-B01 — check email conflict with a *different* user
    conflict = repo.get_by_email(cleaned["email"])
    if conflict and conflict["id"] != user_id:
        raise ConflictError("EMAIL_ALREADY_EXISTS", "Email already registered")

    updated = {
        **existing,
        "first_name": cleaned["first_name"],
        "last_name": cleaned["last_name"],
        "email": cleaned["email"],
        "company": cleaned.get("company"),
        "role": cleaned.get("role", existing.get("role", "attendee")),
        "updated_at": _now_iso(),
    }
    return repo.update(user_id, updated)


def patch_user(repo: UserRepository, user_id: str, data: dict) -> dict:
    """REQ-USR-E05, REQ-USR-B01, REQ-USR-B02"""
    existing = repo.get(user_id)
    if existing is None:
        raise NotFoundError(f"User {user_id} not found")

    cleaned = _validate_user_fields(data, require_all=False)

    if "email" in cleaned:
        conflict = repo.get_by_email(cleaned["email"])
        if conflict and conflict["id"] != user_id:
            raise ConflictError("EMAIL_ALREADY_EXISTS", "Email already registered")

    cleaned["updated_at"] = _now_iso()
    return repo.update(user_id, cleaned)


def delete_user(repo: UserRepository, user_id: str) -> None:
    """REQ-USR-E06"""
    deleted = repo.delete(user_id)
    if not deleted:
        raise NotFoundError(f"User {user_id} not found")

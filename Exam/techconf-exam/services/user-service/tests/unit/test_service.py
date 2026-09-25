"""
Unit tests for service.py — all business rules tested with MemoryRepository.
"""
import pytest
from app.storage.memory import MemoryRepository
from app import service as svc


@pytest.fixture
def repo():
    return MemoryRepository()


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E01")
def test_create_user_valid(repo):
    user = svc.create_user(repo, {
        "first_name": "Alice",
        "last_name": "Rossi",
        "email": "Alice@Example.com",
    })
    assert user["id"]
    assert user["email"] == "alice@example.com"   # REQ-USR-B02: lowercase
    assert user["role"] == "attendee"              # default role
    assert user["created_at"] == user["updated_at"]


@pytest.mark.req("REQ-USR-E01")
def test_create_user_with_all_fields(repo):
    user = svc.create_user(repo, {
        "first_name": "Bob",
        "last_name": "Verdi",
        "email": "bob@example.com",
        "company": "Acme",
        "role": "organizer",
    })
    assert user["company"] == "Acme"
    assert user["role"] == "organizer"


@pytest.mark.req("REQ-USR-E01")
def test_create_user_missing_required_field(repo):
    with pytest.raises(svc.ValidationError):
        svc.create_user(repo, {"first_name": "Alice", "last_name": "Rossi"})  # no email


@pytest.mark.req("REQ-USR-E01")
def test_create_user_invalid_role(repo):
    with pytest.raises(svc.ValidationError):
        svc.create_user(repo, {
            "first_name": "Alice", "last_name": "Rossi",
            "email": "a@b.com", "role": "admin"
        })


@pytest.mark.req("REQ-USR-B01")
def test_create_user_duplicate_email_different_case(repo):
    svc.create_user(repo, {"first_name": "A", "last_name": "B", "email": "user@example.com"})
    with pytest.raises(svc.ConflictError) as exc:
        svc.create_user(repo, {"first_name": "C", "last_name": "D", "email": "USER@EXAMPLE.COM"})
    assert exc.value.code == "EMAIL_ALREADY_EXISTS"


@pytest.mark.req("REQ-USR-B02")
def test_create_user_email_stored_lowercase(repo):
    user = svc.create_user(repo, {"first_name": "A", "last_name": "B", "email": "UPPER@TEST.COM"})
    assert user["email"] == "upper@test.com"


# ---------------------------------------------------------------------------
# list_users
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_with_users(repo):
    svc.create_user(repo, {"first_name": "Alice", "last_name": "A", "email": "a@test.com", "role": "attendee"})
    svc.create_user(repo, {"first_name": "Bob", "last_name": "B", "email": "b@test.com", "role": "organizer"})
    svc.create_user(repo, {"first_name": "Carol", "last_name": "C", "email": "c@test.com", "role": "attendee"})
    return repo


@pytest.mark.req("REQ-USR-E02")
def test_list_users_pagination(repo_with_users):
    items, total = svc.list_users(repo_with_users, page=1, page_size=2)
    assert total == 3
    assert len(items) == 2


@pytest.mark.req("REQ-USR-B03")
def test_list_users_filter_role(repo_with_users):
    items, total = svc.list_users(repo_with_users, page=1, page_size=20, role="organizer")
    assert total == 1
    assert items[0]["role"] == "organizer"


@pytest.mark.req("REQ-USR-B03")
def test_list_users_filter_email(repo_with_users):
    items, total = svc.list_users(repo_with_users, page=1, page_size=20, email="A@TEST.COM")
    assert total == 1
    assert items[0]["email"] == "a@test.com"


@pytest.mark.req("REQ-USR-E02")
def test_list_users_invalid_page_size(repo):
    with pytest.raises(svc.ValidationError):
        svc.list_users(repo, page=1, page_size=200)


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E03")
def test_get_user_found(repo):
    created = svc.create_user(repo, {"first_name": "A", "last_name": "B", "email": "x@y.com"})
    fetched = svc.get_user(repo, created["id"])
    assert fetched["id"] == created["id"]


@pytest.mark.req("REQ-USR-E03")
def test_get_user_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.get_user(repo, "00000000-0000-0000-0000-000000000000")


# ---------------------------------------------------------------------------
# replace_user
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E04")
def test_replace_user(repo):
    import time
    created = svc.create_user(repo, {"first_name": "A", "last_name": "B", "email": "old@test.com"})
    time.sleep(0.01)
    updated = svc.replace_user(repo, created["id"], {
        "first_name": "New", "last_name": "Name", "email": "new@test.com"
    })
    assert updated["first_name"] == "New"
    assert updated["email"] == "new@test.com"
    assert updated["updated_at"] >= created["updated_at"]


@pytest.mark.req("REQ-USR-E04")
def test_replace_user_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.replace_user(repo, "00000000-0000-0000-0000-000000000000", {
            "first_name": "A", "last_name": "B", "email": "x@y.com"
        })


@pytest.mark.req("REQ-USR-B01")
def test_replace_user_email_conflict(repo):
    svc.create_user(repo, {"first_name": "A", "last_name": "B", "email": "taken@test.com"})
    u2 = svc.create_user(repo, {"first_name": "C", "last_name": "D", "email": "mine@test.com"})
    with pytest.raises(svc.ConflictError):
        svc.replace_user(repo, u2["id"], {"first_name": "C", "last_name": "D", "email": "taken@test.com"})


# ---------------------------------------------------------------------------
# patch_user
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E05")
def test_patch_user(repo):
    created = svc.create_user(repo, {"first_name": "A", "last_name": "B", "email": "p@test.com"})
    patched = svc.patch_user(repo, created["id"], {"first_name": "Updated"})
    assert patched["first_name"] == "Updated"
    assert patched["last_name"] == "B"


@pytest.mark.req("REQ-USR-E05")
def test_patch_user_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.patch_user(repo, "00000000-0000-0000-0000-000000000000", {"first_name": "X"})


# ---------------------------------------------------------------------------
# delete_user
# ---------------------------------------------------------------------------

@pytest.mark.req("REQ-USR-E06")
def test_delete_user(repo):
    created = svc.create_user(repo, {"first_name": "A", "last_name": "B", "email": "del@test.com"})
    svc.delete_user(repo, created["id"])
    with pytest.raises(svc.NotFoundError):
        svc.get_user(repo, created["id"])


@pytest.mark.req("REQ-USR-E06")
def test_delete_user_not_found(repo):
    with pytest.raises(svc.NotFoundError):
        svc.delete_user(repo, "00000000-0000-0000-0000-000000000000")

# user-service — Tasks

## T-01 — Project scaffold

Set up the service folder structure and dependencies.

- Create `services/user-service/` with subdirectories `app/storage/`, `tests/unit/`, `tests/integration/`, `data/`
- Create `services/user-service/requirements.txt` with `flask`, `requests`, `pytest`, `pytest-cov`, `responses`
- Create `services/user-service/.gitignore` excluding `data/`, `__pycache__/`, `*.pyc`, `.coverage`
- Create empty `app/__init__.py` and `app/storage/__init__.py`

_Requirements: REQ-USR-E01_

---

## T-02 — Config and entrypoint

Centralise all environment variable reads and wire up Flask.

- Create `app/config.py`: reads `PORT` (default 5001), `STORAGE_BACKEND` (default `memory`), `DATA_DIR` (default `./data`)
- Create `app/__main__.py`: imports config, selects repository backend, registers blueprint, runs Flask on `0.0.0.0:PORT`

_Requirements: REQ-USR-E01, REQ-USR-E07_

---

## T-03 — Repository interface and memory backend

Define the abstract interface and the in-memory implementation.

- Create `app/repository.py`: abstract class `UserRepository` with methods `create`, `get`, `update`, `delete`, `list`
- Create `app/storage/memory.py`: `MemoryRepository` implementing `UserRepository` using a plain dict
- `list` supports filtering by `role` and `email` (case-insensitive) and pagination

_Requirements: REQ-USR-B03_

---

## T-04 — JSON and SQLite backends

Implement the two file-based backends.

- Create `app/storage/json_store.py`: `JsonRepository` — reads/writes `DATA_DIR/users.json` using stdlib `json`
- Create `app/storage/sqlite_store.py`: `SqliteRepository` — uses stdlib `sqlite3`, creates table on init, stores all user fields
- Both must satisfy the same `UserRepository` interface as the memory backend

_Requirements: REQ-USR-E01_

---

## T-05 — Service layer

Implement business logic with typed exceptions.

- Create `app/service.py` with functions: `create_user`, `list_users`, `get_user`, `replace_user`, `patch_user`, `delete_user`
- Define exception classes: `ValidationError`, `ConflictError`, `NotFoundError`
- `create_user` / `replace_user` / `patch_user`: normalise email to lowercase, check uniqueness → raise `ConflictError("EMAIL_ALREADY_EXISTS")` — REQ-USR-B01, REQ-USR-B02
- All write operations generate UUID v4 `id` (server-side), set `created_at` / `updated_at` ISO 8601 UTC
- Input validation (field lengths, email format, role enum) raises `ValidationError`

_Requirements: REQ-USR-B01, REQ-USR-B02, REQ-USR-B03_

---

## T-06 — Routes and error handlers

Expose the HTTP endpoints via a Flask blueprint.

- Create `app/routes.py` with blueprint `users_bp` registered at `/api/v1/users`
- Implement all 6 endpoints: POST, GET (list), GET `/{id}`, PUT `/{id}`, PATCH `/{id}`, DELETE `/{id}`
- Implement `GET /health` returning `{"status": "ok", "service": "user-service"}`
- Register error handler for malformed JSON → 400
- Translate service exceptions to HTTP responses using the standard error format `{"error": {"code": ..., "message": ..., "details": ...}}`
- POST 201 response includes `Location: /api/v1/users/{id}` header

_Requirements: REQ-USR-E01, REQ-USR-E02, REQ-USR-E03, REQ-USR-E04, REQ-USR-E05, REQ-USR-E06, REQ-USR-E07_

---

## T-07 — Unit tests: service layer

Test all business rules with the memory backend.

- `tests/unit/test_service.py`
- Test `create_user`: valid input → user created with UUID, timestamps, lowercase email
- Test `create_user`: duplicate email (different case) → `ConflictError` — REQ-USR-B01
- Test `create_user`: missing required field → `ValidationError`
- Test `list_users`: pagination, `role` filter, `email` filter — REQ-USR-B03
- Test `get_user`: found / not found
- Test `replace_user` / `patch_user`: updates `updated_at`, email conflict, not found
- Test `delete_user`: removes user / not found
- All tests use `@pytest.mark.req("REQ-USR-B0x")` or equivalent ID in docstring

_Requirements: REQ-USR-B01, REQ-USR-B02, REQ-USR-B03_

---

## T-08 — Unit tests: all storage backends

Verify all three backends satisfy the same contract.

- `tests/unit/test_storage.py`
- Parametrize with `memory`, `json` (using `tmp_path`), `sqlite` (using `tmp_path`)
- Test create → get → update → delete roundtrip for each backend
- Test `list` with filters and pagination for each backend

_Requirements: REQ-USR-E01_

---

## T-09 — Contract tests

Validate HTTP responses against the OpenAPI contract.

- `tests/unit/test_contract.py`
- Use Flask test client
- At least 1 test per endpoint calling `assert_matches_contract(service, method, path, response)` from `contracts/validator.py`
- Covers: POST 201, GET list 200, GET by id 200, GET by id 404, PUT 200, PATCH 200, DELETE 204, health 200

_Requirements: REQ-USR-E01 through REQ-USR-E07_

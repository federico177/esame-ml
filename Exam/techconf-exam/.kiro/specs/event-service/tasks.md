# event-service — Tasks

## T-01 — Project scaffold
- Create `services/event-service/` with subdirs `app/storage/`, `tests/unit/`, `tests/integration/`, `data/`
- Create `requirements.txt`, `.gitignore`, `pytest.ini`, `__init__.py` files

_Requirements: REQ-EVT-E01_

## T-02 — Config and entrypoint
- `app/config.py`: reads `PORT` (5002), `STORAGE_BACKEND`, `DATA_DIR`, `USER_SERVICE_URL`
- `app/__main__.py`: selects backend, registers blueprint, runs Flask on `PORT`

_Requirements: REQ-EVT-E01, REQ-EVT-E07_

## T-03 — Repository interface and memory backend
- `app/repository.py`: abstract `EventRepository` with `create`, `get`, `update`, `delete`, `list`
- `app/storage/memory.py`: `MemoryRepository` with filters for `status` (exact) and `city` (case-insensitive)

_Requirements: REQ-EVT-B06_

## T-04 — JSON and SQLite backends
- `app/storage/json_store.py`: `JsonRepository` using `DATA_DIR/events.json`
- `app/storage/sqlite_store.py`: `SqliteRepository` using `DATA_DIR/events.db`

_Requirements: REQ-EVT-E01_

## T-05 — HTTP client for user-service
- `app/clients.py`: `get_user(user_id)` with 2 s timeout
- Returns user dict on 200, None on 404, raises `DependencyError` on timeout/5xx

_Requirements: REQ-EVT-B01, REQ-EVT-B05_

## T-06 — Service layer
- `app/service.py`: `create_event`, `list_events`, `get_event`, `replace_event`, `patch_event`, `delete_event`
- Typed exceptions: `ValidationError`, `NotFoundError`, `DependencyError`, `ReferenceNotFoundError`, `InvalidOrganizerError`, `InvalidStatusTransitionError`
- REQ-EVT-B01: call `clients.get_user`, handle None → `ReferenceNotFoundError`
- REQ-EVT-B02: check `user.role == "organizer"` → `InvalidOrganizerError`
- REQ-EVT-B03: `end_date >= start_date` → `ValidationError`
- REQ-EVT-B04: enforce allowed transitions `draft→published`, `draft→cancelled`, `published→cancelled`

_Requirements: REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B03, REQ-EVT-B04, REQ-EVT-B05, REQ-EVT-B06_

## T-07 — Routes and error handlers
- `app/routes.py`: blueprint `events_bp` at `/api/v1/events`
- All 6 endpoints + `GET /health`
- Translate exceptions to HTTP; POST returns 201 + `Location` header
- 400 handler for malformed JSON

_Requirements: REQ-EVT-E01 through REQ-EVT-E07_

## T-08 — Unit tests
- `tests/unit/test_service.py`: all business rules, `clients.get_user` mocked with `responses`
- `tests/unit/test_storage.py`: all 3 backends parametrized
- `tests/unit/test_contract.py`: 1 test per endpoint with `assert_matches_contract`
- `@pytest.mark.req` markers on every test

_Requirements: REQ-EVT-B01 through REQ-EVT-B06_

## T-09 — Integration tests
- `tests/integration/test_integration.py`
- Fixture that starts user-service as subprocess on a free port
- Test 1 (positive): create organizer → create event → 201
- Test 2 (422): create event with non-existent organizer_id → 422 `REFERENCE_NOT_FOUND`
- Test 3 (503): start event-service with USER_SERVICE_URL pointing to closed port → 503 `DEPENDENCY_UNAVAILABLE`

_Requirements: REQ-EVT-B01, REQ-EVT-B05_

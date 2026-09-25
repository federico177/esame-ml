# registration-service — Tasks

## T-01 — Scaffold
- Create folder structure, `requirements.txt`, `.gitignore`, `pytest.ini`, `__init__.py` files
_Requirements: REQ-REG-E01_

## T-02 — Config and entrypoint
- `app/config.py`: PORT(5003), STORAGE_BACKEND, DATA_DIR, USER_SERVICE_URL, EVENT_SERVICE_URL
- `app/__main__.py`: backend selection, blueprint registration, Flask startup
_Requirements: REQ-REG-E01, REQ-REG-E08_

## T-03 — Repository interface + memory backend
- `app/repository.py`: abstract `RegistrationRepository` with `create`, `get`, `update`, `delete`, `list`, `count_confirmed`, `find_confirmed`
- `app/storage/memory.py`: `MemoryRepository`
_Requirements: REQ-REG-B04, REQ-REG-B05_

## T-04 — JSON and SQLite backends
- `app/storage/json_store.py`
- `app/storage/sqlite_store.py`
_Requirements: REQ-REG-E01_

## T-05 — HTTP clients
- `app/clients.py`: `get_user(user_id)`, `get_event(event_id)` with 2s timeout and DependencyError
_Requirements: REQ-REG-B01, REQ-REG-B02, REQ-REG-B09_

## T-06 — Service layer
- `create_registration`: B01(user exists), B02(event exists), B03(event published), B04(no duplicate), B05(capacity), B06(amount=price)
- `list_registrations`, `get_registration`, `patch_registration`: B07(confirmed→cancelled only)
- `delete_registration`, `get_stats`: B08(capacity/confirmed/available), B09(dependency errors)
_Requirements: REQ-REG-B01 through REQ-REG-B09_

## T-07 — Routes
- Blueprint at `/api/v1/registrations`
- All endpoints + `GET /health` + PUT→405
- Translate exceptions to HTTP responses
_Requirements: REQ-REG-E01 through REQ-REG-E08_

## T-08 — Unit + contract tests
- `test_service.py`: all B rules mocked with `responses`
- `test_storage.py`: 3 backends parametrized
- `test_contract.py`: 1 test per endpoint with `assert_matches_contract`
_Requirements: REQ-REG-B01 through REQ-REG-B09_

## T-09 — Integration tests
- Start user-service + event-service as subprocesses
- Test positive (201), reference not found (422), dependency down (503)
_Requirements: REQ-REG-B01, REQ-REG-B09_

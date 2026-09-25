# feedback-service — Tasks

## T-01 — Scaffold
Folder structure, requirements.txt, .gitignore, pytest.ini, __init__.py
_Requirements: REQ-FBK-E01_

## T-02 — Config + entrypoint
config.py (PORT 5004, REGISTRATION_SERVICE_URL, EVENT_SERVICE_URL), __main__.py
_Requirements: REQ-FBK-E01, REQ-FBK-E07_

## T-03 — Repository + memory backend
FeedbackRepository (create,get,update,delete,list,find_by_user_event,list_by_event), memory.py
_Requirements: REQ-FBK-B02, REQ-FBK-B03_

## T-04 — JSON + SQLite backends
json_store.py, sqlite_store.py
_Requirements: REQ-FBK-E01_

## T-05 — Clients
has_confirmed_registration(), get_event(), 2s timeout, DependencyError
_Requirements: REQ-FBK-B01, REQ-FBK-B04_

## T-06 — Service layer
create/list/get/patch/delete/summary with B01,B02,B03
_Requirements: REQ-FBK-B01, REQ-FBK-B02, REQ-FBK-B03, REQ-FBK-B04_

## T-07 — Routes
Blueprint /api/v1/feedbacks, all endpoints + /health + /summary (before /{id})
_Requirements: REQ-FBK-E01 through REQ-FBK-E07_

## T-08 — Unit + contract tests
test_service, test_storage (3 backends), test_contract (1 per endpoint)
_Requirements: REQ-FBK-B01 through REQ-FBK-B04_

## T-09 — Integration tests
Start user+event+registration+feedback; positive, not registered (422), dependency down (503)
_Requirements: REQ-FBK-B01, REQ-FBK-B04_

# notification-service — Design

## Contract reference
`contracts/openapi/notification-service.yaml`

## Componenti
app/: __main__.py, config.py, routes.py, service.py, repository.py, clients.py, storage/{memory,json_store,sqlite_store}.py

### config.py
PORT(5005), STORAGE_BACKEND, DATA_DIR, USER_SERVICE_URL, REGISTRATION_SERVICE_URL

### clients.py
- get_user(user_id) -> dict | None
- list_confirmed_registrations(event_id) -> list of registrations (user_id extracted)
- 2s timeout, DependencyError on 5xx/timeout

### service.py
create_notification (B01), list, get, patch_notification (B02 transitions + sent_at), delete, broadcast (B03)
Exceptions: ValidationError, NotFoundError, DependencyError, ReferenceNotFoundError, InvalidStatusTransitionError

### repository.py
NotificationRepository: create, get, update, delete, list

## Persistenza
3 backend (memory/json/sqlite), notifications.json / notifications.db

## Chiamate esterne
| Servizio | Endpoint | Errore |
|---|---|---|
| user | GET /api/v1/users/{id} | 404->422 REFERENCE_NOT_FOUND, 5xx->503 |
| registration | GET /api/v1/registrations?event_id=&status=confirmed&page_size=100 | 5xx->503 |

## Errori
REFERENCE_NOT_FOUND 422, VALIDATION_ERROR 422, INVALID_STATUS_TRANSITION 422, NOT_FOUND 404, DEPENDENCY_UNAVAILABLE 503

## Test
Unit (mock responses), storage (3 backend), contract (1 per endpoint), integration (user+registration+notification reali)

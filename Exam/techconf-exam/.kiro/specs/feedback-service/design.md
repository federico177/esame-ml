# feedback-service — Design

## Contract reference
`contracts/openapi/feedback-service.yaml`

## Componenti
```
services/feedback-service/app/
  __main__.py, config.py, routes.py, service.py, repository.py
  clients.py               # get_confirmed_registration(), get_event()
  storage/ memory.py json_store.py sqlite_store.py
```

### config.py
PORT(5004), STORAGE_BACKEND, DATA_DIR, REGISTRATION_SERVICE_URL, EVENT_SERVICE_URL

### clients.py
- `has_confirmed_registration(user_id, event_id)` -> bool — chiama registration-service list con filtri
- `get_event(event_id)` -> dict | None
- timeout 2s, 5xx/timeout -> DependencyError

### service.py
- create_feedback: B01(registered), B02(unique)
- list_feedbacks, get_feedback, patch_feedback, delete_feedback
- get_summary: B03(count/average, event exists)
Exceptions: ValidationError, NotFoundError, ConflictError, DependencyError, NotRegisteredError

### repository.py
FeedbackRepository: create, get, update, delete, list, find_by_user_event, list_by_event

## Persistenza
3 backend intercambiabili (memory/json/sqlite), file feedbacks.json / feedbacks.db

## Chiamate esterne
| Servizio | Endpoint | Errore |
|---|---|---|
| registration | GET /api/v1/registrations?user_id=&event_id=&status=confirmed | vuoto->422 NOT_REGISTERED, 5xx->503 |
| event | GET /api/v1/events/{id} | 404->404 NOT_FOUND (summary), 5xx->503 |

## Errori
NOT_REGISTERED 422, FEEDBACK_ALREADY_EXISTS 409, VALIDATION_ERROR 422, NOT_FOUND 404, DEPENDENCY_UNAVAILABLE 503

## Test
Unit (mock responses), storage (3 backend), contract (1 per endpoint), integration (user+event+registration+feedback reali)

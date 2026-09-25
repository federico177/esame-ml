# registration-service — Design

## Contract reference

`contracts/openapi/registration-service.yaml` — fonte di verità per tutti gli endpoint.

---

## Componenti e responsabilità

```
services/registration-service/
├── app/
│   ├── __main__.py
│   ├── config.py          # PORT, STORAGE_BACKEND, DATA_DIR, USER_SERVICE_URL, EVENT_SERVICE_URL
│   ├── routes.py
│   ├── service.py         # REQ-REG-B01..B09
│   ├── repository.py
│   ├── storage/
│   │   ├── memory.py
│   │   ├── json_store.py
│   │   └── sqlite_store.py
│   └── clients.py         # get_user(), get_event()
├── tests/unit/
├── tests/integration/
├── requirements.txt
└── data/
```

### `config.py`
```python
PORT                    = int(os.environ.get("PORT", 5003))
STORAGE_BACKEND         = os.environ.get("STORAGE_BACKEND", "memory")
DATA_DIR                = os.environ.get("DATA_DIR", "./data")
USER_SERVICE_URL        = os.environ.get("USER_SERVICE_URL", "http://localhost:5001")
EVENT_SERVICE_URL       = os.environ.get("EVENT_SERVICE_URL", "http://localhost:5002")
```

### `clients.py`
- `get_user(user_id)` → dict | None — 404 = None, 5xx/timeout = DependencyError
- `get_event(event_id)` → dict | None — 404 = None, 5xx/timeout = DependencyError

### `service.py`
Funzioni principali:
- `create_registration(repo, data)` — REQ-REG-B01..B06
- `list_registrations(repo, page, page_size, user_id, event_id, status)` — REQ-REG-E02
- `get_registration(repo, id)` — REQ-REG-E03
- `patch_registration(repo, id, data)` — REQ-REG-B07
- `delete_registration(repo, id)` — REQ-REG-E05
- `get_stats(repo, event_id)` — REQ-REG-B08

Eccezioni: `ValidationError`, `NotFoundError`, `ConflictError`, `DependencyError`,
`ReferenceNotFoundError`, `EventNotOpenError`, `InvalidStatusTransitionError`.

### `repository.py`
`RegistrationRepository` con metodi: `create`, `get`, `update`, `delete`, `list`,
`count_confirmed(event_id)`, `find_confirmed(user_id, event_id)`.

---

## Persistenza

Identica agli altri servizi: 3 backend (`memory`, `json`, `sqlite`) intercambiabili.
- `memory`: dizionario
- `json`: `DATA_DIR/registrations.json`
- `sqlite`: `DATA_DIR/registrations.db`, tabella `registrations`

---

## Chiamate ad altri servizi

| Servizio | Endpoint | Quando | Errore |
|---|---|---|---|
| user-service | `GET /api/v1/users/{user_id}` | POST | 404→422 `REFERENCE_NOT_FOUND`, 5xx→503 |
| event-service | `GET /api/v1/events/{event_id}` | POST, stats | 404→422/404, 5xx→503 |

---

## Gestione errori

| Situazione | Eccezione | HTTP |
|---|---|---|
| Campo mancante | `ValidationError` | 422 `VALIDATION_ERROR` |
| user non trovato | `ReferenceNotFoundError` | 422 `REFERENCE_NOT_FOUND` |
| evento non trovato | `ReferenceNotFoundError` | 422 `REFERENCE_NOT_FOUND` |
| evento non published | `EventNotOpenError` | 422 `EVENT_NOT_OPEN` |
| già iscritto (confirmed) | `ConflictError("ALREADY_REGISTERED")` | 409 |
| evento pieno | `ConflictError("EVENT_FULL")` | 409 |
| transizione non ammessa | `InvalidStatusTransitionError` | 422 `INVALID_STATUS_TRANSITION` |
| registrazione non trovata | `NotFoundError` | 404 `NOT_FOUND` |
| dipendenza irraggiungibile | `DependencyError` | 503 `DEPENDENCY_UNAVAILABLE` |
| PUT | — | 405 `METHOD_NOT_ALLOWED` |

---

## Strategia di test

### Unit test
- `test_service.py`: tutte le regole B01..B09 con mock HTTP via `responses`
- `test_storage.py`: tutti e 3 i backend parametrizzati
- `test_contract.py`: 1 test per endpoint con `assert_matches_contract`

### Integration test
- Avvia user-service ed event-service come subprocess su porte libere
- Test positivo, 422 riferimento inesistente, 503 dipendenza spenta

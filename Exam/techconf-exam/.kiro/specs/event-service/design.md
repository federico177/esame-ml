# event-service — Design

## Contract reference

`contracts/openapi/event-service.yaml` — fonte di verità per tutti gli endpoint, schemi e codici di risposta.

---

## Componenti e responsabilità

```
services/event-service/
├── app/
│   ├── __main__.py       # entrypoint: legge PORT, avvia Flask
│   ├── config.py         # legge PORT, STORAGE_BACKEND, DATA_DIR, USER_SERVICE_URL
│   ├── routes.py         # blueprint Flask: HTTP layer
│   ├── service.py        # logica di business (REQ-EVT-B*)
│   ├── repository.py     # interfaccia astratta EventRepository
│   ├── storage/
│   │   ├── memory.py
│   │   ├── json_store.py
│   │   └── sqlite_store.py
│   └── clients.py        # chiamate HTTP a user-service
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── data/
```

### `config.py`
```python
PORT             = int(os.environ.get("PORT", 5002))
STORAGE_BACKEND  = os.environ.get("STORAGE_BACKEND", "memory")
DATA_DIR         = os.environ.get("DATA_DIR", "./data")
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://localhost:5001")
```

### `clients.py`
Unica funzione rilevante:
```python
def get_user(user_id: str) -> dict | None
```
- Timeout: 2 s
- 200 → restituisce il dict utente
- 404 → restituisce `None`
- Timeout / connessione rifiutata / 5xx → solleva `DependencyError`

### `service.py`
Funzioni principali:
- `create_event(repo, data)` — REQ-EVT-B01, B02, B03
- `list_events(repo, page, page_size, status, city)` — REQ-EVT-B06
- `get_event(repo, id)` — REQ-EVT-E03
- `replace_event(repo, id, data)` — REQ-EVT-B01, B02, B03, B04
- `patch_event(repo, id, data)` — REQ-EVT-B01, B02, B03, B04
- `delete_event(repo, id)` — REQ-EVT-E06

Eccezioni tipizzate: `ValidationError`, `NotFoundError`, `DependencyError`, `ReferenceNotFoundError`, `InvalidOrganizerError`, `InvalidStatusTransitionError`.

### `repository.py`
Interfaccia astratta `EventRepository` con metodi: `create`, `get`, `update`, `delete`, `list`.

---

## Persistenza

Identica al user-service: 3 backend (`memory`, `json`, `sqlite`) intercambiabili senza toccare `service.py`.

- Backend `memory`: dizionario in memoria
- Backend `json`: `DATA_DIR/events.json`
- Backend `sqlite`: `DATA_DIR/events.db`, tabella `events`

---

## Chiamate ad altri servizi

### user-service
- URL da `USER_SERVICE_URL` (mai hardcoded)
- Endpoint chiamato: `GET /api/v1/users/{organizer_id}`
- Timeout: 2 s
- Logica di errore:
  - 404 → 422 `REFERENCE_NOT_FOUND` (REQ-EVT-B01)
  - user.role ≠ organizer → 422 `INVALID_ORGANIZER` (REQ-EVT-B02)
  - timeout / 5xx → 503 `DEPENDENCY_UNAVAILABLE` (REQ-EVT-B05)

---

## Gestione errori

| Situazione | Eccezione interna | HTTP |
|---|---|---|
| Campo mancante / valore non valido | `ValidationError` | 422 `VALIDATION_ERROR` |
| end_date < start_date | `ValidationError` | 422 `VALIDATION_ERROR` |
| organizer_id non trovato | `ReferenceNotFoundError` | 422 `REFERENCE_NOT_FOUND` |
| organizer non ha role=organizer | `InvalidOrganizerError` | 422 `INVALID_ORGANIZER` |
| transizione di status non ammessa | `InvalidStatusTransitionError` | 422 `INVALID_STATUS_TRANSITION` |
| evento non trovato | `NotFoundError` | 404 `NOT_FOUND` |
| user-service irraggiungibile | `DependencyError` | 503 `DEPENDENCY_UNAVAILABLE` |
| JSON malformato | handler Flask | 400 |

---

## Strategia di test

### Unit test (`tests/unit/`)
- `test_service.py`: tutte le regole di business con mock di `clients.py` tramite `responses`
- `test_storage.py`: tutti e 3 i backend parametrizzati con `tmp_path`
- `test_contract.py`: almeno 1 test per endpoint con `assert_matches_contract`
- Coverage target: ≥ 80%

### Integration test (`tests/integration/`)
- Avvia user-service in un subprocess su porta libera
- Verifica: 1 caso positivo (organizer valido → 201), 1 riferimento inesistente (422), 1 dipendenza spenta (503)

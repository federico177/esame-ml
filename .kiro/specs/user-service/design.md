# user-service — Design

## Contract reference

`contracts/openapi/user-service.yaml` — fonte di verità per tutti gli endpoint, schemi e codici di risposta.
Ogni risposta prodotta dal servizio viene validata contro questo contratto nei test.

---

## Componenti e responsabilità

```
services/user-service/
├── app/
│   ├── __main__.py       # entrypoint: legge PORT da env, avvia Flask
│   ├── config.py         # centralizza la lettura di tutte le variabili d'ambiente
│   ├── routes.py         # blueprint Flask: parsing HTTP, validazione input, serializzazione
│   ├── service.py        # logica di business (regole REQ-USR-B*), orchestrazione
│   ├── repository.py     # interfaccia Repository (metodi: create, get, update, delete, list)
│   └── storage/
│       ├── memory.py     # MemoryRepository — dizionario in memoria
│       ├── json_store.py # JsonRepository — file JSON in DATA_DIR
│       └── sqlite_store.py # SqliteRepository — SQLite in DATA_DIR
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── data/                 # esclusa da git
```

### `__main__.py`
- Legge `PORT` da `config.py`
- Registra il blueprint e avvia `app.run(host="0.0.0.0", port=PORT)`

### `config.py`
Legge una sola volta all'avvio:
```python
PORT             = int(os.environ.get("PORT", 5001))
STORAGE_BACKEND  = os.environ.get("STORAGE_BACKEND", "memory")  # memory | json | sqlite
DATA_DIR         = os.environ.get("DATA_DIR", "./data")
```
Nessun'altra parte del codice chiama `os.environ` direttamente.

### `routes.py`
- Definisce il Flask blueprint `/api/v1/users`
- Responsabilità: parsare il body JSON, chiamare `service.py`, serializzare la risposta
- Non contiene logica di business
- Gestisce `400` per JSON malformato con l'error handler di Flask

### `service.py`
Contiene tutte le regole di business:
- `create_user(data)` — REQ-USR-B01, REQ-USR-B02
- `list_users(page, page_size, role, email)` — REQ-USR-B03
- `get_user(id)` — REQ-USR-E03
- `replace_user(id, data)` — REQ-USR-B01, REQ-USR-B02
- `patch_user(id, data)` — REQ-USR-B01, REQ-USR-B02
- `delete_user(id)` — REQ-USR-E06

Ogni metodo solleva eccezioni tipizzate (`NotFoundError`, `ConflictError`, `ValidationError`) che `routes.py` cattura e traduce in risposte HTTP.

### `repository.py`
Interfaccia astratta (classe base con metodi astratti):
```python
class UserRepository:
    def create(self, user: dict) -> dict: ...
    def get(self, id: str) -> dict | None: ...
    def update(self, id: str, data: dict) -> dict: ...
    def delete(self, id: str) -> None: ...
    def list(self, filters: dict, page: int, page_size: int) -> tuple[list, int]: ...
```
Il backend viene scelto in `__main__.py` in base a `STORAGE_BACKEND` e iniettato in `service.py`.

---

## Persistenza

### Backend `memory`
- Dizionario Python `{id: user_dict}` in memoria
- Dati persi al riavvio — usato di default e nei test

### Backend `json`
- File `DATA_DIR/users.json`
- Lettura/scrittura dell'intero file ad ogni operazione
- Libreria standard `json`

### Backend `sqlite`
- File `DATA_DIR/users.db`
- Tabella `users` con colonne corrispondenti ai campi
- Libreria standard `sqlite3`
- Creazione automatica della tabella all'avvio se non esiste

Il cambio di backend avviene solo in `__main__.py` (selezione) e in `storage/`
(implementazione): `service.py` e `routes.py` non cambiano.

---

## Chiamate ad altri servizi

Il user-service **non chiama** nessun altro servizio — è il servizio base della piattaforma.
È invece chiamato da event-service, registration-service e notification-service.

---

## Gestione errori

| Situazione | Eccezione interna | HTTP |
|---|---|---|
| Campo mancante / valore non valido | `ValidationError` | 422 `VALIDATION_ERROR` |
| Email già esistente | `ConflictError("EMAIL_ALREADY_EXISTS")` | 409 |
| Utente non trovato | `NotFoundError` | 404 `NOT_FOUND` |
| JSON malformato | handler Flask `@app.errorhandler` | 400 |

Tutte le risposte di errore seguono il formato:
```json
{"error": {"code": "UPPER_SNAKE", "message": "...", "details": {}}}
```

---

## Strategia di test

### Unit test (`tests/unit/`)
- Testano `service.py` con il backend `memory` (nessun I/O)
- Testano `storage/json_store.py` e `storage/sqlite_store.py` con `tmp_path` pytest
- Mock non necessario (nessuna chiamata HTTP esterna)
- Coverage target: ≥ 80%
- Almeno 1 test per endpoint che chiama `assert_matches_contract` dal contratto OpenAPI
- Marker `@pytest.mark.req("REQ-USR-B01")` su ogni test

### Integration test (`tests/integration/`)
- Non necessari per user-service (non chiama altri servizi)
- La validazione esterna è coperta dalla suite del docente (`tests/integration/`)

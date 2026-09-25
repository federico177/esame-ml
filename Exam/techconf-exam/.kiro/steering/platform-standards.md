# TechConf — Platform Standards

Queste regole sono **vincolanti per tutti i microservizi**. Kiro deve rispettarle in ogni task di implementazione.

## Avvio e configurazione

- Ogni servizio legge la porta dalla variabile d'ambiente `PORT` (mai hardcoded)
- Il file `services.yaml` nella root dichiara `cwd` e `command` per ogni servizio
- La suite di collaudo inietta `PORT` e `*_SERVICE_URL`; il servizio deve usare solo quelle

## Base path e formato

- Base path: `/api/v1/<risorsa>` (es. `/api/v1/users`)
- Formato: **JSON**, campi in `snake_case`
- Encoding: UTF-8

## Identificativi

- `id` è un **UUID v4** generato dal server
- L'`id` non è mai accettato in input dal client

## Timestamp e date

- Timestamp: **ISO 8601 UTC** — `2026-10-15T09:30:00Z`
- Ogni risorsa ha `created_at` e `updated_at` (read-only, gestiti dal server)
- Date: `YYYY-MM-DD`
- Importi: numerici con 2 decimali (`149.00`), valuta implicita EUR

## Paginazione

Query params: `?page=1&page_size=20` (max 100)

Risposta:
```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 57
}
```

## Formato errori

Tutti gli errori usano **sempre** questa struttura:
```json
{
  "error": {
    "code": "UPPER_SNAKE_CASE",
    "message": "Descrizione leggibile",
    "details": {}
  }
}
```

## Status code

| Situazione | Codice |
|---|---|
| Creazione riuscita | **201** + header `Location: /api/v1/<risorsa>/<id>` |
| Lettura / modifica riuscita | **200** |
| Cancellazione riuscita | **204** (body vuoto) |
| JSON malformato | **400** |
| Risorsa non trovata | **404** `NOT_FOUND` |
| Metodo non previsto | **405** |
| Conflitto (es. email duplicata) | **409** |
| Errore di validazione / riferimento non trovato | **422** `VALIDATION_ERROR` / `REFERENCE_NOT_FOUND` |
| Dipendenza non raggiungibile | **503** `DEPENDENCY_UNAVAILABLE` |

## Chiamate tra servizi

- Gli URL degli altri servizi vengono letti **solo** da variabili d'ambiente:
  - `USER_SERVICE_URL` (default: `http://localhost:5001`)
  - `EVENT_SERVICE_URL` (default: `http://localhost:5002`)
  - `REGISTRATION_SERVICE_URL` (default: `http://localhost:5003`)
  - `FEEDBACK_SERVICE_URL` (default: `http://localhost:5004`)
  - `NOTIFICATION_SERVICE_URL` (default: `http://localhost:5005`)
- **Timeout: 2 secondi**
- Se il servizio chiamato risponde 404 → **422** `REFERENCE_NOT_FOUND`
- Se il servizio chiamato è irraggiungibile, va in timeout o risponde 5xx → **503** `DEPENDENCY_UNAVAILABLE`

## Health check

```
GET /health  →  200  {"status": "ok", "service": "<nome-servizio>"}
```

## Persistenza

- Variabile `STORAGE_BACKEND`: `memory` (default) | `json` | `sqlite`
- Con `json`/`sqlite` i file vanno in `DATA_DIR` (default `./data`, esclusa da git)
- Solo librerie standard (`json`, `sqlite3`): nessun DBMS esterno
- Il cambio di backend **non deve richiedere modifiche alla logica di business**

# TechConf — Technology Stack

## Runtime

- **Python 3.12**
- **Flask** — framework HTTP per ogni microservizio
- **requests** — chiamate HTTP tra microservizi

## Test

- **pytest** — framework di test
- **pytest-cov** — coverage (target ≥ 80% per servizio)
- **responses** — mock delle chiamate HTTP verso altri servizi nei test unitari

## Persistenza

Ogni servizio supporta 3 backend, selezionato tramite la variabile d'ambiente `STORAGE_BACKEND`:

| Valore | Backend | Note |
|---|---|---|
| `memory` (default) | Dizionario in memoria | Dati persi al riavvio — usato nei test |
| `json` | File JSON in `DATA_DIR` | Libreria standard `json` |
| `sqlite` | Database SQLite in `DATA_DIR` | Libreria standard `sqlite3` |

- `DATA_DIR` default: `./data` (esclusa da git)
- Il cambio di backend **non deve richiedere modifiche alla logica di business**
- Nessun DBMS esterno da installare o configurare
- Solo librerie standard per la persistenza (`json`, `sqlite3`)

## Dipendenze Python

Ogni servizio ha il proprio `requirements.txt`:

```
# runtime
flask
requests

# test
pytest
pytest-cov
responses
```

Nessuna altra dipendenza esterna è ammessa.

## Avvio

Ogni servizio si avvia con:
```bash
python -m app
```

La porta è sempre letta dalla variabile d'ambiente `PORT`.

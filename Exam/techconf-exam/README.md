# TechConf — Microservizi per la gestione delle conferenze

Piattaforma a microservizi (Spec-Driven Development con Kiro) per gestire utenti, eventi
e iscrizioni a conferenze tech.

## Servizi implementati (obbligatori)

| Servizio | Base path | Porta dev | Chiama |
|---|---|---|---|
| user-service | `/api/v1/users` | 5001 | — |
| event-service | `/api/v1/events` | 5002 | user |
| registration-service | `/api/v1/registrations` | 5003 | user, event |

## Requisiti

- Python 3.12
- Dipendenze runtime: `flask`, `requests` (solo librerie standard per la persistenza)

Installazione dipendenze (per servizio):
```bash
pip install -r services/user-service/requirements.txt
pip install -r services/event-service/requirements.txt
pip install -r services/registration-service/requirements.txt
```

## Avvio dei servizi

Ogni servizio si avvia con lo stesso comando, dalla sua cartella:
```bash
cd services/user-service && PORT=5001 python -m app
cd services/event-service && PORT=5002 USER_SERVICE_URL=http://localhost:5001 python -m app
cd services/registration-service && PORT=5003 USER_SERVICE_URL=http://localhost:5001 EVENT_SERVICE_URL=http://localhost:5002 python -m app
```

Su Windows PowerShell:
```powershell
$env:PORT=5001; cd services/user-service; python -m app
```

## Variabili d'ambiente

| Variabile | Default | Descrizione |
|---|---|---|
| `PORT` | 5001/5002/5003 | Porta di ascolto (obbligatoria in collaudo) |
| `STORAGE_BACKEND` | `memory` | `memory` \| `json` \| `sqlite` |
| `DATA_DIR` | `./data` | Cartella per i file json/sqlite (esclusa da git) |
| `USER_SERVICE_URL` | `http://localhost:5001` | URL di user-service |
| `EVENT_SERVICE_URL` | `http://localhost:5002` | URL di event-service |

## Persistenza

Backend intercambiabile senza modifiche alla logica di business:
- `memory` — dizionario in memoria (default, usato nei test)
- `json` — file JSON in `DATA_DIR`
- `sqlite` — database SQLite in `DATA_DIR` (stdlib `sqlite3`)

## Test

Unit test di un singolo servizio (con coverage):
```bash
cd services/user-service && python -m pytest tests/unit/ --cov=app
cd services/event-service && python -m pytest tests/unit/ --cov=app
cd services/registration-service && python -m pytest tests/unit/ --cov=app
```

Test di integrazione propri (avviano i servizi reali):
```bash
cd services/event-service && python -m pytest tests/integration/
cd services/registration-service && python -m pytest tests/integration/
```

Coverage attuale: user 89%, event 84%, registration 86% (target >= 80%).

## Suite di collaudo (docente)

```bash
pip install -r tests/integration/requirements.txt
python -m pytest tests/integration -m mandatory -v
```

Risultato: **27/27 test obbligatori passati** (output in `collaudo.txt`).

## Struttura del progetto

```
techconf-exam/
├── .kiro/
│   ├── steering/        # product, tech, structure, platform-standards
│   ├── specs/           # requirements/design/tasks per ogni servizio
│   └── hooks/           # agent hook: test al salvataggio
├── contracts/           # OpenAPI (non modificabili)
├── services/
│   ├── user-service/
│   ├── event-service/
│   └── registration-service/
├── tests/integration/   # suite di collaudo (non modificabile)
├── services.yaml
├── BUGS.md
└── collaudo.txt
```

## Note

- I file in `contracts/` e `tests/integration/` non sono stati modificati.
- Gli URL degli altri servizi sono letti solo da variabili d'ambiente.
- La cartella `data/` è esclusa da git.

# TechConf — Code Structure

## Repository e confini dei servizi

Un unico repository (monorepo) con tutti i servizi, ognuno in una cartella separata sotto `services/`.

```
techconf-exam/
├── .kiro/
│   ├── steering/
│   └── specs/
│       ├── user-service/
│       ├── event-service/
│       └── registration-service/
├── contracts/
│   └── openapi/
├── services/
│   ├── user-service/
│   ├── event-service/
│   └── registration-service/
├── tests/
│   └── integration/          ← suite del docente, non modificabile
├── services.yaml
├── services.example.yaml
└── BUGS.md
```

**Motivazione**: monorepo semplifica la suite di collaudo (un solo `services.yaml`), il versionamento e la condivisione degli standard. I confini tra servizi sono resi espliciti dalla struttura delle cartelle: un servizio non può importare codice di un altro.

## Struttura interna di ogni servizio

```
services/<nome>-service/
├── app/
│   ├── __main__.py       ← entrypoint: legge PORT e avvia Flask
│   ├── config.py         ← legge tutte le variabili d'ambiente (PORT, *_URL, STORAGE_BACKEND, DATA_DIR)
│   ├── routes.py         ← definizione delle route Flask (HTTP layer)
│   ├── service.py        ← logica di business e regole REQ-*-B*
│   ├── repository.py     ← interfaccia astratta di persistenza
│   ├── storage/
│   │   ├── memory.py     ← backend in memoria
│   │   ├── json_store.py ← backend JSON
│   │   └── sqlite_store.py ← backend SQLite
│   └── clients.py        ← chiamate HTTP verso gli altri servizi
├── tests/
│   ├── unit/
│   └── integration/      ← test di integrazione propri (avvia i servizi dipendenti)
├── requirements.txt
└── data/                 ← esclusa da git
```

**Separazione delle responsabilità**:
- `routes.py`: parsing HTTP, validazione input, serializzazione risposta — nessuna logica di business
- `service.py`: regole di business (`REQ-*-B*`), orchestrazione, chiamate ai client
- `repository.py`: interfaccia con metodi `create`, `get`, `update`, `delete`, `list` — mai dipende da Flask
- `storage/`: implementazioni concrete del repository, intercambiabili senza toccare service.py
- `clients.py`: wrapper per le chiamate HTTP agli altri servizi, con gestione timeout e traduzione errori

## Codice condiviso

**Nessuna libreria condivisa tra servizi.** Ogni servizio è autonomo e duplica i piccoli helper (formato errori, paginazione, validazione UUID). Questa scelta:
- elimina l'accoppiamento tra servizi
- permette a team diversi di sviluppare servizi indipendentemente
- semplifica il deployment (ogni servizio ha solo `flask` e `requests`)

## Configurazione e avvio

Tutte le variabili d'ambiente sono lette **una sola volta** in `config.py` all'avvio. Nessun'altra parte del codice chiama `os.environ` direttamente.

Comando di avvio uniforme per tutti i servizi:
```bash
python -m app
```

## Test

- Test unitari in `services/<nome>/tests/unit/` — mock HTTP con `responses`
- Test di integrazione propri in `services/<nome>/tests/integration/`
- Un singolo comando per servizio: `pytest services/<nome>/tests/`
- Un singolo comando per tutto: `pytest services/`
- Coverage: `pytest --cov=app services/<nome>/tests/unit/`

## Tracciabilità requisiti

- Ogni test usa `@pytest.mark.req("REQ-XXX-B01")` o l'ID nella docstring
- Partendo da `REQ-REG-B05`: `service.py` contiene il commento `# REQ-REG-B05`, il test ha il marker corrispondente

## Dati e Git

- `data/` è nel `.gitignore` di ogni servizio e nella root
- I file JSON/SQLite non vengono mai committati

# BUGS.md — Registro dei bug

Registro dei bug trovati durante lo sviluppo e il collaudo dei microservizi TechConf.

| ID | Issue | Trovato da | Tipo | Requisito | Causa radice | Test di regressione | Commit |
|---|---|---|---|---|---|---|---|
| BUG-01 | #1 | dev (routing) | impl | REQ-REG-B08 | La route `/api/v1/registrations/stats` veniva intercettata dalla route `/api/v1/registrations/<id>` quando dichiarata dopo di essa: Flask trattava "stats" come un id di registrazione, restituendo 404 invece delle statistiche | `test_stats_200_contract` | (vedi git log) |
| BUG-02 | #2 | test contract | impl | REQ-USR-E01 | Il validator del contratto (`assert_matches_contract`) invoca `response.json()` come metodo, ma il Flask test client espone `json` come attributo (dict): la chiamata sollevava `TypeError: 'dict' object is not callable`. Risolto introducendo un adapter `FlaskTestResponseAdapter` che espone `.json()` come metodo | `test_health_contract` (e tutti i contract test) | (vedi git log) |

---

## Dettaglio BUG-01 — Ordine delle route `/stats` vs `/{id}`

**Servizio:** registration-service
**Comportamento atteso:** `GET /api/v1/registrations/stats?event_id=X` restituisce 200 con `{event_id, capacity, confirmed, available}`.
**Comportamento osservato (prima del fix):** 404 `NOT_FOUND`, perché la stringa "stats" veniva interpretata come `{id}`.

**Causa radice:** in Flask le route vengono valutate anche in base all'ordine e alla specificità. La route statica `/registrations/stats` deve essere registrata **prima** della route dinamica `/registrations/<string:reg_id>`, altrimenti quest'ultima cattura anche "stats".

**Fix:** dichiarazione della route `/stats` prima della route `/<reg_id>` in `routes.py`.

**Tipo:** bug di implementazione (la spec REQ-REG-B08 era corretta, il codice no).

---

## Dettaglio BUG-02 — Adapter per il validator del contratto

**Servizio:** tutti (test di contratto)
**Comportamento atteso:** `assert_matches_contract(...)` valida la risposta contro il contratto OpenAPI.
**Comportamento osservato (prima del fix):** `TypeError: 'dict' object is not callable` durante l'estrazione del body.

**Causa radice:** il `validator.py` fornito dal docente si aspetta un oggetto stile `requests.Response`, dove `.json()` è un **metodo**. Il Flask test client, invece, espone `.json` come **attributo** già deserializzato. Chiamare `resp.json()` sul test client tenta quindi di invocare un dict.

**Fix:** wrapper `FlaskTestResponseAdapter` nei test di contratto che espone `status_code`, `headers`, `text` e un metodo `json()` compatibile con l'interfaccia attesa dal validator. Nessuna modifica al file protetto `contracts/validator.py`.

**Tipo:** bug di implementazione (nel codice di test, non nella spec).

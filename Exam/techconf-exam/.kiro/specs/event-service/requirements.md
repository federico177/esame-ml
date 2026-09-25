# event-service — Requirements

## Overview

Conference management service. Handles events with lifecycle (draft → published → cancelled)
and capacity. Calls user-service to validate the organizer on create/update.

---

## Endpoints

### REQ-EVT-E01 — Create event (POST /api/v1/events)

**User story:** As an organizer, I want to create a new event so that participants can register.

**Acceptance criteria**
1. WHEN a valid POST body is sent with all required fields THE SYSTEM SHALL create the event, generate a UUID v4 `id`, set `created_at` and `updated_at` to the current UTC timestamp, default `status` to `draft`, and respond 201 with the event object and a `Location` header.
2. IF the request body is not valid JSON THEN THE SYSTEM SHALL respond 400.
3. IF any required field is missing or fails validation THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
4. IF user-service is unreachable or returns 5xx THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-EVT-E02 — List events (GET /api/v1/events)

**User story:** As a client, I want to list events with optional filters so that I can find relevant conferences.

**Acceptance criteria**
1. WHEN a GET request is sent THE SYSTEM SHALL return a paginated response `{items, page, page_size, total}` with default `page=1`, `page_size=20`.
2. WHEN `status` query param is provided THE SYSTEM SHALL return only events with that status.
3. WHEN `city` query param is provided THE SYSTEM SHALL return only events in that city (case-insensitive match).
4. IF `page` or `page_size` are invalid THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.

---

### REQ-EVT-E03 — Get event by id (GET /api/v1/events/{id})

**Acceptance criteria**
1. WHEN a valid id is provided and the event exists THE SYSTEM SHALL respond 200 with the full event object.
2. IF the event does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

---

### REQ-EVT-E04 — Replace event (PUT /api/v1/events/{id})

**Acceptance criteria**
1. WHEN a valid PUT body is sent and the event exists THE SYSTEM SHALL update all fields, set `updated_at`, and respond 200.
2. IF the event does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.
3. IF validation fails THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
4. IF user-service is unreachable THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-EVT-E05 — Partial update (PATCH /api/v1/events/{id})

**Acceptance criteria**
1. WHEN a PATCH body with one or more valid fields is sent and the event exists THE SYSTEM SHALL update only the provided fields, set `updated_at`, and respond 200.
2. IF the event does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.
3. IF a provided field fails validation THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
4. IF user-service is unreachable when `organizer_id` is being changed THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-EVT-E06 — Delete event (DELETE /api/v1/events/{id})

**Acceptance criteria**
1. WHEN a valid id is provided and the event exists THE SYSTEM SHALL delete the event and respond 204.
2. IF the event does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

---

### REQ-EVT-E07 — Health check (GET /health)

**Acceptance criteria**
1. WHEN GET /health is called THE SYSTEM SHALL always respond 200 with `{"status": "ok", "service": "event-service"}`.

---

## Business rules

### REQ-EVT-B01 — Organizer must exist

**User story:** As the platform, I want to ensure events are created only by registered organizers.

**Acceptance criteria**
1. WHEN an event is created or updated with an `organizer_id` THE SYSTEM SHALL call `GET /api/v1/users/{organizer_id}` on user-service.
2. IF user-service returns 404 THEN THE SYSTEM SHALL respond 422 with code `REFERENCE_NOT_FOUND`.
3. IF user-service returns 5xx or is unreachable THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-EVT-B02 — Organizer must have role = organizer

**Acceptance criteria**
1. WHEN the user returned by user-service has `role ≠ organizer` THE SYSTEM SHALL respond 422 with code `INVALID_ORGANIZER`.

---

### REQ-EVT-B03 — end_date must be ≥ start_date

**Acceptance criteria**
1. WHEN `end_date` is before `start_date` THE SYSTEM SHALL respond 422 with code `VALIDATION_ERROR`.
2. WHEN `end_date` equals `start_date` THE SYSTEM SHALL accept the event (single-day event).

---

### REQ-EVT-B04 — Status transitions

**User story:** As an organizer, I want controlled state transitions so that events cannot go back to draft once published.

**Acceptance criteria**
1. WHEN `status` is updated THE SYSTEM SHALL only allow: `draft→published`, `draft→cancelled`, `published→cancelled`.
2. IF any other transition is attempted (e.g. `published→draft`, `cancelled→draft`, `cancelled→published`) THEN THE SYSTEM SHALL respond 422 with code `INVALID_STATUS_TRANSITION`.
3. WHEN `status` is not provided in a PATCH body THE SYSTEM SHALL leave the current status unchanged.

---

### REQ-EVT-B05 — Dependency unavailable

**Acceptance criteria**
1. WHEN user-service times out (> 2 s), refuses connection, or returns 5xx THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-EVT-B06 — List filters

**Acceptance criteria**
1. WHEN `status` filter is applied THE SYSTEM SHALL return only events whose `status` matches exactly.
2. WHEN `city` filter is applied THE SYSTEM SHALL return only events whose `city` matches case-insensitively.
3. Filters MAY be combined; when combined THE SYSTEM SHALL apply both (AND logic).

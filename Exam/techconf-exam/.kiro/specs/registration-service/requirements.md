# registration-service — Requirements

## Overview

Manages registrations of users to published events. Calls user-service to validate the user
and event-service to validate the event. Enforces capacity limits and duplicate prevention.

---

## Endpoints

### REQ-REG-E01 — Create registration (POST /api/v1/registrations)

**User story:** As a participant, I want to register for a published event so that I can attend.

**Acceptance criteria**
1. WHEN a valid POST body with `user_id` and `event_id` is sent THE SYSTEM SHALL validate both references, copy `amount` from `event.price`, create the registration with `status = confirmed`, and respond 201 with a `Location` header.
2. IF the request body is not valid JSON THEN THE SYSTEM SHALL respond 400.
3. IF `user_id` or `event_id` is missing THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
4. IF a dependency is unreachable THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-REG-E02 — List registrations (GET /api/v1/registrations)

**Acceptance criteria**
1. WHEN a GET request is sent THE SYSTEM SHALL return a paginated response with default `page=1`, `page_size=20`.
2. WHEN `user_id`, `event_id`, or `status` query params are provided THE SYSTEM SHALL filter accordingly.
3. IF pagination params are invalid THEN THE SYSTEM SHALL respond 422.

---

### REQ-REG-E03 — Get registration by id (GET /api/v1/registrations/{id})

**Acceptance criteria**
1. WHEN a valid id is provided and the registration exists THE SYSTEM SHALL respond 200.
2. IF the registration does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

---

### REQ-REG-E04 — Patch registration status (PATCH /api/v1/registrations/{id})

**Acceptance criteria**
1. WHEN a PATCH body with `status` is sent and the registration exists THE SYSTEM SHALL update the status, set `updated_at`, and respond 200.
2. IF the registration does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.
3. IF the status transition is not allowed THEN THE SYSTEM SHALL respond 422 `INVALID_STATUS_TRANSITION`.

---

### REQ-REG-E05 — Delete registration (DELETE /api/v1/registrations/{id})

**Acceptance criteria**
1. WHEN a valid id is provided and the registration exists THE SYSTEM SHALL delete it and respond 204.
2. IF the registration does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

---

### REQ-REG-E06 — Stats (GET /api/v1/registrations/stats?event_id=)

**Acceptance criteria**
1. WHEN a valid `event_id` is provided THE SYSTEM SHALL return `{event_id, capacity, confirmed, available}`.
2. IF the event does not exist in event-service THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.
3. IF event-service is unreachable THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-REG-E07 — PUT not allowed (PUT /api/v1/registrations/{id})

**Acceptance criteria**
1. WHEN PUT is called on a registration THE SYSTEM SHALL respond 405 `METHOD_NOT_ALLOWED`.

---

### REQ-REG-E08 — Health check (GET /health)

**Acceptance criteria**
1. WHEN GET /health is called THE SYSTEM SHALL respond 200 `{"status": "ok", "service": "registration-service"}`.

---

## Business rules

### REQ-REG-B01 — user_id must exist

**Acceptance criteria**
1. WHEN creating a registration THE SYSTEM SHALL call `GET /api/v1/users/{user_id}`.
2. IF user-service returns 404 THEN THE SYSTEM SHALL respond 422 `REFERENCE_NOT_FOUND`.
3. IF user-service is unreachable THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-REG-B02 — event_id must exist

**Acceptance criteria**
1. WHEN creating a registration THE SYSTEM SHALL call `GET /api/v1/events/{event_id}`.
2. IF event-service returns 404 THEN THE SYSTEM SHALL respond 422 `REFERENCE_NOT_FOUND`.
3. IF event-service is unreachable THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

---

### REQ-REG-B03 — Event must be published

**Acceptance criteria**
1. WHEN the event returned by event-service has `status ≠ published` THE SYSTEM SHALL respond 422 `EVENT_NOT_OPEN`.

---

### REQ-REG-B04 — No duplicate confirmed registrations

**User story:** As an organizer, I want to prevent the same user from registering twice for the same event.

**Acceptance criteria**
1. WHEN a user already has a `confirmed` registration for the same event THE SYSTEM SHALL respond 409 `ALREADY_REGISTERED`.
2. WHEN a user has only a `cancelled` registration for the same event THE SYSTEM SHALL allow a new registration.

---

### REQ-REG-B05 — Capacity enforcement

**User story:** As an organizer, I want registrations to stop when the event is full.

**Acceptance criteria**
1. WHEN the confirmed registrations for the event are fewer than `event.capacity` THE SYSTEM SHALL allow the registration.
2. IF confirmed registrations equal `event.capacity` THEN THE SYSTEM SHALL respond 409 `EVENT_FULL`.
3. WHEN a confirmed registration is cancelled THE SYSTEM SHALL free one seat (the available count increases by 1).

---

### REQ-REG-B06 — Amount from event price

**Acceptance criteria**
1. WHEN a registration is created THE SYSTEM SHALL set `amount = event.price` read from event-service.
2. The client MUST NOT be able to provide `amount`; it is always server-set.

---

### REQ-REG-B07 — Status transition

**Acceptance criteria**
1. WHEN PATCH is called THE SYSTEM SHALL only allow the transition `confirmed → cancelled`.
2. IF any other transition is attempted THE SYSTEM SHALL respond 422 `INVALID_STATUS_TRANSITION`.
3. A cancelled registration MUST NOT be re-confirmed.

---

### REQ-REG-B08 — Stats endpoint

**Acceptance criteria**
1. WHEN `GET /api/v1/registrations/stats?event_id=` is called THE SYSTEM SHALL fetch the event from event-service to get `capacity`.
2. THE SYSTEM SHALL count confirmed registrations for the event locally.
3. `available = capacity - confirmed`.
4. IF the event does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

---

### REQ-REG-B09 — Dependency unavailable

**Acceptance criteria**
1. WHEN user-service or event-service times out, refuses connection, or returns 5xx THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

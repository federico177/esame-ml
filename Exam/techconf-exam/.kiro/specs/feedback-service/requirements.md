# feedback-service — Requirements

## Overview

Ratings/feedback on events by registered users. Calls registration-service to verify a
confirmed registration exists and event-service to validate the event on summary.

---

## Endpoints

### REQ-FBK-E01 — Create feedback (POST /api/v1/feedbacks)
**User story:** As an attendee, I want to rate an event I attended.
**Acceptance criteria**
1. WHEN a valid body with `user_id`, `event_id`, `rating` is sent AND a confirmed registration exists THE SYSTEM SHALL create the feedback and respond 201 with a `Location` header.
2. IF the body is not valid JSON THEN THE SYSTEM SHALL respond 400.
3. IF a required field is missing or `rating` is outside 1-5 THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
4. IF a dependency is unreachable THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

### REQ-FBK-E02 — List feedbacks (GET /api/v1/feedbacks)
1. WHEN a GET request is sent THE SYSTEM SHALL return a paginated response.
2. WHEN `event_id` or `user_id` filters are provided THE SYSTEM SHALL filter accordingly.

### REQ-FBK-E03 — Get feedback by id (GET /api/v1/feedbacks/{id})
1. WHEN the feedback exists THE SYSTEM SHALL respond 200.
2. IF it does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

### REQ-FBK-E04 — Patch feedback (PATCH /api/v1/feedbacks/{id})
1. WHEN a valid PATCH body (`rating` and/or `comment`) is sent THE SYSTEM SHALL update the feedback and respond 200.
2. IF the feedback does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.
3. IF `rating` is outside 1-5 THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.

### REQ-FBK-E05 — Delete feedback (DELETE /api/v1/feedbacks/{id})
1. WHEN the feedback exists THE SYSTEM SHALL delete it and respond 204.
2. IF it does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

### REQ-FBK-E06 — Summary (GET /api/v1/feedbacks/summary?event_id=)
1. WHEN a valid `event_id` is provided THE SYSTEM SHALL return `{event_id, count, average_rating}`.
2. IF the event does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

### REQ-FBK-E07 — Health (GET /health)
1. WHEN GET /health is called THE SYSTEM SHALL respond 200 `{"status": "ok", "service": "feedback-service"}`.

---

## Business rules

### REQ-FBK-B01 — Must be registered (confirmed)
1. WHEN creating feedback THE SYSTEM SHALL call `GET /api/v1/registrations?user_id=&event_id=&status=confirmed` on registration-service.
2. IF no confirmed registration exists (or only cancelled) THEN THE SYSTEM SHALL respond 422 `NOT_REGISTERED`.
3. IF registration-service is unreachable THEN THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

### REQ-FBK-B02 — One feedback per (user, event)
1. WHEN a feedback already exists for `(user_id, event_id)` THE SYSTEM SHALL respond 409 `FEEDBACK_ALREADY_EXISTS`.

### REQ-FBK-B03 — Summary computation
1. THE SYSTEM SHALL verify the event exists via event-service; if not, respond 404 `NOT_FOUND`.
2. `count` = number of feedbacks for the event; `average_rating` = mean rating rounded to 2 decimals, or `null` when `count = 0`.

### REQ-FBK-B04 — Dependency unavailable
1. WHEN registration-service or event-service times out, refuses connection, or returns 5xx THE SYSTEM SHALL respond 503 `DEPENDENCY_UNAVAILABLE`.

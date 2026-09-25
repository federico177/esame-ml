# notification-service — Requirements

## Overview
Notifications to users, including broadcast to confirmed registrants of an event.
Calls user-service (validate user) and registration-service (broadcast recipients).

## Endpoints

### REQ-NTF-E01 — Create notification (POST /api/v1/notifications)
1. WHEN a valid body (`user_id`, `channel`, `subject`, `body`) is sent AND the user exists THE SYSTEM SHALL create the notification with `status=queued`, `sent_at=null`, respond 201 with Location header.
2. IF body is malformed JSON THEN respond 400.
3. IF a required field is missing/invalid THEN respond 422 VALIDATION_ERROR.
4. IF user-service unreachable THEN respond 503 DEPENDENCY_UNAVAILABLE.

### REQ-NTF-E02 — List (GET /api/v1/notifications)
1. Paginated; filters `user_id`, `status`.

### REQ-NTF-E03 — Get by id (GET /api/v1/notifications/{id})
1. 200 if exists, 404 NOT_FOUND otherwise.

### REQ-NTF-E04 — Patch status (PATCH /api/v1/notifications/{id})
1. Update status per allowed transitions; 404 if not found; 422 on invalid transition.

### REQ-NTF-E05 — Delete (DELETE /api/v1/notifications/{id})
1. 204 if deleted, 404 otherwise.

### REQ-NTF-E06 — Broadcast (POST /api/v1/notifications/broadcast)
1. Create one notification per confirmed registrant of the event; return `{event_id, created: n}`.

### REQ-NTF-E07 — Health (GET /health)
1. 200 `{"status":"ok","service":"notification-service"}`.

## Business rules

### REQ-NTF-B01 — user_id must exist
1. POST calls GET /api/v1/users/{user_id}; 404 -> 422 REFERENCE_NOT_FOUND; 5xx/timeout -> 503.

### REQ-NTF-B02 — Status transitions
1. Allowed: queued->sent, queued->failed. `sent` and `failed` are final states.
2. Invalid transition -> 422 INVALID_STATUS_TRANSITION.
3. WHEN status becomes `sent` THE SYSTEM SHALL set `sent_at` to the current UTC timestamp.

### REQ-NTF-B03 — Broadcast recipients
1. Broadcast calls registration-service for confirmed registrations of the event.
2. Creates one queued notification per confirmed registrant (cancelled excluded).
3. Returns `{event_id, created: n}`.

### REQ-NTF-B04 — Dependency unavailable
1. user-service or registration-service unreachable/5xx/timeout -> 503 DEPENDENCY_UNAVAILABLE.

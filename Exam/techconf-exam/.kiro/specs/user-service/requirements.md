# user-service — Requirements

## Overview

User registry for the TechConf platform. Manages attendees, speakers, and organizers.
Called by event-service, registration-service, and notification-service to validate user references.

---

## Endpoints

### REQ-USR-E01 — Create user (POST /api/v1/users)

**User story:** As a platform client, I want to register a new user so that they can participate in events.

**Acceptance criteria**
1. WHEN a valid POST body is sent with `first_name`, `last_name`, and `email` THE SYSTEM SHALL create the user, generate a UUID v4 `id`, set `created_at` and `updated_at` to the current UTC timestamp, default `role` to `attendee`, and respond 201 with the user object and a `Location` header.
2. IF the request body is not valid JSON THEN THE SYSTEM SHALL respond 400.
3. IF any required field (`first_name`, `last_name`, `email`) is missing or empty THEN THE SYSTEM SHALL respond 422 with code `VALIDATION_ERROR`.
4. WHEN `role` is provided it MUST be one of `attendee`, `speaker`, `organizer`; otherwise THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
5. IF `company` exceeds 100 characters THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.

---

### REQ-USR-E02 — List users (GET /api/v1/users)

**User story:** As a platform client, I want to list users with optional filters so that I can find specific users.

**Acceptance criteria**
1. WHEN a GET request is sent THE SYSTEM SHALL return a paginated response `{items, page, page_size, total}` with default `page=1`, `page_size=20`.
2. WHEN `role` query param is provided THE SYSTEM SHALL return only users with that role.
3. WHEN `email` query param is provided THE SYSTEM SHALL return only users whose email matches (case-insensitive).
4. IF `page` or `page_size` are not positive integers THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
5. `page_size` MUST NOT exceed 100; if it does THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.

---

### REQ-USR-E03 — Get user by id (GET /api/v1/users/{id})

**User story:** As a platform client, I want to retrieve a user by their ID so that I can view their details.

**Acceptance criteria**
1. WHEN a valid UUID is provided and the user exists THE SYSTEM SHALL respond 200 with the full user object.
2. IF the user does not exist THEN THE SYSTEM SHALL respond 404 with code `NOT_FOUND`.

---

### REQ-USR-E04 — Replace user (PUT /api/v1/users/{id})

**User story:** As a platform client, I want to fully replace a user's data so that I can correct all fields at once.

**Acceptance criteria**
1. WHEN a valid PUT body is sent and the user exists THE SYSTEM SHALL update all fields, set `updated_at` to the current UTC timestamp, and respond 200 with the updated user.
2. IF the user does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.
3. IF validation fails (same rules as POST) THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
4. IF the new email conflicts with another user THEN THE SYSTEM SHALL respond 409 `EMAIL_ALREADY_EXISTS`.

---

### REQ-USR-E05 — Partial update (PATCH /api/v1/users/{id})

**User story:** As a platform client, I want to update individual fields of a user without replacing them all.

**Acceptance criteria**
1. WHEN a PATCH body with one or more valid fields is sent and the user exists THE SYSTEM SHALL update only the provided fields, set `updated_at`, and respond 200.
2. IF the user does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.
3. IF a provided field fails validation THEN THE SYSTEM SHALL respond 422 `VALIDATION_ERROR`.
4. IF the new email conflicts with another user THEN THE SYSTEM SHALL respond 409 `EMAIL_ALREADY_EXISTS`.

---

### REQ-USR-E06 — Delete user (DELETE /api/v1/users/{id})

**User story:** As a platform client, I want to delete a user from the registry.

**Acceptance criteria**
1. WHEN a valid id is provided and the user exists THE SYSTEM SHALL delete the user and respond 204 with no body.
2. IF the user does not exist THEN THE SYSTEM SHALL respond 404 `NOT_FOUND`.

---

### REQ-USR-E07 — Health check (GET /health)

**Acceptance criteria**
1. WHEN GET /health is called THE SYSTEM SHALL always respond 200 with `{"status": "ok", "service": "user-service"}`.

---

## Business rules

### REQ-USR-B01 — Email uniqueness

**User story:** As an organizer, I want email addresses to be unique so that each user has a distinct identity.

**Acceptance criteria**
1. WHEN a user is created or updated with an email that already exists (case-insensitive comparison) THE SYSTEM SHALL respond 409 with code `EMAIL_ALREADY_EXISTS`.
2. WHEN checking uniqueness THE SYSTEM SHALL compare emails case-insensitively (e.g. `User@Example.com` conflicts with `user@example.com`).

---

### REQ-USR-B02 — Email normalisation

**Acceptance criteria**
1. WHEN a user is created or updated THE SYSTEM SHALL store the email in lowercase regardless of the case provided by the client.

---

### REQ-USR-B03 — List filters

**Acceptance criteria**
1. WHEN `role` filter is applied THE SYSTEM SHALL return only users whose `role` matches exactly.
2. WHEN `email` filter is applied THE SYSTEM SHALL return only users whose stored (lowercase) email matches the provided value (case-insensitive).
3. Filters MAY be combined; when combined THE SYSTEM SHALL apply both (AND logic).

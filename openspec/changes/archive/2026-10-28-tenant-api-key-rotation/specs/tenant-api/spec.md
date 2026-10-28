# Spec Delta

## MODIFIED Requirements

### Requirement: Update tenant detail

The service SHALL expose `PATCH /admin/tenants/{id}` for internal operators to update tenant information.

- The request body accepts `{"name": <string>}` and optional rotation settings
  `{"auto_rotate": <boolean>, "rotate_days": <integer | null>}` where `null`
  means "forever" (no expiry).
- Updating an archived tenant's name SHALL be permitted.
- The response MUST return the updated tenant object `{"id", "name",
  "created_at", "archived_at", "auto_rotate", "rotate_days",
  "api_key_expires_at"}`.

#### Scenario: Successfully update tenant name

- **WHEN** an internal operator sends `PATCH /admin/tenants/{tenant_id}` with `{"name": "New Acme Name"}`
- **THEN** the tenant name is updated in SQLite and returned in the `200` response

#### Scenario: Update rotation settings

- **WHEN** an internal operator sends `PATCH /admin/tenants/{tenant_id}` with `{"auto_rotate": false, "rotate_days": 30}`
- **THEN** the settings are stored and returned in the `200` response

#### Scenario: Forever rotation

- **WHEN** an internal operator sends `PATCH /admin/tenants/{tenant_id}` with `{"rotate_days": null}`
- **THEN** `rotate_days` and `api_key_expires_at` are stored as `null` and
  the key does not expire

#### Scenario: Update non-existent tenant

- **WHEN** an internal operator sends `PATCH /admin/tenants/nonexistent-id` with `{"name": "Name"}`
- **THEN** the service responds `404` with message `Tenant not found`

## ADDED Requirements

### Requirement: Retrieve tenant API key

The service SHALL expose `GET /admin/tenants/{id}/api-key` for internal
operators to retrieve the tenant's current API key for copying.

- The response MUST be `{"api_key": <string>}`.
- The endpoint MUST require admin authentication.

#### Scenario: Retrieve key

- **WHEN** an internal operator requests `/admin/tenants/{id}/api-key`
- **THEN** the response is `200` with the tenant's `api_key`

### Requirement: Regenerate tenant API key

The service SHALL expose `POST /admin/tenants/{id}/regenerate-key` for
internal operators to manually rotate the API key.

- A new key MUST be generated and stored.
- `api_key_created_at` MUST be reset; `api_key_expires_at` MUST be reset based
  on `rotate_days`, or set to `null` when `rotate_days` is `null` (forever).
- The response MUST include the new `api_key` (shown once).

#### Scenario: Manual regeneration

- **WHEN** an internal operator posts to `/admin/tenants/{id}/regenerate-key`
- **THEN** a new `api_key` is returned and the old key stops working

### Requirement: API key expiry enforcement

Tenant authentication SHALL reject expired API keys.

- If a key is expired and auto-rotation is enabled, the service SHALL
  generate a new key, store it, and reject the request with `401` and a
  message indicating rotation.
- If a key is expired and auto-rotation is disabled, the service SHALL reject
  with `401` and a message indicating expiry.
- Default expiry is 90 days from key creation; a `null` `rotate_days` means
  the key never expires.

#### Scenario: Expired key with auto-rotation

- **WHEN** an expired key with auto-rotation enabled is used
- **THEN** the service responds `401` and a new key is stored

#### Scenario: Expired key without auto-rotation

- **WHEN** an expired key with auto-rotation disabled is used
- **THEN** the service responds `401` with an expiry message
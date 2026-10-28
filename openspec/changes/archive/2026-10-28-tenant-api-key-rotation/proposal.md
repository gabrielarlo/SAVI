# Proposal

## Why

Tenant API keys are shown only once at creation and cannot be rotated or
copied later. Operators need to copy, manually regenerate, and optionally
auto-rotate keys (default 90 days) for security hygiene.

## What Changes

- Persist API key creation/expiry and auto-rotation settings per tenant.
- Add endpoints to copy (retrieve) and regenerate a tenant's API key.
- Allow updating auto-rotation settings (enabled flag and interval days).
- Enforce expiry on tenant authentication: expired keys are rejected; when
  auto-rotation is enabled the key is rotated automatically on expiry.
- Update the tenant management UI with copy, regenerate, and auto-rotation
  controls.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `tenant-api`: API key retrieval, regeneration, rotation settings, and
  expiry enforcement.
- `admin-ui`: Tenant management UI supports copy, regenerate, and
  auto-rotation controls.

## Impact

- `migrations/` (tenant columns), `app/routes.py`, `app/auth.py`,
  `app/db` migration.
- `ui/src/pages/.../tenants.html`, `ui/src/js/tenants.js`.
- Tests for key rotation and expiry.
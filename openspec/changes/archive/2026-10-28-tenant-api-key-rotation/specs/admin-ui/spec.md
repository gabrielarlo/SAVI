# Spec Delta

## ADDED Requirements

### Requirement: Tenant API key copy and regeneration UI

The tenant management UI SHALL let operators copy and regenerate a tenant's
API key.

- Each tenant row MUST provide a "Copy" action that fetches and copies the
  current API key to the clipboard.
- Each tenant row MUST provide a "Regenerate" action requiring confirmation
  before calling `POST /admin/tenants/{id}/regenerate-key`.
- The regenerated key MUST be shown once in a modal with a copy button.

#### Scenario: Copy key

- **WHEN** an operator clicks "Copy" for a tenant
- **THEN** the current API key is fetched and copied to the clipboard

#### Scenario: Regenerate key

- **WHEN** an operator confirms regeneration
- **THEN** a new key is shown once in a modal with a copy button

### Requirement: Tenant API key auto-rotation settings UI

The tenant management UI SHALL allow configuring auto-rotation.

- An edit form MUST allow toggling auto-rotation and selecting the rotation
  interval from a dropdown of predefined common options (30, 60, 90, 180, 365
  days, and "Forever" which sets `rotate_days` to `null`). Default is 90 days.
- The tenant table MUST show expiry status (active/expired).

#### Scenario: Configure auto-rotation

- **WHEN** an operator sets auto-rotation to enabled with 30 days
- **THEN** `PATCH /admin/tenants/{id}` is called with those settings
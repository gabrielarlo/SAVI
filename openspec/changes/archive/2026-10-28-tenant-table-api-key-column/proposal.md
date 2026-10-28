# Proposal

## Why

Operators need to see and copy a tenant's API key directly in the tenants
table without opening a modal, improving day-to-day management.

## What Changes

- Add an "API key" column to the tenants table showing a masked value with a
  copy action.
- Reuse the existing copy-key flow.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `admin-ui`: tenants table includes an API key column.

## Impact

- `ui/src/pages/(admin-layout)/(main)/tenants.html`
- `ui/src/js/tenants.js`
- `ui/build/` regenerated.
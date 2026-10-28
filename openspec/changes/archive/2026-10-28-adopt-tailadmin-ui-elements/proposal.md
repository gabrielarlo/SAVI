# Proposal

## Why

The console already uses TailAdmin free, but several pages still use ad-hoc
markup instead of the template's documented UI element patterns (buttons,
badges, form controls, modals, alerts, tables). Aligning them improves
consistency and maintainability.

## What Changes

- Audit console pages and replace ad-hoc controls with TailAdmin UI element
  patterns and classes.
- Standardize button, badge, input, modal, and alert styling across documents,
  tenants, users, and dashboard pages.
- No functional or API changes; styling/consistency only.

## Capabilities

### New Capabilities

(none - styling only)

### Modified Capabilities

(none - styling only)

## Impact

- `ui/src/pages/...` HTML templates, `ui/src/js/*.js` for class usage.
- `ui/build/` regenerated via Docker build.
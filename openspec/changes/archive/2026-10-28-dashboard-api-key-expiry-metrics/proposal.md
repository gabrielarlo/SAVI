# Proposal

## Why

Operators need visibility into tenant API keys that are about to rotate or
have expired, with urgency color-coding, so they can act before clients break.

## What Changes

- Add API key rotation urgency metrics to `GET /admin/stats`: counts of keys
  in blue (healthy), orange (expiring soon), and red (expired) states.
- Update the dashboard to render these metrics as color-coded cards (blue,
  orange, red) and refresh them with the existing live polling.

## Capabilities

### New Capabilities

- `api-key-rotation-metrics`: Counts of tenant API keys by rotation urgency
  (blue/orange/red) exposed via `GET /admin/stats`.

### Modified Capabilities

- `admin-ui`: dashboard renders color-coded API key rotation metrics.

## Impact

- `app/routes.py` (stats extension), `ui/src/js/dashboard.js`,
  `ui/src/pages/.../dashboard.html`.
- Tests for new metrics.
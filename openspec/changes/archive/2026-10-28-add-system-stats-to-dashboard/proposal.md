# Proposal

## Why

The dashboard page at `/console` is currently a placeholder, so operators land
on an empty screen with no overview of the system. Surfacing basic counts
(tenants, documents, chunks, users) gives an at-a-glance health snapshot and
makes the dashboard useful.

## What Changes

- Add a new admin endpoint `GET /admin/stats` returning aggregate counts of
  tenants, documents, chunks, and users (total/active/archived where relevant).
- Replace the dashboard placeholder with a stats view that fetches
  `/admin/stats` and renders one card per metric.
- Keep all rendering text-based (no HTML injection) and consistent with the
  existing admin console styling.

## Capabilities

### New Capabilities

- `system-stats`: Aggregate system counts exposed to internal operators via
  `GET /admin/stats`.

### Modified Capabilities

- `admin-ui`: Dashboard page displays system stats cards instead of a
  placeholder.

## Impact

- `app/routes.py` (new `/admin/stats` handler), `app/services.py` or db queries.
- `ui/src/pages/(admin-layout)/(main)/dashboard.html` and a new/updated JS
  module for dashboard data loading.
- `ui/build/` regenerated via Docker build.
- Tests for the new endpoint and dashboard route.
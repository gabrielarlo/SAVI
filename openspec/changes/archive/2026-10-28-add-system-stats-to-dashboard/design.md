# Design

## Context

Dashboard is served at `/console/` from `ui/build/dashboard.html` and currently
renders a placeholder. Admin API already exposes list endpoints for tenants,
documents, and users; counts can be derived with SQL `COUNT(*)`.

## Goals / Non-Goals

**Goals:**
- One admin endpoint returning the four core counts.
- Dashboard renders a card per count using existing TailAdmin styling.

**Non-Goals:**
- No charts, trends, or time-series.
- No caching; counts are cheap SQL aggregates.

## Decisions

- **Endpoint shape**: `GET /admin/stats` returns a flat JSON object
  `{tenants, documents, chunks, users}`. Flat keeps the UI trivial and matches
  the existing simple response shapes (e.g. list endpoints return arrays).
  Alternative (nested objects per entity) rejected as unnecessary for four
  scalars.
- **Auth**: reuse `require_admin` dependency, consistent with other admin
  routes; tenant keys get 401.
- **UI data flow**: dashboard page gets a small inline script (in a new
  `dashboard.js` module registered in `index.js`) that calls `request("/admin/stats")`
  and builds cards with `textContent` (no innerHTML), mirroring documents.js.
- **Counting archived records**: `tenants` and `users` counts include archived
  rows (total records), keeping the metric a simple system total.

## Risks / Trade-offs

- [Counts drift under concurrent writes] → Acceptable; reads are best-effort
  snapshots, no locking needed.
- [UI build must be regenerated] → Rebuild via Docker per project guidelines.

## Migration Plan

No schema changes. Deploy by rebuilding and restarting the service.

## Open Questions

None.
# Design

## Context

Stats endpoint already returns tenant counts. Tenant API keys now have
expiry metadata (api_key_expires_at). Dashboard polls stats every 4s.

## Goals / Non-Goals

**Goals:**
- Add urgency counts to `/admin/stats`.
- Render color-coded cards on dashboard.

**Non-Goals:**
- No per-tenant detail table; counts only.

## Decisions

- **Thresholds**: red = within 10 days; orange = within 30 days (but >10);
  blue = more than 30 days (including null/forever).
- **Aggregation**: SQL counts grouped by urgency; archived tenants excluded.
- **UI**: reuse existing card component with color classes per metric key.

## Risks / Trade-offs

- [Threshold choice] → 7 days fixed; acceptable for v1.

## Migration Plan

No schema changes. Rebuild UI and restart.
# Design

## Context

Builds on the completed stats change: `/admin/stats` already returns core
counts. Chat endpoints exist for admin and tenant. Dashboard already renders
stat cards from `dashboard.js`.

## Goals / Non-Goals

**Goals:**
- Persist a lightweight inquiry row per chat request.
- Extend stats with inquiry and active/archived counts.
- Poll stats every 4 seconds with visibility handling and a "Live" indicator.
- Present a polished, responsive dashboard layout consistent with TailAdmin.

**Non-Goals:**
- No charts or time-series beyond 7-day per-day counts.
- No WebSockets; polling is sufficient.
- No new CSS framework or charting library.

## Decisions

- **Inquiry table**: new `inquiries` table with `id`, `tenant_id` (nullable),
  `created_at`. Migration added; idempotent.
- **Instrumentation**: insert inquiry row inside `admin_chat` and `tenant_chat`
  after generating the answer, before returning. Wrap in try/except so a
  tracking failure never breaks chat.
- **Per-day aggregation**: SQL `GROUP BY date(created_at)` for last 7 days,
  zero-filled in Python.
- **Polling**: `setInterval` 4000ms in `dashboard.js`, cleared on `visibilitychange`
  when hidden; resume on visible. "Live" badge is a pulsing SVG circle via CSS
  animation.
- **Additional counts**: derive active/archived from `tenants`/`users` with
  `archived_at IS NULL`.
- **Visual design**: responsive 1/2/4-column grid, TailAdmin card styling,
  consistent spacing, subtle hover elevation, loading placeholders while
  fetching, no new CSS dependencies, no charts.

## Risks / Trade-offs

- [Polling adds load] → 4s interval is modest; counts are indexed aggregates.
- [Inquiry insert failure] → caught and logged; chat response unaffected.
- [Timezone] → use UTC date for `created_at` and per-day grouping.

## Migration Plan

Add migration file; apply on startup via existing migrate(). Rebuild UI and
restart service.
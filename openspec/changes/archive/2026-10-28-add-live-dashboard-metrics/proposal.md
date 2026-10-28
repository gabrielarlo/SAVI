# Proposal

## Why

Operators want the dashboard to reflect activity as it happens: chat inquiries
per day and a few more useful counts, refreshed automatically, with a clear
"live" indicator so it's obvious the numbers are current.

## What Changes

- Record each chat inquiry (admin and tenant) with a timestamp so per-day
  counts can be derived.
- Extend `GET /admin/stats` with inquiry metrics: total inquiries and inquiries
  in the last 7 days (per day).
- Add a few additional helpful counts (e.g. active tenants, archived tenants,
  active users).
- Make the dashboard poll `/admin/stats` every 3-5 seconds and render a small
  "Live" badge (text + pulsing SVG dot) while polling is active.
- Keep rendering text-based (no HTML injection).

## Capabilities

### New Capabilities

- `inquiry-tracking`: Persist chat inquiries and expose per-day and total
  inquiry counts to internal operators.

### Modified Capabilities

- `admin-ui`: Dashboard polls stats on a short interval and shows a live
  indicator; dashboard displays inquiry metrics.

## Impact

- `migrations/` (new `inquiries` table), `app/routes.py` (instrument chat
  endpoints, extend stats), `app/services.py` maybe.
- `ui/src/pages/(admin-layout)/(main)/dashboard.html`, `ui/src/js/dashboard.js`.
- Tests for inquiry tracking and live stats.
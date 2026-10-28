# Tasks

## 1. Backend (inquiry tracking)

- [x] 1.1 Add migration for `inquiries` table and verify migrate creates it
- [x] 1.2 Instrument `admin_chat` and `tenant_chat` to record inquiry rows
  and verify chat still returns 200
- [x] 1.3 Extend `GET /admin/stats` with inquiries, inquiries_per_day,
  tenants_active/archived, users_active/archived and verify response shape

## 2. UI (live dashboard)

- [x] 2.1 Update dashboard.html to include "Live" badge with animated SVG dot
  and verify build succeeds
- [x] 2.2 Update dashboard.js to poll every 4s, pause on hidden, resume on
  visible, and render inquiry cards; verify no console errors
- [x] 2.3 Rebuild UI bundle via Docker and verify stats-grid and live badge
  present

## 3. Verification

- [x] 3.1 Run full test suite in Docker and verify all tests pass
- [x] 3.2 Rebuild and restart service; verify /admin/stats and /console work

## 4. Visual polish (from revised design)

- [x] 4.1 Apply responsive grid, loading placeholders, and card styling in
  dashboard.html/js and verify build succeeds
- [x] 4.2 Rebuild UI bundle via Docker and verify placeholders present
- [x] 4.3 Rebuild and restart service; verify polished layout renders
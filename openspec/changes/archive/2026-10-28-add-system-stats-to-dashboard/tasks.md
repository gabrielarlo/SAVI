# Tasks

## 1. Backend

- [x] 1.1 Add `GET /admin/stats` handler in `app/routes.py` returning
  `{tenants, documents, chunks, users}` counts and verify with a pytest
  request as admin
- [x] 1.2 Ensure non-admin (tenant API key) gets 401 and verify with
  `tests/test_api.py`-style assertion

## 2. UI

- [x] 2.1 Replace the dashboard placeholder with a stats grid in
  `ui/src/pages/(admin-layout)/(main)/dashboard.html` and verify the page
  builds
- [x] 2.2 Add `ui/src/js/dashboard.js` that fetches `/admin/stats` and
  renders cards with `textContent`, register it in `index.js`, and verify
  no console errors
- [x] 2.3 Rebuild the UI bundle via Docker and verify `ui/build/dashboard.html`
  contains the stats markup

## 3. Verification

- [x] 3.1 Run the full test suite in Docker and verify all tests pass
- [x] 3.2 Rebuild and restart the service with `docker compose up --build -d`
  and verify `/console` renders stats
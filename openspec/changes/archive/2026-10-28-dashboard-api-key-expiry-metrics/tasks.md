# Tasks

## 1. Backend

- [x] 1.1 Extend `GET /admin/stats` with api_keys_blue/orange/red counts and
  verify response shape

## 2. UI

- [x] 2.1 Add color-coded cards to dashboard for API key urgency metrics and
  verify build
- [x] 2.2 Rebuild UI bundle via Docker and verify output

## 3. Verification

- [x] 3.1 Run full test suite in Docker and verify all tests pass
- [x] 3.2 Rebuild and restart service; verify dashboard metrics work

## 4. Threshold adjustment

- [x] 4.1 Update stats urgency thresholds (red <=10, orange <=30, blue >30)
  and verify
- [x] 4.2 Rebuild and restart service; verify metrics
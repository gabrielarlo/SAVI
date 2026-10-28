# Tasks

## 1. Backend

- [x] 1.1 Add migration for tenant API key rotation columns and backfill;
  verify migrate applies
- [x] 1.2 Add `GET /admin/tenants/{id}/api-key` and
  `POST /admin/tenants/{id}/regenerate-key` endpoints; verify responses
- [x] 1.3 Extend `PATCH /admin/tenants/{id}` with auto_rotate and rotate_days;
  verify validation and response
- [x] 1.4 Enforce expiry in `get_role` with auto-rotation handling; verify
  expired keys rejected

## 2. UI

- [x] 2.1 Add copy/regenerate actions and auto-rotation settings to tenants
  page; verify build
- [x] 2.2 Rebuild UI bundle via Docker and verify output

## 3. Verification

- [x] 3.1 Run full test suite in Docker and verify all tests pass
- [x] 3.2 Rebuild and restart service; verify tenant key flows work

## 4. Forever option (from revised design)

- [x] 4.1 Support `rotate_days = null` in backend (validation, regeneration,
  expiry check) and verify
- [x] 4.2 Update tenant UI dropdown with predefined options including
  "Forever" and verify build
- [x] 4.3 Rebuild and restart service; verify forever keys do not expire
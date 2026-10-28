# Tasks

## 1. Schema & migrations
- [x] 1.1 Add `migrations/20261028000000_users.sql` creating `users` (id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('administrator','account_manager')), archived_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP); verify migration applies via existing migration runner
- [x] 1.2 Add tests for users table creation and uniqueness

## 2. Config & seeding
- [x] 2.1 Add `DEFAULT_ADMIN_USERNAME` and `DEFAULT_ADMIN_PASSWORD` to `Config` (env-driven, same pattern as existing vars) and `.env.example`; seed an administrator user on startup (lifespan, after migrate) only if both are set and the username does not already exist; idempotent; skip seeding with a warning if the password is shorter than 8 characters
- [x] 2.2 Add tests for seeding: creates user when env set, idempotent on repeat, no seed when unset, short password skipped with warning

## 3. Auth
- [x] 3.1 Retain `X-Admin-Secret` support in `app/auth.py` (must not be removed). Add a login endpoint that verifies username + password (salted PBKDF2 hash via `hmac.compare_digest`) and establishes the console session; reject unknown username, wrong password, and archived users with the same generic `401` message
- [x] 3.2 Add tests verifying `X-Admin-Secret` works on `/admin/*` after user auth changes, plus login tests (valid pair, wrong password generic 401, archived user rejected)

## 4. User management API
- [x] 4.1 Add `/admin/users` endpoints: list/create/update/archive (no delete). Roles Administrator/Account Manager (Tenant Manager). Archive-only. Create and update accept a password, enforce the ≥ 8 character minimum, store a salted hash, and never return the password or hash in any response
- [x] 4.2 Add tests for user CRUD/archive, prohibition of delete, the password policy (7-char rejected / 8-char accepted), and hash-at-rest (no plaintext column value)

## 5. Console UI
- [x] 5.1 Update sign-in to support username + password auth (username and password fields, no email). Preserve API secret usage for programmatic access
- [x] 5.2 Add `ui/src/pages/(admin-layout)/(main)/users.html` and `ui/src/js/users.js`, wire into `ui/src/js/index.js`, add sidebar link to Users, add `GET /console/users` route in `app/main.py`; follow `ui/CONTRIBUTING-UI.md`
- [x] 5.3 Update `AGENTS.md` §6 to include Users page
- [x] 5.4 Fix sign-in UX: submit on Enter from either field; fix toggle icon placement so it renders inside the password input (relative wrapper + absolute button + input right padding)
- [x] 5.5 Extract a reusable password-input pattern (shared `wirePasswordToggle` helper + documented markup) and reuse it in sign-in and every user-management password field instead of duplicating logic
- [x] 5.6 Update guidelines (`ui/CONTRIBUTING-UI.md`, `AGENTS.md` §6) to document the reusable password input, in-input toggle, and Enter-to-submit behavior
- [x] 5.7 Add `/console` dashboard page (empty/placeholder), serve via `GET /console` and `GET /console/` inside UI_DIR guard; make `/` redirect to `/console`
- [x] 5.8 Update login flow to redirect to `/console` after success; guard `/console/signin` so authenticated sessions redirect to `/console` (no signin form shown)
- [x] 5.9 Move sign-in route to `/auth/signin` (FastAPI `GET /auth/signin`); protect all `/console/*` routes with auth (unauthenticated → redirect `/auth/signin`); update JS guard redirects and login redirect accordingly

## 6. Verify
- [x] 6.1 Run full suite with `docker run --rm -v "$PWD:/src" -w /src python:3.12-slim sh -c 'pip install -q -r requirements.txt && pytest -q'`

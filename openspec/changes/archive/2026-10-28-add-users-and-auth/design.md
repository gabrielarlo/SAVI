# Design

## Context

See `proposal.md`. Current auth: `get_role` accepts `X-Admin-Secret` (→ `AdminRole`) or `X-API-Key` for tenants (→ `TenantRole`, archived blocked). Console uses `sessionStorage` admin secret sent as `X-Admin-Secret`. No user table exists.

## Goals / Non-Goals

**Goals:**
- Add `users` table with username identities, salted password hashes, and roles `administrator`, `account_manager`.
- Console username/password sign-in (no email anywhere); keep `X-Admin-Secret` working for all `/admin/*` API calls unchanged.
- Minimal password policy: at least 8 characters, enforced on create and password change.
- User management page at `/console/users`, archive-only, no deletion; roles labeled "Administrator" / "Account Manager (Tenant Manager)" in UI.
- Follow `ui/CONTRIBUTING-UI.md` and existing patterns.

**Non-Goals:**
- Email-based login or email fields of any kind.
- Complex password rules (composition, rotation, lockout) beyond the 8-character minimum.
- Changing tenant API key auth behavior except to preserve it.
- Deleting users.

## Decisions

**Auth layering:** Keep header-based auth in `app/auth.py` intact for `X-Admin-Secret` and `X-API-Key`. For console UI, add a login endpoint that verifies username + password and establishes a session; the UI will call it, but **all `/admin/*` routes must continue to accept `X-Admin-Secret`** — this is a hard requirement (no removal). Treat console user sessions and the secret header as independent auth paths that both can grant admin access where appropriate.

**Schema:** `users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('administrator','account_manager')), archived_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)`. Username only, no email. Archive sets `archived_at` (timestamp) like tenants; archived users cannot sign in.

**Password hashing (stdlib, no new dependency):** `hashlib.pbkdf2_hmac("sha256", password, per-user random salt)` with the salt stored alongside the hash; verification uses `hmac.compare_digest` for constant-time comparison. The iteration count is a named module constant so tests can lower it instead of paying full cost per call. Alternatives considered: bcrypt/argon2 (new dependency — rejected), plaintext or reversible storage (never).

**Login verification:** one shared lookup `SELECT ... FROM users WHERE username = ?` that fetches `password_hash, role, archived_at`; unknown username and wrong password return the same single `401` message ("Invalid username or password") so responses do not reveal which part failed. Archived users get the same generic rejection at login.

**UI:** Add `/console/users` served from `UI_DIR`, sidebar item, new page + JS module wired in `index.js`. The sign-in page moves to `/auth/signin` (no email input); sign-in calls the login endpoint, and the API secret usage for programmatic access is unchanged. The sign-in form submits on Enter from either field (native submit + explicit Enter handling). The password field with visibility toggle is a shared partial (webpack `<include>`) plus one shared JS toggle helper; the toggle button is absolutely positioned inside a relative wrapper with matching input right padding so the icon never renders detached outside the field. Any password field (sign-in, user create/update) reuses this partial instead of duplicating markup. Add a dashboard page at `/console` (empty/placeholder for now); successful login redirects to `/console`. Authenticated sessions (valid session token or admin secret) are redirected away from `/auth/signin` to `/console`. All `/console/*` routes are auth-protected: unauthenticated requests redirect to `/auth/signin`.

## Risks / Trade-offs

- [API compatibility] → Must verify every existing `/admin/*` test still passes with `X-Admin-Secret` unchanged. Add explicit tests for retention.
- [Credential leaks] → Salted hashes only, never logged, never returned by user endpoints; generic login error avoids username enumeration.
- [Auth complexity] → Keep changes additive; prefer extending `get_role` minimally or adding separate dependencies so existing behavior is not regressed.
- [UI drift] → Follow `ui/CONTRIBUTING-UI.md` strictly.

## Migration Plan

Additive migration only. Rollback not required; archive-only model prevents destructive deletes.

## Seeding

On startup (lifespan), after `migrate()`, if both `DEFAULT_ADMIN_USERNAME` and `DEFAULT_ADMIN_PASSWORD` are set, insert an `administrator` user with that username and a salted hash of the password **only if no user with that username exists**. Idempotent; an invalid (short) seed password logs a warning and skips seeding rather than failing startup.


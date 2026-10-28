# Proposal

## Why

The console currently authenticates operators with a shared `ADMIN_SECRET` and
manages tenants separately. To support user-based access control in the UI
(and to lay groundwork for role-scoped administration), we need a dedicated
user account system with two roles ("Administrator" and "Account Manager" /
"Tenant Manager") and a username + password login — never email/password. The
existing API-key-based admin access (`X-Admin-Secret`) must remain for direct
API/programmatic use.

## What Changes

- Add a `users` table (username only, no email) with role enum
  (`administrator`, `account_manager`), a salted password hash column, created/
  active metadata, and migration to apply it.
- Seed a default administrator from environment variables on startup (idempotent:
  create only if the username does not already exist), so a fresh deployment
  ships with a usable admin account. The seeded password is subject to the same
  minimal policy.
- Add a user management page in the console (`/console/users`) following
  `ui/CONTRIBUTING-UI.md` (TailAdmin free only) to create/list/update/archive
  users; no user deletion.
- Add username + password authentication for the console (no email anywhere)
  with a minimal password policy: **passwords MUST be at least 8 characters**
  on user creation and on any password change. Passwords are stored salted and
  hashed, never in plaintext, and never returned by any API response.
  Sign-in submits on Enter and every password field reuses one shared
  password-input component with an in-input visibility toggle.
- Define roles: `Administrator` and `Account Manager` (this project calls the
  second `Tenant Manager` in description but the system uses canonical role names;
  document both labels in the UI).
- Update auth in `app/auth.py` to support the new UI auth model while
  **retaining** `ADMIN_SECRET` for API interactions (all `/admin/*` routes must
  still accept `X-Admin-Secret` where they do now; no removal of that path).
- Serve `/console/users` like `/console/tenants` inside the `UI_DIR` guard.

## Capabilities

### New Capabilities

- `user-auth`: Username/password console authentication (no email), roles
  (Administrator / Account Manager-Tenant Manager), minimal password policy
  (≥ 8 characters), salted-hashed credential storage, session handling in the
  browser consistent with existing patterns; `X-Admin-Secret` remains valid for
  API interactions.
- `user-management`: Console page and admin API for creating/listing/updating
  users with the above roles, archive-only (no deletion), following UI
  conventions.

### Modified Capabilities

- `admin-ui`: Add `/console/users` route, Users navigation item, add `/console`
  dashboard route, and move sign-in to `/auth/signin` supporting username/password
  auth (no email) with Enter-to-submit and a reusable in-input password
  visibility toggle. Successful login redirects to `/console`; authenticated
  users are redirected away from `/auth/signin`. All `/console/*` routes are
  auth-protected (unauthenticated → `/auth/signin`). Still honors the
  "retained admin_secret for api interaction" requirement.
- `tenant-api`: Only if strictly necessary to avoid breaking existing admin auth;
  preferably no change — ensure role separation doesn't require removing
  `X-Admin-Secret` support.

## Impact

- **Database**: New migration adding `users` table (includes `password_hash`).
- **Backend**: `app/auth.py` (login verification), `app/routes.py` (user
  CRUD/archiving, login/session endpoints as needed), `app/config.py` (add
  `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD`), `app/main.py` (seed on
  startup), `app/db.py` unchanged for migration runner.
- **Frontend**: New page `ui/src/pages/(admin-layout)/(main)/users.html`, JS
  `ui/src/js/users.js`, sidebar link, sign-in page changes (username + password
  fields, no email, Enter-to-submit, in-input visibility toggle via a reusable
  password-input partial), webpack entry update.
- **Docs**: `AGENTS.md` §6 updated to include Users page.
- **Tests**: New tests for user auth/roles, password policy, hash handling, and
  API secret retention.

# Tasks

## 1. Schema & migrations

- [x] 1.1 Rewrite `app/db.py:migrate` to apply every `migrations/*.sql` in filename order exactly once, tracked in a `schema_migrations` table (drop the hardcoded `MIGRATION_PATH`), and add `migrations/20261027000000_tenant_archiving.sql` with `ALTER TABLE tenants ADD COLUMN archived_at DATETIME;`; verify a new test in `tests/test_db.py` proves migrating the same database twice succeeds and leaves `archived_at` present

## 2. Tenant API

- [x] 2.1 Change the API-key lookup in `app/auth.py:get_role` to also select `archived_at` and reject a key whose tenant is archived with `403` and message `Tenant account is archived`; verify a test archives a tenant, calls `/api/v1/chat` with its key, and gets `403`, while an active tenant's key still returns `200`
- [x] 2.2 Extend `GET /admin/tenants` in `app/routes.py` with an `include_archived` bool query parameter (default false), returning `{id, name, created_at, archived_at}` ordered by `created_at` ascending and never `api_key`; verify tests cover default active-only, `include_archived=true` including archived, and the no-`api_key` rule
- [x] 2.3 Add `GET /admin/tenants/{id}` returning `{id, name, created_at, archived_at}` and `404` `Tenant not found` for unknown ids, sharing a `_tenant_or_404` helper; verify tests cover the 200 shape (no `api_key`) and 404
- [x] 2.4 Add `PATCH /admin/tenants/{id}` accepting `{"name": <string>}` (pydantic `UpdateTenantRequest`), allowed for archived tenants too, returning the updated tenant object; verify tests cover renaming an active tenant, renaming an archived tenant, and 404 on an unknown id
- [x] 2.5 Add `POST /admin/tenants/{id}/archive` setting `archived_at` only when null (idempotent re-archive keeps the first timestamp) and returning the updated tenant object; verify tests cover first archive setting `archived_at`, second archive returning `200` with the same `archived_at`, and 404 on an unknown id
- [x] 2.6 Confirm no tenant delete route exists; verify a test asserts `DELETE /admin/tenants/{id}` responds `405`

## 3. Tenant console page

- [x] 3.1 Create `ui/src/pages/(admin-layout)/(main)/tenants.html` (TailAdmin free components only): a create dialog with a required name field that shows the returned `api_key` exactly once with a copy button, an edit dialog for renaming, a table with tenant name + short id suffix, created date, Active/Archived status badge, and Edit/Archive actions, an All/Active/Archived filter select, an explicit empty state, and no delete control anywhere in the DOM
- [x] 3.2 Export the shared helpers (`getSecret`, `signOut`, `request`, `showMessage`, `formatDate`, tenant label helpers) from `ui/src/js/documents.js`, import them in a new `ui/src/js/tenants.js` wired into `src/js/index.js`, and implement list/create/edit/archive there (create dialog shows the `lrk_` key once, archive requires `confirm()`, all text rendered with `textContent`); verify the built page performs each flow against the running API
- [x] 3.3 Add a "Tenants" item to `ui/src/partials/layout/app-layout/sidebar/sidebar-nav-group-main.html` pointing at `/console/tenants` and set the page's `x-data`/breadcrumb so the link highlights on the new page; verify both sidebar links highlight on their own page
- [x] 3.4 Add a `GET /console/tenants` `FileResponse` route in `app/main.py` (inside the existing `UI_DIR` guard, before the `/console` mount); verify `tests/test_ui.py` covers the route serving the page and returning 404 when no UI is built
- [x] 3.5 Change the documents page's tenant fetch to `/admin/tenants?include_archived=true` so labels resolve for archived tenants' documents while the filter and upload selects offer active tenants only; verify an archived tenant's document still shows its name and the selects no longer list it

## 4. Docs & verification

- [x] 4.1 Update `AGENTS.md` §6: three pages (`documents.html`, `tenants.html`, `signin.html`), sidebar links (Documents, Tenants), the `/console/tenants` route, and the no-tenant-delete/archive-only rule; verify no stale references remain
- [x] 4.2 Run the full suite with `docker exec localrag-test pytest -q`, rebuild the UI through the node container, `docker compose up --build -d`, then verify in the browser: sign-in, create tenant with key reveal + copy, rename, filter, archive with confirmation, archived badge, no delete controls, documents page unaffected; and `curl` smoke for the new endpoints including 403 on an archived key

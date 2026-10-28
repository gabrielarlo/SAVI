# Design

## Context

The console today has two pages (`documents.html`, `signin.html`) served from
`app/main.py` inside a `UI_DIR.is_dir()` guard, one sidebar link, and one JS
module (`ui/src/js/documents.js`) that also holds the shared sign-in/fetch
helpers. Tenant state lives in `tenants` (`id, name, api_key, created_at`);
`app/auth.py:get_role` resolves `X-API-Key` to a `TenantRole` with a single
`SELECT id FROM tenants WHERE api_key = ?`. `app/db.py:migrate` replays one
hardcoded init script (`migrations/20261026000000_init.sql`, all
`CREATE TABLE IF NOT EXISTS`) on every startup — it cannot express an `ALTER`
that must run exactly once, because SQLite has no
`ADD COLUMN IF NOT EXISTS`.

## Goals / Non-Goals

**Goals:**

- Add tenant lifecycle endpoints (detail, rename, archive) and a Tenants page,
  per the delta specs.
- Keep every existing schema statement in `migrations/` and make the migration
  runner idempotent for both fresh and already-initialized databases.

**Non-Goals:**

- No un-archive, key rotation, per-tenant config, or pagination — not in the
  specs.
- No changes to the external `/api/v1/*` route surface beyond rejecting archived
  keys.

## Decisions

**Tracked, ordered migrations.** `migrate()` will create a `schema_migrations`
table, then apply every `migrations/*.sql` in filename order, skipping files
already recorded. The new `20261027000000_tenant_archiving.sql` holds only
`ALTER TABLE tenants ADD COLUMN archived_at DATETIME;` — the single place the
column is defined, so fresh databases (init then ALTER) and existing ones
(init re-runs as a no-op, then ALTER) converge on the same schema.
Alternatives: a `PRAGMA table_info` guard in Python (moves schema knowledge out
of `migrations/`, against the project convention) or adding the column to the
init script too (would make the ALTER fail on fresh databases). The init script
stays untouched.

**Reject archived keys at the single choke point.** `get_role` is where every
authenticated request resolves its role, so it is the only place that needs to
know about archiving: the lookup becomes
`SELECT id, archived_at FROM tenants WHERE api_key = ?` and a non-null
`archived_at` raises `403 Tenant account is archived` (per the `tenant-api`
delta). `403` rather than `401` also tells well-behaved external clients the
credential is valid but the account is closed, so they stop retrying it.

**Archive is a timestamp write, not a state machine.**
`POST /admin/tenants/{id}/archive` runs
`UPDATE tenants SET archived_at = CURRENT_TIMESTAMP WHERE id = ? AND archived_at IS NULL`
and then re-selects the row: already-archived tenants skip the `UPDATE`, keep
their first timestamp, and still get `200` with the full tenant object
(`id, name, created_at, archived_at` — never `api_key`). The same
select-then-return shape serves `PATCH /admin/tenants/{id}` (rename, allowed for
archived tenants) and `GET /admin/tenants/{id}`; all three share one
`_tenant_or_404` helper mirroring `_document_or_404`. No route ever deletes a
tenant row — `DELETE /admin/tenants/{id}` stays the framework's default `405`.

**`include_archived` as a plain bool query parameter.** FastAPI coerces
`?include_archived=true` to `bool`; the SQL adds `WHERE archived_at IS NULL`
unless it is set, keeping `created_at ASC` ordering and the no-`api_key` rule.

**One new page, one new module, shared helpers exported.** The page is
`ui/src/pages/(admin-layout)/(main)/tenants.html` (webpack flattens it to
`build/tenants.html`) served at `GET /console/tenants` next to the existing
`FileResponse` routes. `ui/src/js/tenants.js` is imported by `src/js/index.js`
alongside `documents.js`; the shared helpers already in `documents.js`
(`request`, `signOut`, `showMessage`, `formatDate`, `getSecret`, tenant label
helpers) get `export` keywords and are imported from there — smallest diff,
one bundle, no new module to invent. The page fetches
`/admin/tenants?include_archived=true` once and filters All/Active/Archived
client-side; the create dialog shows the returned `api_key` exactly once with
a copy button (`navigator.clipboard.writeText`, which works because localhost is
a secure context; the key also stays selectable as a fallback). All text is
rendered with `textContent`, no delete control exists in the DOM.

**Documents page keeps resolving names.** The default tenant list now excludes
archived tenants, so the documents page would show `Unknown tenant` for an
archived tenant's documents. Its tenant fetch therefore passes
`include_archived=true` (labels keep resolving for every stored document), while
the filter and upload selects offer only active tenants — you should not be
able to start new work for an archived account from the UI.

## Risks / Trade-offs

- [An edited migration never re-runs] → never modify an applied file; add new
  files instead (standard migration discipline).
- [`include_archived` default `false` changes `GET /admin/tenants`] → the only
  consumer is the admin UI, updated in the same change; the spec change is the
  contract.
- [Clipboard API unavailable on non-secure origins] → the key is displayed as
  selectable text as well; copying is convenience, not the only path.
- [Archived tenant data is never cleaned up] → deletion is explicitly out of
  scope by request; storage cost of archived rows is accepted.

## Migration Plan

Additive `ALTER TABLE` on startup — instant on SQLite, no data rewrite, no
downtime; a fresh checkout and an existing volume converge automatically.
Rollback (if ever needed) is dropping the nullable column or leaving it in
place; nothing reads it except the new code paths.

# Proposal

## Why

Currently, operators can only list and create tenants via the API, and there is no UI page to manage tenants or archive former clients. To support full tenant lifecycle management safely without risk of data loss, we need a dedicated Tenant Management page in the UI that supports tenant creation, editing, and archiving (with explicit prohibition of deletion).

## What Changes

- Add an `archived_at` column to the `tenants` table via migration.
- Update `tenant-api` to:
  - Add `GET /admin/tenants/{id}` to fetch details for a single tenant.
  - Add `PATCH /admin/tenants/{id}` to update tenant attributes (e.g., name).
  - Add `POST /admin/tenants/{id}/archive` to archive a tenant (setting `archived_at`).
  - Reject requests with `403 Forbidden` (or `401`) when an archived tenant attempts to authenticate using their API key against tenant API endpoints.
  - Expose query parameter filter on `GET /admin/tenants` (`include_archived` or status filtering).
- Update `admin-ui` to:
  - Add a dedicated Tenant Management page (`/console/tenants`) accessible via sidebar navigation.
  - Allow operators to create new tenants, update existing tenant names, and archive tenants.
  - Prohibit tenant deletion in the UI and API.
  - Filter active and archived tenants in the UI list view.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `tenant-api`: Add tenant update, detail, archive endpoints, status filtering on list endpoint, and block archived tenants from API key authentication.
- `admin-ui`: Add dedicated Tenant Management UI page, navigation sidebar link, modal/forms for creation/editing/archiving, and status filtering.

## Impact

- **Database**: New migration `20261027000000_tenant_archiving.sql` adding `archived_at DATETIME NULL` to `tenants`.
- **Frontend**: New page `ui/src/pages/(admin-layout)/(main)/tenants.html`, JS controller `ui/src/js/tenants.js`, updated sidebar navigation in layout partials, updated webpack configuration if needed.
- **Tests**: `tests/test_tenants.py` or updated `test_routes.py` covering tenant management and archiving behavior.

> Re-confirmed 2026-10-28: the follow-up request "add tenant management page
> without delete but archive only" is already covered by this change — see
> specs/tenant-api (archive endpoint, 405 on delete) and specs/admin-ui
> ("No deletion controls exist" scenario). Scope unchanged.
- **Backend**: `app/routes.py` (new and updated tenant admin endpoints), `app/auth.py` (check for non-archived tenant on API key auth).
- **Frontend**: New page `ui/src/pages/tenants.html`, JS controller `ui/src/js/tenants.js`, updated sidebar navigation in layout partials, updated webpack configuration if needed.
- **Tests**: `tests/test_tenants.py` or updated `test_routes.py` covering tenant management and archiving behavior.

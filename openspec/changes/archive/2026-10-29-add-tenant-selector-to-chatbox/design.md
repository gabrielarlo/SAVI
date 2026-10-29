# Design

## Context

The chat widget lives in `ui/src/partials/layout/app-layout/header/chat-widget.html`
and is driven by `ui/src/js/chat.js`. It calls `POST /admin/chat` and
`POST /admin/chat/voice` through the shared `request()` helper in
`documents.js`, which already attaches the admin secret or session token.
Tenant display-name helpers (`setTenants`, `tenantLabel`) and the `GET /admin/tenants`
endpoint already exist, so the selector can reuse them. The backend already
enforces scoping: administrators may omit `tenant_id` (all accounts) or supply
one; account managers must supply one or receive `400`.

## Goals / Non-Goals

**Goals:**
- Add a tenant/account selector to the chat widget header.
- Load active tenants once on widget init and label them consistently.
- Detect the signed-in user's role (session profile vs. admin secret).
- Gate sending for account managers until a tenant is chosen.

**Non-Goals:**
- No schema migration or new dependencies; retrieval changes reuse existing SQLite.
- No per-message tenant switching history; selector value applies to each request.
- No tenant assignment to users (account managers still choose a tenant per inquiry).
- The chatbox selector MUST NOT drive or alter page-level tenant filters or page data.

## Decisions

1. **Role detection**: If a session token exists, call `GET /auth/profile` to get
   `role`; otherwise treat the caller as `administrator` (admin secret) without
   calling the endpoint. This avoids 401 sign-outs for admin-secret users.
   - Alternative: store role at sign-in. Rejected: would require migrating stored
     sessions and risks stale role after role changes.

2. **Tenant list**: Reuse `GET /admin/tenants` (active only) and `setTenants()` so
   labels match the rest of the console, including disambiguation suffixes.
   - Alternative: a separate chat-only endpoint. Rejected: duplicates existing data.

3. **Selector placement**: In the chat panel header next to "New conversation",
   so it is visible without scrolling and persists across messages.

4. **"All accounts" option**: Represented by an empty `value` in the select; the
   request omits `tenant_id` when empty. Administrators only.

5. **Disabling sends**: For account managers, keep the textarea submit and mic
   button disabled until a tenant is selected; show a hint. Administrators can
   send immediately (defaults to "All accounts").

6. **Retrieval for "All accounts"**: Replace the arbitrary `LIMIT 5` fetch with
   relevance-based retrieval (keyword match on the inquiry, falling back to a
   bounded recent set when no match) so scoped and unscoped inquiries can answer
   from relevant documents. Applies to `/admin/chat` and `/admin/chat/voice`.

## Risks / Trade-offs

- [Profile fetch adds one request on first widget use] → Acceptable; cached in
  module scope for the page lifetime.
- [Tenant list can be large] → Existing endpoint returns all active tenants;
  selector is a native `<select>`, which handles long lists adequately.
- [Role change mid-session] → Profile is read per page load; acceptable.

## Migration Plan

Static bundle rebuild via Docker (`npm ci && npm run build` inside the node
stage) and `docker compose up --build -d`. No database migration. No API change.

## Open Questions

(none)
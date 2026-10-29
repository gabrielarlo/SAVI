# Proposal

## Why

The console chat widget currently always inquires across all documents (or fails for
account managers who must scope to a tenant). There is no way for an operator to choose
which tenant/account the inquiry targets from the chat box, so scoping depends on the
caller remembering to pass `tenant_id` elsewhere. Adding an in-widget tenant selector
lets administrators choose "All accounts" or a specific tenant, and requires account
managers to pick a tenant, matching the backend's existing scoping rules.

## What Changes

- Add a tenant/account selector to the console-wide chat widget.
- Populate the selector from `GET /admin/tenants`, using tenant display names.
- For administrators, include an "All accounts" option and default to it.
- For account managers, require a tenant selection before sending (no "All accounts").
- Send the selected `tenant_id` (or omit it for "All accounts") in `POST /admin/chat`
  and `POST /admin/chat/voice`.
- Disable sending while an account manager has no tenant selected.
- The selector lives only in the chat widget; changing it MUST NOT affect page-level
  tenant filters or page data.
- Admin inquiry retrieval MUST return relevant chunks for the chosen scope (including
  "All accounts"), not an arbitrary first N chunks, so inquiries can answer from
  documents beyond the first few.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `admin-ui`: chat widget gains a tenant/account selector whose options depend on the
  authenticated user's role and scope.
- `retrieval`: admin inquiry chat retrieval must return relevant chunks for the applied
  scope (including "All accounts") rather than an arbitrary first N.
- `voice-chat`: admin voice inquiry retrieval must use the same relevance-based retrieval
  as text chat.

## Impact

- `ui/src/partials/layout/app-layout/header/chat-widget.html` (selector markup)
- `ui/src/js/chat.js` (tenant loading, role detection, request payload)
- `ui/src/js/documents.js` (reuse `setTenants`/`tenantLabel` helpers)
- `openspec/specs/admin-ui/spec.md` (chat widget requirement)
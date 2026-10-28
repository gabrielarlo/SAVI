# Design

## Context

The service already has `/admin/search` (cross-tenant chunk lookup) and
`/api/v1/chat` (tenant-scoped). Console auth supports both `X-Admin-Secret`
and session tokens via `get_role`. The new feature reuses the existing chunk
query pattern and auth choke point; no schema change is needed.

## Goals / Non-Goals

**Goals:**
- Add `POST /admin/chat` with role-based tenant scoping.
- Add a floating chat widget to the shared console layout.
- Keep isolation at the SQL layer.

**Non-Goals:**
- No LLM generation beyond the existing stub response; sources are the deliverable.
- No new user-tenant assignment table; account managers supply a tenant scope in
  the request (UI enforces selection).
- No Qdrant/vector changes.

## Decisions

**Reuse the chat response shape.** `/admin/chat` returns the same
`{tenant_id, response, sources}` shape as `/api/v1/chat`, plus `tenant_id` on
each source for attribution, matching `/admin/search`. Admins may omit
`tenant_id` for an all-tenant inquiry; account managers must provide it.

**Role awareness from the session.** `get_role` already resolves session tokens
to `AdminRole`. To distinguish account managers, look up the user's role when
resolving a session token and store it on `AdminRole` (default
`administrator` for the admin secret). `require_admin` keeps accepting any
admin role; the route checks `role.role` for scoping. This avoids a second auth
mechanism.

**SQL scoping.** When a `tenant_id` is applied, filter
`chunks.tenant_id = ?`; otherwise no filter. Limit results (e.g. 5) like
existing chat/search.

**Answer generation.** After retrieving sources, call Ollama with model
`llama3.2:3b` to produce a concise, greeting-free, JARVIS-style answer
addressing the user by `CODE_NAME` (read from the environment). On any Ollama
failure, return the sources with a fallback response, matching the existing
degradation pattern in `get_embedding`.

**UI widget.** Add `ui/src/js/chat.js` and include the widget markup in the
shared sidebar/layout partial so it is present on every console page. It reuses
`request()` from `documents.js` (exported) and renders sources with
`textContent`.

## Risks / Trade-offs

- Account-manager scoping is enforced by required `tenant_id`, not by an
  assignment table; stricter per-user tenant assignment is a follow-up.
- Result limits and ranking remain naive (LIMIT, no relevance scoring), matching
  existing endpoints.

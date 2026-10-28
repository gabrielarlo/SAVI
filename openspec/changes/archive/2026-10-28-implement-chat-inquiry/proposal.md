# Proposal

## Why

Operators today can search documents (`/admin/search`) and external clients can chat
within a single tenant (`/api/v1/chat`), but there is no conversational inquiry
surface for authenticated console users that respects role scope: administrators
need to inquire across all documents, while account managers must stay within their
assigned accounts. There is also no chat entry point in the console UI, so inquiry
is unavailable where operators actually work.

## What Changes

- Add an internal inquiry chat endpoint `POST /admin/chat` for authenticated
  console users (admin secret or session).
  - Administrators may inquire across all documents, optionally narrowing to a
    single tenant via `tenant_id`.
  - Account managers MUST supply a `tenant_id` and may only inquire within that
    scoped account.
- Add a floating chat widget available on every console page, visible only to
  authenticated users, that calls the new endpoint and renders sources as text.
- Generate the inquiry answer with the local Ollama model `llama3.2:3b`: a concise
  reply with no greetings, in a JARVIS-like tone, addressing the user by the
  configured `CODE_NAME` (the LLM's name, e.g. `SAVI` from `.env`).
- Keep tenant isolation at the SQL layer: every inquiry filters chunks by
  tenant when a scope is present.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `retrieval`: add an internal admin inquiry chat requirement with role-based
  scoping.
- `admin-ui`: add a console-wide chat widget requirement for authenticated users.

## Impact

- **Backend**: `app/routes.py` (new `/admin/chat` route), `app/auth.py` (role
  awareness for session users, optional).
- **Frontend**: layout partials + a new `ui/src/js/chat.js` module, chat widget
  markup on all console pages.
- **Tests**: route coverage for admin inquiry and role scoping.
- **No schema change.**

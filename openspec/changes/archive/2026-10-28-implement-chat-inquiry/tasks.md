# Tasks

## 1. Backend

- [x] 1.1 Add `role` and `username` fields to `AdminRole` in `app/auth.py` (defaults `administrator` / `None`); resolve them from the session token lookup.
- [x] 1.2 Add `POST /admin/chat` route in `app/routes.py` with `ChatRequest`-compatible body (`message`, optional `tenant_id`); enforce tenant_id requirement for account managers.
- [x] 1.3 Implement SQL scoping (filter `chunks.tenant_id` when scope present) and return `{tenant_id, response, sources}` with `tenant_id` on each source.
- [x] 1.4 Add tests in `tests/test_api.py` for admin chat (all tenants, scoped, tenant key rejected).

## 2. Frontend

- [x] 2.1 Create `ui/src/js/chat.js` widget module reusing `request`/`getSecret`/session helpers.
- [x] 2.2 Add widget markup to the shared layout partial so it appears on all console pages.
- [x] 2.3 Render sources with `textContent`; scope selector for account managers.
- [x] 2.4 Add UI route test if needed (page served).

## 3. Validation

- [x] 3.1 Run full test suite in Docker.
- [x] 3.2 Rebuild UI bundle and service.

## 4. LLM answer generation

- [x] 4.1 Add `code_name` and chat model settings to `Config` (default model `llama3.2:3b`, code name from `CODE_NAME`).
- [x] 4.2 Add a helper in `app/services.py` to generate a concise JARVIS-style answer from sources via Ollama.
- [x] 4.3 Update `/admin/chat` to call the helper and return the generated `response`.
- [x] 4.4 Add tests for answer generation and Ollama fallback.
- [x] 4.5 Run test suite and rebuild service.

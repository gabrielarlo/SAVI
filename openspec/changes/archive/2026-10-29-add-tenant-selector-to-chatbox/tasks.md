# Tasks

## 1. Markup

- [x] 1.1 Add a tenant/account `<select id="chat-tenant">` to the chat widget header and verify it renders on every console page
- [x] 1.2 Add an "All accounts" option placeholder and a disabled-state hint element and verify markup is valid

## 2. Frontend logic

- [x] 2.1 Fetch tenants via `GET /admin/tenants?include_archived=true`, call `setTenants(all)` for consistent labels, then populate the selector with active tenants only; verify labels match the console
- [x] 2.2 Detect the signed-in user's role via `GET /auth/profile` only when a session token exists; treat admin-secret sessions as administrator without calling the profile endpoint; verify no 401 sign-out occurs
- [x] 2.3 For administrators default the selector to "All accounts"; for account managers include a disabled placeholder option and leave it selected, disabling sending until a tenant is chosen; verify both roles
- [x] 2.4 Guard the submit handler and mic button with a `canSend()` check and toggle disabled state plus a hint; verify sending is blocked for unscoped account managers
- [x] 2.5 Include the selected `tenant_id` in `POST /admin/chat` JSON and append it to `POST /admin/chat/voice` FormData (omit for "All accounts"); verify scoped responses
- [x] 2.6 Wrap tenant/role fetches in try/catch so widget failures degrade gracefully; verify the widget still loads on fetch errors
- [x] 2.7 Add `_retrieve_inquiry_chunks(db, tenant_id, query, limit=5)` in `app/routes.py`: tokenize the query (strip punctuation, drop empties), filter scoped chunks with fully parameterized case-insensitive `LIKE ? ESCAPE '\'` on any token (escaping backslash, `%`, and `_`), and fall back to the most recent scoped chunks `ORDER BY rowid DESC` when no token matches; use it in both `/admin/chat` (message) and `/admin/chat/voice` (transcript, after the empty-transcript guard); verify scoped and "All accounts" inquiries return relevant sources

## 3. Verification

- [x] 3.1 Rebuild the UI bundle in Docker and restart the service; verify the selector appears and functions
- [x] 3.2 Run the existing test suite and verify all tests pass
- [x] 3.3 Verify changing the chatbox tenant selector does not alter page-level tenant filters or page data
- [x] 3.4 Verify "All accounts" inquiry returns relevant chunks across tenants (not arbitrary first 5)
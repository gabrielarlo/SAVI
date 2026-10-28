# admin-ui Specification

## Purpose

Provides internal operators with a browser interface for managing documents —
sign in, see what is stored, upload files, inspect chunks, and delete — built on
the TailAdmin free template and served by the same FastAPI process.

## Requirements

### Requirement: UI delivery
The service SHALL serve the built admin interface at `/console/documents` and MUST redirect `GET /` there. The service SHALL also serve the Users management view at `/console/users`.

- The sign-in page MUST be served at `/auth/signin` and MUST support
  username/password authentication (username + password fields, no email
  input). The form MUST submit when the user presses Enter in either field.
  The password field MUST include a visibility toggle rendered inside the
  input (right-aligned overlay with input right padding, never detached
  outside the field) that toggles masked/visible without changing the
  submitted value. The password input with toggle MUST be a reusable
  partial/component used by every password field (sign-in and any
  user-management password field).
- `/console/users` MUST be served inside the `UI_DIR` guard.
- `/console` MUST serve a dashboard page (may be empty/placeholder for now).
- Successful login MUST redirect to `/console`.
- An authenticated session (valid session token or admin secret) MUST NOT reach `/console/signin`; it MUST be redirected to `/console`.
- The sidebar MUST include a Users navigation item.
- The interface MUST be the built output of the vendored TailAdmin free template; no TailAdmin Pro assets or components may be used.
- The template's MIT licence and attribution MUST remain in the repository.
- Static assets MUST be served under `/console/`.
- All `/console/*` routes MUST require an authenticated session (valid session token or admin secret); unauthenticated requests MUST redirect to `/auth/signin`. Static assets under `/console/` are exempt only where needed to render the sign-in page; otherwise protected.

#### Scenario: Landing redirect
- **WHEN** a browser requests `/`
- **THEN** it is redirected to `/console/documents`

#### Scenario: UI assets load
- **WHEN** a browser requests `/console/documents` without credentials
- **THEN** the sign-in page loads and no document data is present in the response

#### Scenario: Users page route
- **WHEN** a browser requests `/console/users` with a built UI
- **THEN** the Users page is served

#### Scenario: Dashboard route
- **WHEN** a browser requests `/console` (or `/console/`)
- **THEN** the dashboard page is served

#### Scenario: Login redirect
- **WHEN** an operator signs in successfully
- **THEN** the browser is redirected to `/console`

#### Scenario: Authenticated user blocked from signin
- **WHEN** an authenticated user requests `/auth/signin`
- **THEN** they are redirected to `/console` and never see the sign-in form

#### Scenario: Unauthenticated console access
- **WHEN** an unauthenticated user requests any `/console/*` route
- **THEN** they are redirected to `/auth/signin`

#### Scenario: Username/password sign-in
- **WHEN** an operator signs in with a username and its correct password
- **THEN** authentication succeeds using the username/password flow and no email input is offered

#### Scenario: Submit on Enter
- **WHEN** an operator fills both fields and presses Enter in either field
- **THEN** the sign-in form submits and authentication is attempted

#### Scenario: Password toggle inside input
- **WHEN** an operator views any password field
- **THEN** the visibility toggle is rendered inside the input (not detached outside it)
- **WHEN** the operator activates the toggle
- **THEN** the field switches between masked and visible without altering the submitted value

#### Scenario: Reusable password input
- **WHEN** a page needs a password field
- **THEN** it reuses the shared password-input partial/component instead of duplicating markup

### Requirement: Sign-in with the admin secret

The interface SHALL require the admin secret before showing document data.

- The secret MUST be validated by calling an admin endpoint; a `401` MUST be
  shown as an error and MUST NOT be stored.
- A validated secret MUST be kept in `sessionStorage` only — never in
  `localStorage` or a cookie — and MUST be sent as `X-Admin-Secret` on API calls.
- Signing out MUST clear the stored secret.

#### Scenario: Wrong secret

- **WHEN** an operator enters an incorrect secret
- **THEN** the page shows the API error message and remains on the sign-in view

#### Scenario: Secret not persisted across browser sessions

- **WHEN** the browser tab is closed and the UI is reopened
- **THEN** the operator is asked to sign in again

### Requirement: Documents table

The interface SHALL list documents from `GET /admin/documents`.

- Columns MUST show title, tenant name, chunk count, and creation time.
- The tenant column MUST show the tenant's name, never its raw id; names are
  resolved from `GET /admin/tenants`.
- When two tenants share a name, the display MUST disambiguate them without
  falling back to the full id.
- A tenant filter MUST narrow the list using the `tenant_id` query parameter.
- The table MUST show an explicit empty state when no documents match.

#### Scenario: List reflects stored documents

- **WHEN** an operator opens the documents page after ingestion
- **THEN** every stored document appears with its tenant name and chunk count

#### Scenario: Tenant ids stay out of the interface

- **WHEN** a document belongs to a tenant with a display name
- **THEN** the table and the chunk preview show that name, and no raw tenant id appears

#### Scenario: Filter by tenant

- **WHEN** an operator selects a tenant in the filter
- **THEN** only that tenant's documents are listed

### Requirement: Upload form

The interface SHALL let an operator upload a document through
`POST /admin/documents/upload`.

- The form MUST require a tenant, chosen from `GET /admin/tenants`.
- The file picker MUST accept only `.txt`, `.md`, and `.pdf`.
- The submit control MUST be disabled while an upload is in flight.
- On success the table MUST refresh; on failure the API error message MUST be
  displayed without losing the form's values.

#### Scenario: Successful upload

- **WHEN** an operator selects a tenant, chooses a `.pdf` file, and submits
- **THEN** the new document appears in the table without a page reload

#### Scenario: Rejected upload

- **WHEN** the API rejects an upload with `415` or `413`
- **THEN** the form shows the returned message and the table is unchanged

### Requirement: Chunk preview and deletion

The interface SHALL let an operator inspect a document's chunks and delete it.

- Opening a document MUST fetch `GET /admin/documents/{id}` and display each
  chunk's index and content.
- Deletion MUST require an explicit confirmation before calling
  `DELETE /admin/documents/{id}`, and MUST remove the row on success.
- Document and chunk text MUST be rendered as text, never as HTML.

#### Scenario: Inspect chunks

- **WHEN** an operator opens a document that has three chunks
- **THEN** the three chunks are shown in ascending index order

#### Scenario: Delete requires confirmation

- **WHEN** an operator clicks delete and cancels the confirmation
- **THEN** no request is sent and the document remains

#### Scenario: Script in content stays inert

- **WHEN** a document contains `<script>` markup
- **THEN** the chunk preview shows it as literal text and no script executes

### Requirement: Tenant Management UI delivery and navigation

The service SHALL serve the Tenant Management view at `/console/tenants` and include navigation links to it in the sidebar layout.

- The layout sidebar MUST contain a "Tenants" navigation link leading to `/console/tenants`.
- Navigating to `/console/tenants` without an authenticated admin secret MUST redirect or show the sign-in prompt.
- The UI MUST be consistent with TailAdmin free styling.

#### Scenario: Navigate to Tenants page

- **WHEN** an authenticated operator clicks the "Tenants" link in the sidebar
- **THEN** the browser loads `/console/tenants` showing the tenant management view

### Requirement: Tenant management table and filtering

The Tenant Management UI SHALL list tenants fetched from `GET /admin/tenants?include_archived=true`.

- Columns MUST display tenant name, short ID suffix, created date, and status (Active or Archived).
- A filter toggle MUST allow filtering between "All", "Active", and "Archived" tenants.
- An explicit empty state MUST be shown when no tenants match the selected filter.

#### Scenario: List active and archived tenants

- **WHEN** an operator views the Tenant Management page with "All" selected
- **THEN** all active and archived tenants are displayed with status badges

#### Scenario: Filter by active status

- **WHEN** an operator selects "Active" filter
- **THEN** only non-archived tenants are displayed in the table

### Requirement: Tenant creation and inline editing

The Tenant Management UI SHALL allow operators to create new tenants and update existing tenant names.

- A "Create Tenant" button MUST open a modal or form requiring a tenant name.
- Submitting the creation form calls `POST /admin/tenants` and displays the newly created API key ONCE to the operator in a modal with a copy button.
- An "Edit" action MUST allow updating a tenant's display name via `PATCH /admin/tenants/{id}`.

#### Scenario: Successfully create tenant with API key reveal

- **WHEN** an operator creates a tenant named "Beta Corp"
- **THEN** the tenant is saved, and a modal displays "Beta Corp" and its generated `api_key` (`lrk_...`) with a copy button

#### Scenario: Edit tenant name

- **WHEN** an operator clicks edit on a tenant and submits a new name
- **THEN** `PATCH /admin/tenants/{id}` is called and the table updates without page reload

### Requirement: Tenant archiving and deletion prohibition

The Tenant Management UI SHALL allow operators to archive active tenants and MUST NOT provide any option to delete tenants.

- An "Archive" action button MUST be visible for active tenants.
- Clicking "Archive" MUST require explicit confirmation before invoking `POST /admin/tenants/{id}/archive`.
- Once archived, the row status updates to "Archived" and the "Archive" action is disabled or hidden.
- The UI MUST NOT display any "Delete" or "Remove" button or interface element for tenants.

#### Scenario: Archive tenant with confirmation

- **WHEN** an operator clicks "Archive" for an active tenant and confirms
- **THEN** `POST /admin/tenants/{id}/archive` is called, and the tenant status changes to Archived

#### Scenario: No deletion controls exist

- **WHEN** an operator inspects any tenant row in the table (active or archived)
- **THEN** no delete button or delete action option is present in the DOM

### Requirement: Console-wide chat widget

The admin interface SHALL provide a chat inquiry widget available on every
console page, visible and functional only for authenticated users.

- The widget MUST be rendered in the shared layout so it appears on all
  `/console/*` pages.
- The widget MUST call `POST /admin/chat` with the admin secret or session token.
- An administrator MUST be able to inquire across all documents; an account
  manager MUST be restricted to a selected scoped account.
- All document and chunk text returned by the widget MUST be rendered as text,
  never as HTML.
- Unauthenticated users MUST NOT be able to use the widget; console pages already
  require authentication.
- The floating launcher button MUST be labeled `Chat with <CODE_NAME>`, using
  the configured persona name.
- The widget MUST present a chat-style layout with a header, scrollable message
  area, and input bar.
- Conversation history MUST persist across page refresh for up to 24 hours from
  the latest message and MUST be restored on load.
- A "New conversation" control MUST clear persisted history and reset the view.

#### Scenario: Widget present on console pages

- **WHEN** an authenticated user opens any `/console/*` page
- **THEN** the chat widget is available in the page layout

#### Scenario: Launcher labeled with persona

- **WHEN** the widget renders its floating launcher
- **THEN** the button text is `Chat with <CODE_NAME>`

#### Scenario: Widget renders sources as text

- **WHEN** the chat widget displays inquiry sources
- **THEN** source content is rendered as text, never injected as HTML

#### Scenario: Conversation persists across refresh

- **WHEN** a user refreshes a console page after chatting
- **THEN** the previous messages are restored

#### Scenario: New conversation clears history

- **WHEN** the user clicks "New conversation"
- **THEN** persisted messages are removed and the view resets

#### Scenario: Unauthenticated cannot inquire

- **WHEN** an unauthenticated request is made to `/admin/chat`
- **THEN** the service responds `401`

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
- The widget MUST include a tenant/account selector whose available options depend
  on the authenticated user's role.
- For an administrator, the selector MUST offer an "All accounts" option plus every
  active tenant, defaulting to "All accounts".
- For an account manager, the selector MUST offer only active tenants (no
  "All accounts" option) and MUST require a selection before sending.
- The widget MUST send the selected tenant id as `tenant_id` in `POST /admin/chat`
  and `POST /admin/chat/voice` requests, and MUST omit `tenant_id` when
  "All accounts" is selected.
- While an account manager has no tenant selected, the widget MUST disable
  sending (text submit and voice recording).
- The selector MUST be confined to the chat widget; changing it MUST NOT affect
  page-level tenant filters, page data, or trigger a page reload.

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

#### Scenario: Administrator sees all-accounts option

- **WHEN** an administrator opens the chat widget
- **THEN** the tenant selector offers "All accounts" plus every active tenant
  and defaults to "All accounts"

#### Scenario: Account manager must select a tenant

- **WHEN** an account manager opens the chat widget
- **THEN** the tenant selector offers only active tenants, has no "All accounts"
  option, starts unselected, and sending is disabled until a tenant is chosen

#### Scenario: Inquiry scoped to selected tenant

- **WHEN** a user selects a tenant and sends a message
- **THEN** the request includes that tenant's id as `tenant_id` and only that
  tenant's chunks are considered

#### Scenario: Selector does not affect the page

- **WHEN** a user changes the chat widget's tenant selector
- **THEN** page-level tenant filters and displayed page data remain unchanged
  and no page reload occurs

### Requirement: All modals centered

Every modal dialog in the console MUST be centered in the viewport, including
document View, tenant Edit/Create, and user Create/Edit/Archive dialogs.

#### Scenario: Any modal centered

- **WHEN** any modal dialog opens
- **THEN** it is centered in the viewport

### Requirement: Reusable modal component

The console SHALL provide a reusable modal component (overlay + panel) used by
all dialogs to ensure consistent centering and styling.

#### Scenario: Reusable modal used

- **WHEN** a dialog is rendered
- **THEN** it uses the shared modal overlay/panel classes

### Requirement: Confirmation for data mutations

All data mutation actions (documents, tenants, users: create, update, archive,
delete) MUST require an explicit confirmation modal before the request is sent.

#### Scenario: Create user confirmed

- **WHEN** an operator submits the create-user form
- **THEN** a confirmation modal appears and the request is sent only after
  confirmation

#### Scenario: Archive user confirmed

- **WHEN** an operator clicks Archive on a user
- **THEN** a confirmation modal appears before the archive request

#### Scenario: Delete document confirmed

- **WHEN** an operator clicks Delete on a document
- **THEN** a confirmation modal appears before the delete request

#### Scenario: Tenant mutation confirmed

- **WHEN** an operator creates, updates, or archives a tenant
- **THEN** a confirmation modal appears before the request is sent

### Requirement: Centered modal dialogs

All modal dialogs in the console MUST be centered in the viewport both
horizontally and vertically.

#### Scenario: Modal centered

- **WHEN** a modal dialog opens
- **THEN** it is centered in the viewport

### Requirement: Header username display

The header user dropdown MUST display the signed-in username instead of a static
"Admin" label.

#### Scenario: Header shows username

- **WHEN** a user is signed in
- **THEN** the header displays their username

### Requirement: Text-based avatar

The user dropdown avatar MUST render text initials derived from the signed-in
username instead of an image, using the first two letters uppercased (e.g.
`savi_admin` → `SA`).

#### Scenario: Avatar shows initials

- **WHEN** the signed-in username is `savi_admin`
- **THEN** the avatar displays `SA`

### Requirement: Profile modal

The console SHALL provide a Profile modal reachable from the user dropdown (not
the sidebar) for managing the signed-in user's own profile.

- The modal MUST allow updating username and password.
- Password changes MUST enforce the minimal password policy.
- The modal MUST be centered and rendered as text (no HTML injection).

#### Scenario: Open profile modal

- **WHEN** the user selects "Profile" from the user dropdown
- **THEN** the Profile modal opens centered

#### Scenario: Password policy enforced

- **WHEN** a password shorter than 8 characters is submitted
- **THEN** the request is rejected with a validation error

### Requirement: Restrict self-mutation on Users page

The Users management page MUST NOT allow the signed-in user to edit or archive
their own account. The Edit and Archive actions for the current user's row MUST
be disabled or hidden.

#### Scenario: Self row actions disabled

- **WHEN** an operator views the Users page while signed in
- **THEN** their own row has no enabled Edit or Archive action

### Requirement: Self-mutation safeguard (backend)

The service MUST reject attempts to update or archive the signed-in user via
admin user endpoints with `400` or `403`.

#### Scenario: Self update rejected

- **WHEN** an admin attempts to PATCH their own user record
- **THEN** the service responds `400` or `403`

### Requirement: Dashboard system stats

The dashboard page at `/console` SHALL display system stats fetched from
`GET /admin/stats`.

- The page MUST render one card per metric returned by `/admin/stats`
  (tenants, documents, chunks, users).
- Each card MUST show the metric label and its numeric value.
- Metric values MUST be rendered as text, never as HTML.
- If the stats request fails, the page MUST show an error message and MUST NOT
  crash.

#### Scenario: Stats cards render

- **WHEN** an authenticated operator opens `/console` and `/admin/stats`
  returns `{"tenants": 2, "documents": 3, "chunks": 9, "users": 1}`
- **THEN** four cards are shown with labels Tenants, Documents, Chunks, and
  Users and values `2`, `3`, `9`, and `1`

#### Scenario: Stats request fails

- **WHEN** `/admin/stats` returns an error
- **THEN** an error message is shown on the dashboard and no unhandled
  exception occurs

### Requirement: Dashboard live refresh

The dashboard page at `/console` SHALL refresh its stats automatically.

- The page MUST poll `GET /admin/stats` on an interval of 3 to 5 seconds
  while the page is visible.
- Polling MUST pause when the page is hidden and resume when visible again.
- A "Live" indicator (text plus an animated SVG dot) MUST be shown while
  polling is active.

#### Scenario: Auto refresh

- **WHEN** an operator leaves the dashboard open for 6 seconds
- **THEN** at least one additional `/admin/stats` request is made after the
  initial load

#### Scenario: Live indicator visible

- **WHEN** the dashboard is loaded successfully
- **THEN** a "Live" label and an animated dot are rendered

#### Scenario: Pause when hidden

- **WHEN** the page becomes hidden
- **THEN** no further polling requests are made until it is visible again

### Requirement: Dashboard inquiry metrics

The dashboard SHALL display inquiry metrics returned by `/admin/stats`.

- The page MUST render cards for total inquiries and inquiries today (or the
  latest day's count).
- Values MUST be rendered as text, never as HTML.

#### Scenario: Inquiry cards render

- **WHEN** `/admin/stats` returns `inquiries` equal to `5`
- **THEN** a card shows the value `5`

### Requirement: Dashboard visual polish

The dashboard SHALL present a polished, responsive layout.

- The stat cards MUST be laid out in a responsive grid (1 column on small
  screens, 2 on medium, 4 on large).
- The page MUST show loading placeholders while the first stats response is
  pending.
- Cards MUST use the shared TailAdmin card styling (rounded border, padding)
  and consistent spacing.
- Values MUST be rendered as text, never as HTML.

#### Scenario: Responsive grid

- **WHEN** the dashboard is viewed on a large screen
- **THEN** four stat cards appear per row

#### Scenario: Loading state

- **WHEN** stats have not yet loaded
- **THEN** placeholder cards are shown instead of empty space

### Requirement: Tenant API key copy and regeneration UI

The tenant management UI SHALL let operators copy and regenerate a tenant's
API key.

- Each tenant row MUST provide a "Copy" action that fetches and copies the
  current API key to the clipboard.
- Each tenant row MUST provide a "Regenerate" action requiring confirmation
  before calling `POST /admin/tenants/{id}/regenerate-key`.
- The regenerated key MUST be shown once in a modal with a copy button.

#### Scenario: Copy key

- **WHEN** an operator clicks "Copy" for a tenant
- **THEN** the current API key is fetched and copied to the clipboard

#### Scenario: Regenerate key

- **WHEN** an operator confirms regeneration
- **THEN** a new key is shown once in a modal with a copy button

### Requirement: Tenant API key auto-rotation settings UI

The tenant management UI SHALL allow configuring auto-rotation.

- An edit form MUST allow toggling auto-rotation and selecting the rotation
  interval from a dropdown of predefined common options (30, 60, 90, 180, 365
  days, and "Forever" which sets `rotate_days` to `null`). Default is 90 days.
- The tenant table MUST show expiry status (active/expired).

#### Scenario: Configure auto-rotation

- **WHEN** an operator sets auto-rotation to enabled with 30 days
- **THEN** `PATCH /admin/tenants/{id}` is called with those settings

### Requirement: Color-coded API key rotation metrics on dashboard

The dashboard SHALL display API key rotation urgency metrics with color coding.

- The page MUST render three cards labeled for blue, orange, and red states.
- Each card's numeric value MUST be color-coded (blue, orange, red
  respectively).
- Values MUST be rendered as text, never as HTML.

#### Scenario: Color-coded cards render

- **WHEN** `/admin/stats` returns `api_keys_blue: 2`, `api_keys_orange: 1`,
  `api_keys_red: 1`
- **THEN** three cards show values `2`, `1`, `1` with blue, orange, and red
  styling respectively

### Requirement: Grouped dashboard metrics

The dashboard SHALL group stat cards into labeled sections.

- Sections MUST include Overview, Tenants, Users, Activity, and API keys.
- Each section MUST contain its relevant cards.

#### Scenario: Sections render

- **WHEN** the dashboard loads
- **THEN** cards are grouped under section headings

### Requirement: Stat card icons and links

Each stat card SHALL include an SVG icon and link to its management page.

- The icon MUST be decorative (aria-hidden).
- Clicking a card MUST navigate to the relevant console page.

#### Scenario: Card navigates

- **WHEN** an operator clicks the Tenants card
- **THEN** the browser navigates to `/console/tenants`

### Requirement: Tenant list filters

The tenants page SHALL support filter query parameters.

- `?filter=archived` MUST show only archived tenants.
- `?filter=expiring` MUST show only tenants whose API key expires within 30
  days.

#### Scenario: Archived filter

- **WHEN** `/console/tenants?filter=archived` is opened
- **THEN** only archived tenants are listed

#### Scenario: Expiring filter

- **WHEN** `/console/tenants?filter=expiring` is opened
- **THEN** only tenants with keys expiring within 30 days are listed

### Requirement: Tenants table API key column

The tenants table SHALL include an API key column.

- The column MUST display a masked value (e.g. first 8 chars + ellipsis).
- The column MUST provide a copy action that copies the full key.
- Full keys MUST NOT be rendered in the DOM beyond the copy action.

#### Scenario: API key column renders

- **WHEN** an operator views the tenants table
- **THEN** each row shows a masked API key and a copy control

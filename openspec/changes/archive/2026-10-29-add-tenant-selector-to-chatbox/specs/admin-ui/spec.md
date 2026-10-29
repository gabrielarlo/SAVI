# Spec Delta

## MODIFIED Requirements

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
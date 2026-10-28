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
- Conversation history MUST persist across page refresh within the session and
  MUST be restored on load.
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

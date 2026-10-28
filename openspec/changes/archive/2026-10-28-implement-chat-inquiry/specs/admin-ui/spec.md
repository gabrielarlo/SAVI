# Spec Delta

## ADDED Requirements

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

#### Scenario: Widget present on console pages

- **WHEN** an authenticated user opens any `/console/*` page
- **THEN** the chat widget is available in the page layout

#### Scenario: Widget renders sources as text

- **WHEN** the chat widget displays inquiry sources
- **THEN** source content is rendered as text, never injected as HTML

#### Scenario: Unauthenticated cannot inquire

- **WHEN** an unauthenticated request is made to `/admin/chat`
- **THEN** the service responds `401`

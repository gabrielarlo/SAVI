# Spec Delta

## MODIFIED Requirements

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

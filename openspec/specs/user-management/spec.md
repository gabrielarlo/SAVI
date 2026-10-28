# user-management Specification

## Purpose

Provides user management in the console to create, list, update, and archive users with roles Administrator and Account Manager (Tenant Manager). Users MUST NOT be deletable.

## Requirements

### Requirement: User management page
The console SHALL provide a Users management page at `/console/users` following `ui/CONTRIBUTING-UI.md`.

#### Scenario: Navigate to Users
- **WHEN** an authenticated operator clicks Users in the sidebar
- **THEN** the Users page is displayed

### Requirement: User CRUD with archive-only
The system SHALL allow creating, listing, and updating users. Archiving MUST be supported and deletion MUST NOT be possible.

#### Scenario: Archive user
- **WHEN** an operator archives a user
- **THEN** the user is marked archived and cannot sign in

#### Scenario: No deletion
- **WHEN** an operator inspects the Users page
- **THEN** no delete/remove control is present

### Requirement: Password handling on user records
The system SHALL store user passwords salted and hashed, never in plaintext, and MUST NOT return a password or its hash in any user API response. User creation and password changes MUST enforce the minimal password policy (at least 8 characters).

#### Scenario: Passwords never echoed
- **WHEN** a user list or user detail response is returned
- **THEN** no password or password hash field appears in the response

#### Scenario: Hashed at rest
- **WHEN** a user row is inspected in the database
- **THEN** the stored credential is a salted hash, not the plaintext password

### Requirement: Self profile read

The service SHALL expose an endpoint for the signed-in user to read their own
profile (username, role) using their session token.

#### Scenario: Read own profile

- **WHEN** an authenticated console user requests their profile
- **THEN** the response includes username and role without password hash

### Requirement: Self profile update

The service SHALL allow the signed-in user to update their own username and/or
password.

- Password changes MUST enforce the minimal password policy (at least 8
  characters).
- The response MUST NOT include a password or hash.

#### Scenario: Update own password

- **WHEN** the user submits a valid new password
- **THEN** the password is updated and a success response is returned

#### Scenario: Short password rejected

- **WHEN** the user submits a password shorter than 8 characters
- **THEN** the request is rejected with a validation error

### Requirement: Self-mutation restriction

The service SHALL prevent an administrator from updating or archiving their own
user account through the user management endpoints.

- `PATCH /admin/users/{id}` and `POST /admin/users/{id}/archive` MUST reject
  requests where `{id}` matches the signed-in user with `400` or `403`.

#### Scenario: Self update rejected

- **WHEN** the signed-in admin calls `PATCH /admin/users/{own_id}`
- **THEN** the service responds `400` or `403`

#### Scenario: Self archive rejected

- **WHEN** the signed-in admin calls `POST /admin/users/{own_id}/archive`
- **THEN** the service responds `400` or `403`

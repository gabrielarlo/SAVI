# Spec Delta

## Purpose

Provides user management in the console to create, list, update, and archive users with roles Administrator and Account Manager (Tenant Manager). Users MUST NOT be deletable.

## ADDED Requirements

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

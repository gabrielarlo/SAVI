# Spec Delta

## Purpose

Defines username/password console authentication for LocalRAG (no email) with roles Administrator and Account Manager (Tenant Manager) and a minimal password policy. The existing `X-Admin-Secret` header MUST remain valid for API interactions.

## ADDED Requirements

### Requirement: Username/password sign-in
The system SHALL allow console sign-in using a username and password combination. The sign-in flow MUST NOT request or accept an email address.

#### Scenario: Sign in with username and password
- **WHEN** a valid username with its correct password is provided on the console sign-in page
- **THEN** the user is authenticated for the console session

#### Scenario: Wrong password
- **WHEN** a valid username is provided with an incorrect password
- **THEN** the service responds `401` with a single generic message that does not reveal whether the username exists

### Requirement: Minimal password policy
The system SHALL enforce a minimal password creation restriction: passwords MUST be at least 8 characters long. The policy MUST apply on user creation and on any password change.

#### Scenario: Short password rejected
- **WHEN** a user is created with a 7-character password
- **THEN** the request is rejected with a validation error

#### Scenario: Minimal password accepted
- **WHEN** a user is created with an 8-character password
- **THEN** the request is accepted

### Requirement: Roles
The system SHALL support two roles: `administrator` and `account_manager`. The UI MUST label `account_manager` as "Account Manager (Tenant Manager)".

#### Scenario: Administrator role
- **WHEN** a user has the Administrator role
- **THEN** they have administrative privileges in the console

#### Scenario: Account Manager role
- **WHEN** a user has the Account Manager role
- **THEN** they have tenant-management privileges as assigned

### Requirement: Seeded default administrator
The system SHALL seed a default administrator account from environment variables on startup (username and password). Seeding MUST be idempotent: if a user with that username already exists, no change is made. The seeded password MUST satisfy the minimal password policy.

#### Scenario: Seed on first start
- **WHEN** the service starts with default-admin env vars set and no matching user exists
- **THEN** an administrator user is created with the configured username and hashed password

#### Scenario: Idempotent seed
- **WHEN** the service starts again with the same env vars
- **THEN** no duplicate user is created and the existing password is untouched

#### Scenario: Missing env vars
- **WHEN** the default-admin env vars are unset
- **THEN** no default user is seeded and startup still succeeds

### Requirement: Retain API admin secret
The system MUST continue to accept `X-Admin-Secret` for all `/admin/*` routes. Username/password console auth MUST NOT interfere with header-based API authentication.

#### Scenario: API secret still valid
- **WHEN** a request includes a valid `X-Admin-Secret` header
- **THEN** it is authenticated for `/admin/*` without requiring a console user session

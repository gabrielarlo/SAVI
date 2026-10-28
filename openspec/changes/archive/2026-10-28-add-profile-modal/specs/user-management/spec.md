# Spec Delta

## ADDED Requirements

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

# Spec Delta

## ADDED Requirements

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

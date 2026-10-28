# Spec Delta

## ADDED Requirements

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

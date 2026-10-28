# Spec Delta

## ADDED Requirements

### Requirement: List tenants

The service SHALL expose `GET /admin/tenants` for internal operators so the admin
interface can populate its tenant selector.

- The response MUST be a JSON array of `{"id", "name", "created_at"}`.
- API keys MUST NOT be included in the response.
- Results MUST be ordered by `created_at` ascending.

#### Scenario: List tenants

- **WHEN** an internal operator requests `/admin/tenants` while two tenants exist
- **THEN** both tenants are returned with their id, name, and creation time

#### Scenario: No API keys leak

- **WHEN** the tenant list is returned
- **THEN** no `api_key` field appears in any entry

#### Scenario: Non-admin caller

- **WHEN** a request authenticated with a tenant API key requests `/admin/tenants`
- **THEN** the service responds `401` with message `Internal admin access required`

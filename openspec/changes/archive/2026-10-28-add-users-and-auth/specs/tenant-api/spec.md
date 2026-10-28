# Spec Delta

## MODIFIED Requirements

### Requirement: Header-based authentication
The service SHALL authenticate each request from two optional headers and MUST reject any request that presents neither a valid admin secret nor a valid tenant API key. Active tenant API keys grant access; API keys for archived tenants MUST be rejected with `403`. The `X-Admin-Secret` header MUST remain supported for all `/admin/*` routes.

- `X-Admin-Secret` grants the internal admin role when its value equals the configured admin secret.
- `X-API-Key` grants the tenant role when its value matches an active (non-archived) tenant's stored API key; the resolved tenant identifier MUST be the authenticated scope for the request.

#### Scenario: Valid admin secret
- **WHEN** a request carries `X-Admin-Secret` equal to the configured admin secret
- **THEN** the request is handled with the internal admin role

#### Scenario: Valid tenant API key
- **WHEN** a request carries `X-API-Key` matching an active row in `tenants.api_key`
- **THEN** the request is handled with the tenant role scoped to that tenant's id

#### Scenario: Valid tenant API key
- **WHEN** a request carries `X-API-Key` matching an active row in `tenants.api_key`
- **THEN** the request is handled with the tenant role scoped to that tenant's id

#### Scenario: Archived tenant API key
- **WHEN** a request carries `X-API-Key` matching a tenant whose `archived_at` is non-null
- **THEN** the service responds `403` with body `{"error": {"code": 403, "message": "Tenant account is archived"}}`

#### Scenario: Missing credentials
- **WHEN** a request carries neither header
- **THEN** the service responds `401` with body `{"error": {"code": 401, "message": "Invalid or missing authentication credentials"}}`

#### Scenario: Unknown API key
- **WHEN** a request carries an `X-API-Key` that matches no tenant
- **THEN** the service responds `401` and no tenant-scoped data is returned

#### Scenario: Admin secret retained
- **WHEN** a request to any `/admin/*` route includes a valid `X-Admin-Secret`
- **THEN** the request is authenticated with admin role regardless of console user auth changes

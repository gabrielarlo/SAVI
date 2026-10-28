# tenant-api Specification

## Purpose

Defines who may call each HTTP route: internal operators authenticate with a
shared admin secret, external clients authenticate with a tenant API key, and
every rejected request returns a consistent error body.

## Requirements

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

### Requirement: Role enforcement per route family

Admin routes (`/admin/*`) SHALL require the internal admin role and tenant routes
(`/api/v1/*`) SHALL require the tenant role. A valid credential for one family
MUST NOT authorize the other.

#### Scenario: Tenant calls an admin route

- **WHEN** a request authenticated with `X-API-Key` targets `/admin/documents`
- **THEN** the service responds `401` with message `Internal admin access required`

#### Scenario: Admin calls a tenant route

- **WHEN** a request authenticated with `X-Admin-Secret` targets `/api/v1/chat`
- **THEN** the service responds `401` with message `Tenant API key required`

### Requirement: Consistent error envelope

Every authentication, authorization, not-found, and internal failure SHALL return
a JSON body of the shape `{"error": {"code": <http status>, "message": <text>}}`
with the matching HTTP status code.

#### Scenario: Error body shape

- **WHEN** any request fails authentication or authorization
- **THEN** the response body contains an `error` object with numeric `code` and string `message` fields

### Requirement: Tenant creation issues an API key

The service SHALL expose `POST /admin/tenants` for internal operators to create a
tenant and SHALL return the generated credentials in the response.

- The request body is `{"name": <string>}`.
- The generated API key MUST be unique across tenants and MUST start with `lrk_`.
- The response MUST be `{"tenant_id": <uuid>, "name": <name>, "api_key": <key>}`.

#### Scenario: Create a tenant

- **WHEN** an internal operator posts `{"name": "acme"}` to `/admin/tenants`
- **THEN** the response is `200` with a `tenant_id`, the submitted `name`, and an `api_key` beginning with `lrk_`

#### Scenario: New key authenticates immediately

- **WHEN** a tenant is created and its `api_key` is then sent as `X-API-Key` to `/api/v1/chat`
- **THEN** the request is accepted with that tenant's scope

### Requirement: List tenants

The service SHALL expose `GET /admin/tenants` for internal operators to retrieve tenants.

- The query parameter `include_archived` (boolean, default false) controls whether archived tenants are returned.
- The response MUST be a JSON array of `{"id", "name", "created_at", "archived_at"}`.
- API keys MUST NOT be included in the response.
- Results MUST be ordered by `created_at` ascending.

#### Scenario: List tenants

- **WHEN** an internal operator requests `/admin/tenants` while two tenants exist
- **THEN** both tenants are returned with their id, name, and creation time

#### Scenario: List active tenants by default

- **WHEN** an internal operator requests `/admin/tenants` without parameters
- **THEN** only active (non-archived) tenants are returned with their id, name, creation time, and null archived_at

#### Scenario: Include archived tenants

- **WHEN** an internal operator requests `/admin/tenants?include_archived=true`
- **THEN** both active and archived tenants are returned in the response array

#### Scenario: No API keys leak

- **WHEN** the tenant list is returned
- **THEN** no `api_key` field appears in any entry

#### Scenario: Non-admin caller

- **WHEN** a request authenticated with a tenant API key requests `/admin/tenants`
- **THEN** the service responds `401` with message `Internal admin access required`

### Requirement: Get tenant detail

The service SHALL expose `GET /admin/tenants/{id}` for internal operators to retrieve details for a specific tenant.

- The response MUST be `{"id", "name", "created_at", "archived_at"}` on success.
- API keys MUST NOT be included in the response.
- If the tenant id does not exist, the service MUST respond `404`.

#### Scenario: Get existing tenant detail

- **WHEN** an internal operator requests `/admin/tenants/{tenant_id}` for a valid tenant
- **THEN** the response is `200` containing tenant details without `api_key`

#### Scenario: Get unknown tenant detail

- **WHEN** an internal operator requests `/admin/tenants/nonexistent-id`
- **THEN** the service responds `404` with message `Tenant not found`

### Requirement: Update tenant detail

The service SHALL expose `PATCH /admin/tenants/{id}` for internal operators to update tenant information.

- The request body accepts `{"name": <string>}`.
- Updating an archived tenant's name SHALL be permitted.
- The response MUST return the updated tenant object `{"id", "name", "created_at", "archived_at"}`.

#### Scenario: Successfully update tenant name

- **WHEN** an internal operator sends `PATCH /admin/tenants/{tenant_id}` with `{"name": "New Acme Name"}`
- **THEN** the tenant name is updated in SQLite and returned in the `200` response

#### Scenario: Update non-existent tenant

- **WHEN** an internal operator sends `PATCH /admin/tenants/nonexistent-id` with `{"name": "Name"}`
- **THEN** the service responds `404` with message `Tenant not found`

### Requirement: Archive tenant

The service SHALL expose `POST /admin/tenants/{id}/archive` for internal operators to archive a tenant.

- Archiving MUST set `archived_at` to the current timestamp if it is null.
- Archiving an already archived tenant MUST be idempotent and return `200`.
- The response MUST return the updated tenant object with non-null `archived_at`.

#### Scenario: Successfully archive an active tenant

- **WHEN** an internal operator posts to `/admin/tenants/{tenant_id}/archive`
- **THEN** `archived_at` is set in the database and returned in the `200` response body

#### Scenario: Archive unknown tenant

- **WHEN** an internal operator posts to `/admin/tenants/nonexistent-id/archive`
- **THEN** the service responds `404` with message `Tenant not found`

### Requirement: Prohibition of tenant deletion

The service SHALL NOT expose any HTTP endpoint or database function to permanently delete a tenant or its record.

#### Scenario: No delete endpoint for tenants

- **WHEN** an HTTP DELETE request is sent to `/admin/tenants/{id}`
- **THEN** the service responds `405 Method Not Allowed` or `404 Not Found`

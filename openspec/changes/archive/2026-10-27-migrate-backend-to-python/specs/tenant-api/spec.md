# Spec Delta

## Purpose

Defines who may call each HTTP route: internal operators authenticate with a
shared admin secret, external clients authenticate with a tenant API key, and
every rejected request returns a consistent error body.

## ADDED Requirements

### Requirement: Header-based authentication

The service SHALL authenticate each request from two optional headers and MUST
reject any request that presents neither a valid admin secret nor a valid tenant
API key.

- `X-Admin-Secret` grants the internal admin role when its value equals the
  configured admin secret.
- `X-API-Key` grants the tenant role when its value matches a tenant's stored API
  key; the resolved tenant identifier MUST be the authenticated scope for the
  request.

#### Scenario: Valid admin secret

- **WHEN** a request carries `X-Admin-Secret` equal to the configured admin secret
- **THEN** the request is handled with the internal admin role

#### Scenario: Valid tenant API key

- **WHEN** a request carries `X-API-Key` matching a row in `tenants.api_key`
- **THEN** the request is handled with the tenant role scoped to that tenant's id

#### Scenario: Missing credentials

- **WHEN** a request carries neither header
- **THEN** the service responds `401` with body `{"error": {"code": 401, "message": "Invalid or missing authentication credentials"}}`

#### Scenario: Unknown API key

- **WHEN** a request carries an `X-API-Key` that matches no tenant
- **THEN** the service responds `401` and no tenant-scoped data is returned

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

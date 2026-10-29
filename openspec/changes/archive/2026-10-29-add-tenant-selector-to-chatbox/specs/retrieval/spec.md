# Spec Delta

## MODIFIED Requirements

### Requirement: Internal admin inquiry chat

The service SHALL expose `POST /admin/chat` for authenticated console users to
inquire over stored documents.

- The request body is `{"message": <string>, "tenant_id": <string | null>}`.
- An administrator (admin secret or administrator session) MAY omit `tenant_id`
  to inquire across all tenants; when `tenant_id` is supplied, only that
  tenant's chunks are considered.
- An account manager (account_manager session) MUST supply a non-null
  `tenant_id`; an inquiry without one MUST be rejected with `400`.
- The query MUST filter on `chunks.tenant_id` at the database layer whenever a
  tenant scope is applied.
- Retrieval MUST return relevant chunks for the applied scope, including
  "All accounts", rather than an arbitrary first N chunks: match inquiry tokens
  against chunk content (case-insensitive), and fall back to the most recent
  scoped chunks when no token matches.
- The response MUST be
  `{"tenant_id": <string | null>, "response": <string>, "sources": [{"id": <string>, "tenant_id": <string>, "content": <string>}]}`.
- `sources` MUST contain only chunks visible under the applied scope.
- The route MUST require an authenticated admin/console user; tenant API keys
  MUST NOT authorize it.

#### Scenario: Administrator inquires across all documents

- **WHEN** an administrator calls `/admin/chat` with `{"message": "x"}` and no
  `tenant_id` while chunks exist for tenants A and B
- **THEN** the response is `200` and `sources` may include chunks from both tenants

#### Scenario: Administrator scopes inquiry to one tenant

- **WHEN** an administrator calls `/admin/chat` with a `tenant_id`
- **THEN** every entry in `sources` belongs to that tenant

#### Scenario: Account manager requires a tenant scope

- **WHEN** an account manager calls `/admin/chat` without `tenant_id`
- **THEN** the service responds `400`

#### Scenario: Account manager inquiry is tenant scoped

- **WHEN** an account manager calls `/admin/chat` with a `tenant_id`
- **THEN** every entry in `sources` belongs to that tenant

#### Scenario: Tenant API key cannot use admin chat

- **WHEN** a request authenticated with a tenant API key calls `/admin/chat`
- **THEN** the service responds `401` with message `Internal admin access required`

#### Scenario: All-accounts inquiry returns relevant chunks

- **WHEN** an administrator selects "All accounts" and inquires about a term
  present in a non-first chunk
- **THEN** the response includes that chunk among `sources`
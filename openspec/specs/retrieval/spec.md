# retrieval Specification

## Purpose

Serves the two read paths: a tenant-scoped chat endpoint for external clients and
a cross-tenant search endpoint for internal operators, both strictly filtered by
tenant at the query level.

## Requirements

### Requirement: Tenant-scoped chat

The service SHALL expose `POST /api/v1/chat` for clients authenticated with a
tenant API key.

- The request body is `{"message": <string>}`.
- Only chunks belonging to the authenticated tenant MUST be considered; the query
  MUST filter on `chunks.tenant_id` at the database layer.
- The response MUST be `{"tenant_id": <string>, "response": <string>, "sources": [{"id": <string>, "content": <string>}]}`.

#### Scenario: Tenant receives only its own sources

- **WHEN** tenant A calls `/api/v1/chat` while tenants A and B both have chunks
- **THEN** every entry in `sources` belongs to tenant A and none to tenant B

#### Scenario: Tenant with no chunks

- **WHEN** an authenticated tenant with no chunks calls `/api/v1/chat`
- **THEN** the response is `200` with an empty `sources` list

#### Scenario: Tenant id comes from the credential

- **WHEN** a request supplies a `tenant_id` in the body that differs from its API key's tenant
- **THEN** the body value is ignored and the response `tenant_id` matches the credential

### Requirement: Internal global search

The service SHALL expose `POST /admin/search` for internal operators to search
across all tenants.

- The request body is `{"query": <string>}`.
- The response MUST be `{"query": <string>, "results": [{"id": <string>, "tenant_id": <string>, "content": <string>}]}`.
- Results MUST include each chunk's tenant id so operators can attribute content.

#### Scenario: Search spans tenants

- **WHEN** an internal operator searches while chunks exist for tenants A and B
- **THEN** results may include chunks from both tenants, each tagged with its `tenant_id`

#### Scenario: Empty result set

- **WHEN** an internal operator searches and no chunks exist
- **THEN** the response is `200` with an empty `results` list

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

### Requirement: LLM-generated inquiry answer

The service SHALL generate the `response` field of `/admin/chat` using the local
Ollama model `llama3.2:3b` over the retrieved sources.

- The answer MUST be concise and MUST NOT include greetings or filler.
- The answer MUST use a JARVIS-like tone and address the user by the configured
  `CODE_NAME` (the LLM's name).
- If Ollama is unavailable, the service MUST still return `200` with the
  retrieved `sources` and a `response` indicating the answer could not be
  generated.

#### Scenario: Concise JARVIS-style answer

- **WHEN** an authenticated user inquires and sources are retrieved
- **THEN** `response` is a concise answer with no greeting, addressing the user
  by `CODE_NAME`

#### Scenario: Ollama unavailable

- **WHEN** Ollama cannot be reached during inquiry
- **THEN** the response is `200` with sources and a fallback `response`

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

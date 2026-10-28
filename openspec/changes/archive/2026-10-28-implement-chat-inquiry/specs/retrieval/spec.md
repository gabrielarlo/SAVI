# Spec Delta

## ADDED Requirements

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

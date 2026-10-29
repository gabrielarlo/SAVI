# Spec Delta

## MODIFIED Requirements

### Requirement: Admin voice chat

The service SHALL expose `POST /admin/chat/voice` for authenticated console
users to inquire over stored documents by voice.

- The request MUST accept an audio upload (multipart form data) and an optional
  `tenant_id`.
- The audio MUST be transcribed to text using the configured faster-whisper
  model before retrieval.
- An administrator (admin secret or administrator session) MAY omit `tenant_id`
  to inquire across all tenants; when `tenant_id` is supplied, only that
  tenant's chunks are considered.
- An account manager (account_manager session) MUST supply a non-null
  `tenant_id`; a request without one MUST be rejected with `400`.
- The query MUST filter on `chunks.tenant_id` at the database layer whenever a
  tenant scope is applied.
- Retrieval MUST return relevant chunks for the applied scope, including
  "All accounts", rather than an arbitrary first N chunks: match transcript
  tokens against chunk content (case-insensitive), and fall back to the most
  recent scoped chunks when no token matches.
- The assistant answer MUST be generated over the retrieved sources using the
  configured chat model.
- The answer MUST be synthesized to audio using the configured Ollama
  text-to-speech model.
- The response MUST be JSON with `tenant_id`, `transcript`, `response`,
  `sources`, and `audio` (base64-encoded audio, or null when synthesis is
  unavailable).
- `sources` MUST contain only chunks visible under the applied scope.
- The route MUST require an authenticated admin/console user; tenant API keys
  MUST NOT authorize it.

#### Scenario: Administrator voice inquiry across tenants

- **WHEN** an administrator uploads audio while chunks exist for tenants A and B
- **THEN** the response is `200` and `sources` may include chunks from both tenants

#### Scenario: Administrator voice inquiry scoped to one tenant

- **WHEN** an administrator uploads audio with a `tenant_id`
- **THEN** every entry in `sources` belongs to that tenant

#### Scenario: Tenant API key cannot use admin voice chat

- **WHEN** a request authenticated with a tenant API key calls `/admin/chat/voice`
- **THEN** the service responds `401` with message `Internal admin access required`

#### Scenario: All-accounts voice inquiry returns relevant chunks

- **WHEN** an administrator selects "All accounts" and asks by voice about a
  term present in a non-first chunk
- **THEN** the response includes that chunk among `sources`
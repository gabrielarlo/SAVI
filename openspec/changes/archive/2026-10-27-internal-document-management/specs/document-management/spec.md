# Spec Delta

## Purpose

Gives internal operators read and lifecycle control over stored documents: see
what exists, inspect how it was chunked, delete it, and re-process it after a
chunking or embedding change.

## ADDED Requirements

### Requirement: List documents

The service SHALL expose `GET /admin/documents` for internal operators.

- The response MUST be a JSON array of
  `{"id", "tenant_id", "title", "created_at", "chunk_count"}`.
- `chunk_count` MUST be the number of chunks stored for that document.
- An optional `tenant_id` query parameter MUST restrict results to that tenant.
- Results MUST be ordered newest first by `created_at`.

#### Scenario: List all documents

- **WHEN** an internal operator requests `/admin/documents` while documents exist for two tenants
- **THEN** the response contains every document, each with its `tenant_id` and `chunk_count`

#### Scenario: Filter by tenant

- **WHEN** an internal operator requests `/admin/documents?tenant_id=<tenant A>`
- **THEN** only tenant A's documents are returned

#### Scenario: No documents

- **WHEN** no documents exist
- **THEN** the response is `200` with an empty array

#### Scenario: Non-admin caller

- **WHEN** a request authenticated with a tenant API key requests `/admin/documents`
- **THEN** the service responds `401` with message `Internal admin access required`

### Requirement: Read a document with its chunks

The service SHALL expose `GET /admin/documents/{id}` returning the document and
its chunks ordered by `chunk_index`.

- The response MUST include `id`, `tenant_id`, `title`, `content`, `created_at`,
  and `chunks` as an array of `{"id", "chunk_index", "content"}`.

#### Scenario: Document found

- **WHEN** an internal operator requests an existing document id
- **THEN** the response is `200` and `chunks` are ordered by ascending `chunk_index`

#### Scenario: Document missing

- **WHEN** an internal operator requests an id that does not exist
- **THEN** the service responds `404` with the standard error envelope

### Requirement: Delete a document

The service SHALL expose `DELETE /admin/documents/{id}`.

- Deleting a document MUST also delete all of its chunks.
- The response MUST be `{"document_id": <id>, "status": "deleted"}`.

#### Scenario: Delete removes chunks

- **WHEN** an internal operator deletes a document that has chunks
- **THEN** the response is `200` and a later request for that document returns `404`

#### Scenario: Deleting a missing document

- **WHEN** an internal operator deletes an id that does not exist
- **THEN** the service responds `404` with the standard error envelope

### Requirement: Re-ingest a document

The service SHALL expose `POST /admin/documents/{id}/reingest` to rebuild a
document's chunks from its stored content using the current chunking rules.

- Existing chunks for that document MUST be replaced, not appended.
- Each new chunk MUST be sent for embedding exactly as on first ingestion.
- The response MUST be `{"document_id": <id>, "status": "reingested", "chunks": <count>}`.

#### Scenario: Re-ingest replaces chunks

- **WHEN** an internal operator re-ingests a document
- **THEN** the document's chunk rows are rebuilt and their `chunk_index` values start at `0`

#### Scenario: Re-ingest a missing document

- **WHEN** an internal operator re-ingests an id that does not exist
- **THEN** the service responds `404` with the standard error envelope

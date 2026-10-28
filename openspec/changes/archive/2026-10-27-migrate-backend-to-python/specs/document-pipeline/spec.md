# Spec Delta

## Purpose

Turns an uploaded document into stored, chunk-indexed records for a single tenant
and requests an embedding for each chunk from the configured Ollama service.

## ADDED Requirements

### Requirement: Document ingestion

The service SHALL expose `POST /admin/documents` for internal operators to store a
document for a named tenant.

- The request body is `{"tenant_id": <string>, "title": <string>, "content": <string>}`.
- The document MUST be persisted in `documents` with a generated UUID id and the
  supplied tenant id, title, and content.
- The response MUST be `{"document_id": <uuid>, "status": "ingested"}`.

#### Scenario: Ingest a document

- **WHEN** an internal operator posts a document for an existing tenant
- **THEN** the document row is created and the response reports its id with status `ingested`

#### Scenario: Document is scoped to the named tenant

- **WHEN** a document is ingested for tenant A
- **THEN** the stored document and all of its chunks carry tenant A's id

### Requirement: Word-window chunking

The service SHALL split document content into chunks of at most 500 words with 50
words of overlap between consecutive chunks, preserving word order.

- Text is split on whitespace; empty or whitespace-only content produces no chunks.
- Content of 500 words or fewer produces exactly one chunk.
- Each stored chunk MUST record its zero-based position in `chunks.chunk_index`.

#### Scenario: Long content produces overlapping chunks

- **WHEN** content of 1000 words is ingested
- **THEN** the first chunk holds words 1-500, the second begins at word 451, and no chunk exceeds 500 words

#### Scenario: Empty content

- **WHEN** content is empty or whitespace only
- **THEN** the document is stored and no chunk rows are created

#### Scenario: Chunk indices are sequential

- **WHEN** a document produces multiple chunks
- **THEN** `chunk_index` values are `0, 1, 2, ...` in document order

### Requirement: Per-chunk embedding request

For every chunk the service SHALL request an embedding from the configured Ollama
endpoint using the `nomic-embed-text` model.

- An embedding failure MUST NOT fail the ingestion request; the chunk is still
  stored and the response still reports `ingested`.
- Embedding vectors are not persisted to Qdrant by this change; behaviour is
  unchanged from the pre-migration implementation.

#### Scenario: Ollama unreachable

- **WHEN** the Ollama endpoint is unavailable during ingestion
- **THEN** ingestion still succeeds, chunks are stored, and the response is `200` with status `ingested`

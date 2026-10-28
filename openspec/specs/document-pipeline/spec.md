# document-pipeline Specification

## Purpose

Turns an uploaded document into stored, chunk-indexed records for a single tenant
and requests an embedding for each chunk from the configured Ollama service.

## Requirements

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

### Requirement: File upload ingestion

The service SHALL expose `POST /admin/documents/upload` accepting a multipart
form with `tenant_id`, an optional `title`, and one `file`.

- Accepted file types are `.txt`, `.md`, and `.pdf`.
- The uploaded file MUST be limited to 10 MB; a larger file MUST be rejected with
  `413` and the standard error envelope.
- A file with any other extension MUST be rejected with `415` and the standard
  error envelope.
- Extracted text MUST be stored as the document content and processed with the
  same chunking and embedding rules as JSON ingestion.
- When `title` is omitted, the file name without its extension MUST be used.
- The response MUST be `{"document_id": <uuid>, "status": "ingested", "chunks": <count>}`.

#### Scenario: Upload a text file

- **WHEN** an internal operator uploads a `.txt` file for an existing tenant
- **THEN** the response is `200` with `status` `ingested` and the document's content equals the file's text

#### Scenario: Upload a PDF

- **WHEN** an internal operator uploads a `.pdf` file containing selectable text
- **THEN** the extracted text is chunked and stored for the named tenant

#### Scenario: Unsupported type

- **WHEN** an internal operator uploads a `.docx` file
- **THEN** the service responds `415` and stores nothing

#### Scenario: Oversized file

- **WHEN** an internal operator uploads a file larger than 10 MB
- **THEN** the service responds `413` and stores nothing

### Requirement: PDF text extraction

PDF uploads SHALL be converted to text by reading every page in order.

- Pages MUST be concatenated in document order, separated by a newline.
- A PDF with no extractable text (for example a scanned image) MUST still store
  the document, with zero chunks, and respond `200`.

#### Scenario: Scanned PDF

- **WHEN** an internal operator uploads a PDF whose pages contain no text layer
- **THEN** the document is stored with empty content and no chunk rows, and the response is `200`

### Requirement: Text file decoding

Plain text and Markdown uploads SHALL be decoded as UTF-8, replacing invalid byte
sequences rather than failing the request.

#### Scenario: Non-UTF-8 bytes

- **WHEN** an uploaded `.txt` file contains invalid UTF-8 bytes
- **THEN** the document is stored with the replacement characters and the request succeeds

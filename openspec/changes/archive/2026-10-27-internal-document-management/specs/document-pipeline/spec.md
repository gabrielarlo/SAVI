# Spec Delta

## ADDED Requirements

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

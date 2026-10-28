# Spec Delta

## Purpose

Provides internal operators with a browser interface for managing documents —
sign in, see what is stored, upload files, inspect chunks, and delete — built on
the TailAdmin free template and served by the same FastAPI process.

## ADDED Requirements

### Requirement: UI delivery

The service SHALL serve the built admin interface at `/console/documents` and
MUST redirect `GET /` there.

- The sign-in page MUST be served at `/console/signin`.
- `/console` and `/console/` MUST redirect to `/console/documents`.
- Static assets MUST be served under `/console/`.

- The interface MUST be the built output of the vendored TailAdmin free
  template; no TailAdmin Pro assets or components may be used.
- The template's MIT licence and attribution MUST remain in the repository.
- Static assets MUST be served without authentication; all data MUST come from
  the admin JSON API, which enforces authentication.

#### Scenario: Landing redirect

- **WHEN** a browser requests `/`
- **THEN** it is redirected to `/console/documents`

#### Scenario: UI assets load

- **WHEN** a browser requests `/console/documents` without credentials
- **THEN** the sign-in page loads and no document data is present in the response

### Requirement: Sign-in with the admin secret

The interface SHALL require the admin secret before showing document data.

- The secret MUST be validated by calling an admin endpoint; a `401` MUST be
  shown as an error and MUST NOT be stored.
- A validated secret MUST be kept in `sessionStorage` only — never in
  `localStorage` or a cookie — and MUST be sent as `X-Admin-Secret` on API calls.
- Signing out MUST clear the stored secret.

#### Scenario: Wrong secret

- **WHEN** an operator enters an incorrect secret
- **THEN** the page shows the API error message and remains on the sign-in view

#### Scenario: Secret not persisted across browser sessions

- **WHEN** the browser tab is closed and the UI is reopened
- **THEN** the operator is asked to sign in again

### Requirement: Documents table

The interface SHALL list documents from `GET /admin/documents`.

- Columns MUST show title, tenant name, chunk count, and creation time.
- The tenant column MUST show the tenant's name, never its raw id; names are
  resolved from `GET /admin/tenants`.
- When two tenants share a name, the display MUST disambiguate them without
  falling back to the full id.
- A tenant filter MUST narrow the list using the `tenant_id` query parameter.
- The table MUST show an explicit empty state when no documents match.

#### Scenario: List reflects stored documents

- **WHEN** an operator opens the documents page after ingestion
- **THEN** every stored document appears with its tenant name and chunk count

#### Scenario: Tenant ids stay out of the interface

- **WHEN** a document belongs to a tenant with a display name
- **THEN** the table and the chunk preview show that name, and no raw tenant id appears

#### Scenario: Filter by tenant

- **WHEN** an operator selects a tenant in the filter
- **THEN** only that tenant's documents are listed

### Requirement: Upload form

The interface SHALL let an operator upload a document through
`POST /admin/documents/upload`.

- The form MUST require a tenant, chosen from `GET /admin/tenants`.
- The file picker MUST accept only `.txt`, `.md`, and `.pdf`.
- The submit control MUST be disabled while an upload is in flight.
- On success the table MUST refresh; on failure the API error message MUST be
  displayed without losing the form's values.

#### Scenario: Successful upload

- **WHEN** an operator selects a tenant, chooses a `.pdf` file, and submits
- **THEN** the new document appears in the table without a page reload

#### Scenario: Rejected upload

- **WHEN** the API rejects an upload with `415` or `413`
- **THEN** the form shows the returned message and the table is unchanged

### Requirement: Chunk preview and deletion

The interface SHALL let an operator inspect a document's chunks and delete it.

- Opening a document MUST fetch `GET /admin/documents/{id}` and display each
  chunk's index and content.
- Deletion MUST require an explicit confirmation before calling
  `DELETE /admin/documents/{id}`, and MUST remove the row on success.
- Document and chunk text MUST be rendered as text, never as HTML.

#### Scenario: Inspect chunks

- **WHEN** an operator opens a document that has three chunks
- **THEN** the three chunks are shown in ascending index order

#### Scenario: Delete requires confirmation

- **WHEN** an operator clicks delete and cancels the confirmation
- **THEN** no request is sent and the document remains

#### Scenario: Script in content stays inert

- **WHEN** a document contains `<script>` markup
- **THEN** the chunk preview shows it as literal text and no script executes

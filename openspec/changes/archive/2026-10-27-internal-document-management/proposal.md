# Proposal

## Why

Internal operators can only create documents by hand-posting raw JSON, and they
cannot see what exists, inspect chunks, delete a bad document, or re-process one
after a chunking change. `AGENTS.md` promises an internal document management
interface; today there is only `POST /admin/documents`. Real source files also
have to be pasted as text, so PDFs cannot be ingested at all.

## What Changes

- Add the missing admin JSON endpoints: list documents (optionally per tenant),
  read one document with its chunks, delete a document, and re-ingest a document
  (replace its chunks and embeddings).
- Add `POST /admin/documents/upload` accepting multipart `.txt`, `.md`, and
  `.pdf` files, extracting text (pypdf for PDFs) and running the existing
  chunking and embedding pipeline.
- Add an internal admin UI built on **TailAdmin free** (HTML + Tailwind CSS +
  Alpine.js, MIT) and served by the FastAPI app at `/console/documents`: sign-in with the
  admin secret, a documents table with tenant filter, upload form, chunk preview,
  and delete confirmation.
- Vendor TailAdmin free v2.4.0 under `ui/` and build it in a Docker node stage;
  the Python runtime image only receives the built `dist/`.
- Record in `AGENTS.md` that the UI uses TailAdmin free and that TailAdmin Pro
  components are not to be used.
- No database schema change: uploaded text is stored in the existing
  `documents.content` column.

## Capabilities

### New Capabilities

- `document-management`: list, inspect, delete, and re-ingest documents through
  the admin API, with tenant filtering and admin-only access.
- `admin-ui`: the browser interface served at `/console/documents`, its sign-in flow,
  document table, upload form, and the TailAdmin-free constraint.

### Modified Capabilities

- `document-pipeline`: adds file-upload ingestion and PDF text extraction on top
  of the existing JSON ingestion, chunking, and embedding behaviour.
- `tenant-api`: adds `GET /admin/tenants` so the UI can populate its tenant
  selector; API keys are never returned by that endpoint.

## Impact

- `app/routes.py`: five new admin routes (list, detail, delete, re-ingest,
  upload) alongside the existing ones.
- `app/services.py`: text extraction for `.txt`/`.md`/`.pdf` and a shared
  ingest helper reused by JSON ingest, upload, and re-ingest.
- `requirements.txt`: adds `python-multipart` (form parsing) and `pypdf` (PDF
  text extraction).
- New `ui/` tree (vendored TailAdmin free, MIT licence and attribution kept),
  `ui/src/pages/.../documents.html`, and a `ui/src/js/documents.js` API client.
- `app/main.py`: mounts the built UI as static files and redirects `/` to it.
- `Dockerfile`: adds a `node:22-alpine` build stage; final image unchanged in
  kind (Python only).
- `AGENTS.md`: documents the UI stack and the free-only TailAdmin rule.
- Unchanged: existing JSON ingest, tenant API, chat, search, schema, and the
  SQLite/Qdrant compose services.

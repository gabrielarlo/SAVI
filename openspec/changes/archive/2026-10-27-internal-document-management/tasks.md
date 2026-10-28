# Tasks

## 1. Document API

- [x] 1.1 Add `GET /admin/tenants` returning `id`, `name`, `created_at` and never `api_key`; verify tests cover the list, the absence of key fields, and `401` for a tenant credential
- [x] 1.2 Extract `ingest_document(db, tenant_id, title, content, ollama_url)` in `app/services.py` and rewire `POST /admin/documents` to it; verify the existing suite still passes unchanged
- [x] 1.3 Add `GET /admin/documents` with `chunk_count` via `LEFT JOIN ... GROUP BY`, newest-first ordering, and an optional `tenant_id` filter; verify tests cover all, filtered, empty, and `401`
- [x] 1.4 Add `GET /admin/documents/{id}` returning the document plus chunks ordered by `chunk_index`; verify tests cover a found document and a `404` envelope for a missing id
- [x] 1.5 Add `DELETE /admin/documents/{id}` returning `{"document_id", "status": "deleted"}`; verify a test asserts the chunks are gone and that a second delete returns `404`
- [x] 1.6 Add `POST /admin/documents/{id}/reingest` that deletes existing chunks and rebuilds them through the shared helper; verify a test asserts chunk indices restart at `0`, the old chunk ids are gone, and a missing id returns `404`

## 2. File uploads

- [x] 2.1 Add `python-multipart` and `pypdf` to `requirements.txt`; verify `pip install -r requirements.txt` succeeds in `python:3.12-slim`
- [x] 2.2 Implement `extract_text(filename, data)` for `.txt`, `.md`, and `.pdf` (pypdf pages joined with newlines, UTF-8 decode with replacement); verify tests cover a text file, a non-UTF-8 text file, a PDF fixture with selectable text, and a text-less PDF returning an empty string
- [x] 2.3 Add `POST /admin/documents/upload` (multipart `tenant_id`, optional `title`, `file`) rejecting unsupported extensions with `415` and files over 10 MB with `413`; verify tests cover a successful `.txt` upload, the filename-derived title, both rejections, and that rejected uploads store nothing

## 3. Admin UI

- [x] 3.1 Vendor TailAdmin free v2.4.0 into `ui/` (keep `LICENSE`, `README.md`, `package-lock.json`, webpack/postcss config, `src/css`, `src/js`, `src/images`, layout and common partials; delete demo pages for charts, calendar, profile, forms, and UI elements); verify `npm ci && npm run build` succeeds in `node:22-alpine` and emits `build/`
- [x] 3.2 Author `ui/src/pages/(admin-layout)/(main)/index.html` and the sign-in page on the template layout, and trim the sidebar to the documents link; verify both pages are present in `build/` after a build
- [x] 3.3 Write `ui/src/js/documents.js` (API client with `X-Admin-Secret`, `sessionStorage` sign-in and sign-out, table with tenant filter, upload form, chunk modal, delete confirmation, `textContent` rendering); verify it is bundled into `build/` and that no `innerHTML` assignment carries document data
- [x] 3.4 Add the `node:22-alpine` build stage to `Dockerfile` and copy `build/` into the Python image; verify `docker compose build app` succeeds and `docker compose run --rm app ls /app/ui/build/index.html` lists the file
- [x] 3.5 Serve the console at `/console/documents` and `/console/signin` with assets under `/console/`, redirecting `/`, `/console`, and `/console/` to the documents page, and mount nothing when `ui/build` is absent; verify tests cover the redirects, page and asset serving, and that the app still imports and serves the API without a built UI

## 4. Documentation

- [x] 4.1 Update `AGENTS.md` with the UI stack, the `ui/` layout, the Docker build stage, the new endpoints, and an explicit rule that only TailAdmin free is used (no Pro components or assets); verify it contains no Pro component guidance and names the vendored version

## 5. Verification

- [x] 5.1 Run the full suite in Docker and confirm every test passes
- [x] 5.2 Build and start the stack, then walk the UI manually: wrong secret shows an error, correct secret lists documents, a `.txt` and a `.pdf` upload appear in the table, the tenant filter narrows the list, the chunk preview shows indices, cancelling delete keeps the row, confirming delete removes it, and a document containing `<script>` renders as text; record the result in the change summary
- [x] 5.3 Smoke test the new endpoints with `curl` — tenant list, document list, detail, re-ingest, delete, `415` for a `.docx`, and `413` for an oversized file — and confirm each returns the documented status and body

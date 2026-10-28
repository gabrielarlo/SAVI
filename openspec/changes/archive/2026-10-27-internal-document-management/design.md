# Design

## Context

See `proposal.md` for motivation. The service is a FastAPI app (`app/`) with four
routes, stdlib `sqlite3`, and pytest coverage; the existing specs are
`tenant-api`, `document-pipeline`, `retrieval`, and `service-configuration`.

Relevant facts discovered while planning:

- `documents` has `id, tenant_id, title, content, created_at`; `chunks` has
  `document_id` with `ON DELETE CASCADE`, so deleting a document already removes
  its chunks at the database layer (foreign keys are enabled per connection).
- There is no endpoint to list tenants, so the UI cannot populate a tenant
  selector without one.
- TailAdmin free (v2.4.0, MIT) is an HTML + Tailwind CSS + Alpine.js template
  built with webpack 5. Its pages live in `src/pages/**` and use
  `<include src="./partials/...">` directives that only resolve during
  `npm run build`, which emits `build/`. There is no published prebuilt CSS, so a
  build step is unavoidable.

## Goals / Non-Goals

**Goals:**

- Full document lifecycle through the admin API, reusing one ingestion path.
- Text and PDF uploads without adding a system dependency (pure-Python pypdf).
- A working TailAdmin-based UI served by the same process, with no runtime Node.
- Every new behaviour covered by pytest, except browser-only rendering.

**Non-Goals:**

- Editing document content, versioning, or bulk operations.
- User accounts or server-side sessions; the UI uses the existing shared admin
  secret.
- TailAdmin Pro components, a SPA framework, or replacing the template's
  build with a custom one.
- Qdrant writes or vector search.

## Decisions

**Vendor TailAdmin free v2.4.0 under `ui/`, trimmed to the pages we use.** The
template is copied in (MIT `LICENSE` and `README` attribution kept), demo pages
for charts, calendar, profile, forms, and UI elements are deleted, and two pages
remain: `signin.html` and `index.html` (the documents page). Trimming pages is safe because
webpack only emits pages found under `src/pages/`; the JS entry stays untouched
so no library import has to be untangled. Alternative rejected: the React/Next
TailAdmin variant — it would add a JS runtime and a second app to deploy.

**Build the UI in a Docker node stage.** `Dockerfile` gains
`FROM node:22-alpine AS ui`, runs `npm ci && npm run build`, and the Python image
copies only `build/`. The dependency layer is keyed on `ui/package-lock.json`, so
UI rebuilds only happen when the lockfile changes. Alternative rejected:
committing `dist/` — stale artifacts and a build step nobody can reproduce.

**Serve at `/console/documents`, assets under `/console/`.** The JSON API keeps
`/admin/*`, so the console gets its own namespace: `/console/documents` and
`/console/signin` are routes returning the built pages, `/console`, `/console/`
and `/` redirect to the documents page, and `StaticFiles` is mounted at
`/console` so `style.css`, `bundle.js`, and `images/` resolve relative to the
page URL. The routes are registered before the mount so they win; everything is
added only when the built directory exists, which keeps pytest and the API-only
image working without Node.

**One ingestion helper, three callers.** `app/services.py` gets
`ingest_document(db, tenant_id, title, content, ollama_url)` returning
`(document_id, chunk_count)`; the existing JSON route, the upload route, and
re-ingest all call it. Re-ingest deletes the document's chunks first, inside the
same transaction, so a failure cannot leave a half-chunked document.

**Uploads validated before extraction.** The route checks the extension against
`{.txt, .md, .pdf}` (else `415`) and the byte length against a 10 MB constant
(else `413`) before reading text, so a bad upload never touches the database.
`extract_text(filename, data)` returns the text: `data.decode("utf-8",
errors="replace")` for text, and pypdf's per-page `extract_text()` joined with
newlines for PDFs.

**List uses a single aggregate query.** `LEFT JOIN chunks ... GROUP BY d.id`
gives `chunk_count` without N+1 queries; the tenant filter is a bound parameter.

**UI authentication is client-side, with the existing secret.** A sign-in form
validates the secret against `GET /admin/tenants` and stores it in
`sessionStorage`; every fetch sends `X-Admin-Secret`. No cookie, no session
table, no second auth mechanism. Because a stolen secret is already a full
compromise, the added risk is limited to XSS — mitigated by rendering document
and chunk text with `textContent`, never `innerHTML`.

**`documents.js` is the only custom JS.** It holds the API client, table
rendering, filter, upload, chunk modal, and delete confirmation, using the
template's existing Tailwind classes and Alpine-free plain DOM code.

## Risks / Trade-offs

- **Vendored template drift** → pin v2.4.0 and treat upgrades as a separate
  change; the trimmed page set is documented in `AGENTS.md`.
- **npm build needs the network and ~1-2 minutes on a cold cache** → layer is
  cached on `package-lock.json`; a rebuild of application code does not rebuild
  the UI.
- **PDF extraction is best-effort** → scanned PDFs store zero chunks by design
  and are reported as ingested; surfaced to the user via the chunk count.
- **Uploads are read fully into memory** → capped at 10 MB, fine for an internal
  tool; stream to disk if the cap ever rises.
- **Browser behaviour is not covered by pytest** → the redirect, static serving,
  and every API call the UI makes are tested; the visual walkthrough is a
  documented manual checklist in the tasks.
- **Secret in `sessionStorage`** → tab-scoped and cleared on sign-out; no
  persistent storage.
- **`npm ci` still installs the template's unused chart/map/calendar packages**
  (~200 MB of `node_modules`, cached in the Docker layer) → the JS entry was
  trimmed, so none of them reach the bundle; pruning `package.json` means
  regenerating the lockfile and is a separate cleanup.

## Migration Plan

1. Ship the backend endpoints and uploads first; they are additive and safe to
   deploy alone.
2. Vendor and build the UI, mount it, verify the walkthrough.
3. Update `AGENTS.md`.
4. Rollback: revert the commit. No schema change and no data migration are
   involved, so an older image reads the same database.

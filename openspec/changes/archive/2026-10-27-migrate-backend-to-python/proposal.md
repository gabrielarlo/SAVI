# Proposal

## Why

Rust builds for this service take far longer than the change-fix-verify loop the
project needs: a cold `docker compose build` spends ~2 hours compiling ~340
crates on a 16 GB Docker Desktop VM, and the daemon has repeatedly dropped
mid-build. The project is a small, single-service RAG API; the compile cost buys
runtime performance the workload does not need. Python with FastAPI starts in
under a second, needs no compile step, and keeps the existing HTTP contract.

## What Changes

- **BREAKING** Replace the Rust/axum backend with a Python/FastAPI backend that
  serves the same HTTP surface (`POST /admin/tenants`, `POST /admin/documents`,
  `POST /admin/search`, `POST /api/v1/chat`), the same auth headers
  (`X-Admin-Secret`, `X-API-Key`), and the same JSON request/response shapes.
- **BREAKING** Delete the Rust sources and toolchain files: `src/`, `Cargo.toml`,
  `Cargo.lock`, and `src/bin/test_ollama.rs`.
- Reimplement the four existing behaviours in Python: tenant creation with a
  generated API key, document ingestion with word-window chunking and Ollama
  embeddings, internal global search, and tenant-scoped chat.
- Replace the multi-stage Rust Dockerfile with a single-stage Python image that
  installs dependencies from `requirements.txt`; drop the `ENV`-conditional
  debug/release build and the cargo cache mounts, which no longer apply.
- Keep SQLite as the datastore and keep `migrations/20261026000000_init.sql` as
  the schema source of truth, applied at startup.
- Rewrite `AGENTS.md` to describe the Python stack, removing the Rust language,
  toolchain, and code-standard guidance.
- Replace the Rust tests with `pytest` tests covering config defaults/overrides,
  the SQLite migration smoke test, chunking, and the authenticated API routes.

## Capabilities

### New Capabilities

- `tenant-api`: header-based authentication (internal admin secret vs. tenant API
  key), role enforcement per route, and tenant creation with a generated key.
- `document-pipeline`: document ingestion, word-window chunking, and Ollama
  embedding retrieval for each chunk.
- `retrieval`: tenant-scoped chat over a tenant's own chunks and internal
  cross-tenant search, with strict tenant isolation on every query.
- `service-configuration`: environment-driven configuration (`PORT`,
  `DATABASE_URL`, `QDRANT_URL`, `OLLAMA_URL`, `ADMIN_SECRET`, `ENV`) with the
  documented defaults.

### Modified Capabilities

None. `openspec/specs/` is empty, so there are no existing requirements to amend.

## Impact

- Removed: `src/**`, `Cargo.toml`, `Cargo.lock`, the Rust builder stage, and the
  cargo cache mounts and `ENV` build arg in `Dockerfile`/`docker-compose.yml`.
- Added: `app/` (FastAPI application), `requirements.txt`, `tests/`, `pytest.ini`
  or `pyproject.toml` test config.
- Unchanged: `migrations/20261026000000_init.sql`, the SQLite and Qdrant compose
  services, the published port, and the request/response contract.
- `AGENTS.md`: Rust architecture, standards, and toolchain sections replaced with
  Python equivalents; multi-tenancy and security rules retained.
- Behavioural gap carried over unchanged from the Rust version: chunk embeddings
  are requested from Ollama but not written to Qdrant, and chat/search return
  SQL matches rather than vector search. This change ports the current behaviour;
  it does not add vector search.

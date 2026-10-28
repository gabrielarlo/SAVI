# Design

## Context

See `proposal.md` for motivation. The starting point is a working Rust/axum
service whose behaviour is captured in this change's specs. Two facts about the
current code shape the port:

- `src/config.rs` currently fails to compile: the first test lost its closing
  brace during an earlier edit. The Rust tree is being deleted, so this is not
  repaired; the pytest suite replaces it.
- The `qdrant-client` dependency is constructed at startup and never used:
  embeddings are requested from Ollama and discarded, and retrieval is plain SQL.
  The port keeps that behaviour rather than inventing vector search.

Constraints: Docker-only execution (no host Python toolchain required), SQLite
as the datastore, the existing HTTP contract preserved, and
`migrations/20261026000000_init.sql` kept as the schema source of truth.

## Goals / Non-Goals

**Goals:**

- Same routes, headers, status codes, and JSON bodies as the Rust service.
- No compile step: image build is dependency install only; cold build in under a
  minute on the same machine that took ~2 hours for Rust.
- Startup applies the existing SQL migration idempotently.
- Behaviour is covered by tests that run without Qdrant or Ollama.

**Non-Goals:**

- Vector search, Qdrant writes, or LLM-generated answers. The current code
  returns SQL matches with a fixed response string; so does the port.
- Auth redesign (JWT, key rotation, hashing API keys at rest).
- Schema changes; the migration file is reused as-is.
- Frontend work.

## Decisions

**FastAPI + uvicorn over Flask/Django.** The axum service is async and validates
JSON bodies; FastAPI gives the same shape (pydantic request models, dependency
injection for auth, async handlers) with two dependencies and no settings module.
Flask would need manual validation; Django is far more framework than four routes.

**Sync `def` handlers with stdlib `sqlite3`.** FastAPI runs `def` handlers in a
threadpool, so blocking `sqlite3` calls never block the event loop. This avoids
SQLAlchemy and aiosqlite for four queries. Each request opens its own short-lived
connection with `PRAGMA foreign_keys=ON`; SQLite handles the concurrency, and the
pattern keeps tenant filtering explicit in the SQL string.
Alternative rejected: async SQLAlchemy — a much larger dependency surface for no
behavioural gain here.

**`httpx` for Ollama.** One POST to `/api/embeddings` with the same
`{"model": "nomic-embed-text", "prompt": ...}` payload. Failures are logged and
swallowed so ingestion stays `ingested`, matching the Rust `unwrap_or_default`.

**Auth as a FastAPI dependency, not middleware.** One `require_admin` and one
`require_tenant` dependency replace the axum middleware's role branching. Each
returns a role object (`AdminRole` or `TenantRole(tenant_id)`), so a route cannot
forget the check: it is in the signature. The 401 messages stay byte-identical to
the current ones. A shared exception handler renders the
`{"error": {"code", "message"}}` envelope for both `HTTPException` and unhandled
errors.

**Startup migration via lifespan.** Read `migrations/20261026000000_init.sql` and
`executescript` it against the database on startup. The file already uses
`CREATE TABLE IF NOT EXISTS`, so restart is safe and no migration-tracking table
is needed for a single migration.

**`DATABASE_URL` stays in URL form.** Strip the `sqlite://` prefix to get a file
path and create parent directories, so the existing `.env`, compose environment,
and docs keep working unchanged.

**Drop `qdrant-client`; keep `QDRANT_URL`.** The setting remains in the config
contract and the compose service stays, so adding real vector search later needs
no config change. Nothing imports a Qdrant client.

**Six application modules.** `app/main.py` (app, lifespan, error handler),
`app/config.py`, `app/db.py` (connect + migrate), `app/auth.py`, `app/services.py`
(chunker + embeddings), `app/routes.py` (all four endpoints). Small enough that
per-route modules would be indirection.

**Single-stage Docker image.** `python:3.12-slim`, `pip install -r
requirements.txt`, copy `app/` and `migrations/`. The cargo registry/target cache
mounts, the `ARG ENV` build branch, and the debug/release split all disappear;
`ENV` stays a runtime variable. `PYTHONUNBUFFERED=1` and
`PIP_NO_CACHE_DIR=1` keep logs live and the layer small.

**Tests with pytest + FastAPI TestClient.** In-memory or temp-file SQLite per
test, `ADMIN_SECRET` overridden via monkeypatch, `httpx` mocked for embeddings.
This directly covers the four specs and replaces the two Rust tests.

## Risks / Trade-offs

- **Behaviour drift while porting** → port each endpoint against its spec
  scenarios, and keep the request/response assertions in `tests/test_api.py`
  explicit about JSON shape, not just status codes.
- **Blocking calls under load** → threadpool handlers cap concurrency at
  FastAPI's default 40 threads. Acceptable for an internal service; move to
  async SQLAlchemy if throughput ever matters.
- **API keys stored in plaintext** → unchanged from the Rust service; hashing
  would break the "return the key once" contract and is out of scope.
- **SQLite write contention** → single-file database with short transactions;
  fine at this scale, revisit with Postgres if ingestion becomes concurrent.
- **Losing Rust runtime performance** → the service does four small queries per
  request; Python's overhead is irrelevant next to the Ollama embedding call.
- **Unused Qdrant service still running** → keep it; removing it is a one-line
  compose change once vector search lands or is dropped for good.

## Migration Plan

1. Add `app/`, `requirements.txt`, and `tests/` alongside the Rust tree.
2. Run `pytest` and `docker compose build` against the new app; confirm the
   image builds and starts.
3. Delete `src/`, `Cargo.toml`, `Cargo.lock`; rewrite `Dockerfile` and the `app`
   service build block in `docker-compose.yml`; update `AGENTS.md`.
4. Smoke test the four routes with `curl` against `docker compose up`.
5. Rollback: `git revert` the migration commit — the SQLite volume and migration
   file are untouched, so the Rust service reads the same data.

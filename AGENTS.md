# LocalRAG Development Guidelines & Architecture

Welcome to **LocalRAG**! This document outlines the core architecture, design principles, technology stack, and contribution guidelines for the project.

---

## 1. Project Overview & Requirements

LocalRAG is a robust, secure, containerized Retrieval-Augmented Generation (RAG) system built in **Python**. It provides:
- **Multi-Tenant / Account Scoping**: Data, documents, and chat/FAQ endpoints are strictly isolated by tenant/account identifiers.
- **Internal Document Management UI**: An interface for internal users to upload, manage, chunk, and vectorize documents. Internal users also have rights to perform global searches across all accounts or tenant-scoped searches.
- **External FAQ / Chatbot Endpoint**: Secure API endpoints for external clients/chatbots, scoped strictly by tenant/account credentials (API keys).
- **Dockerized Deployment**: Fully containerized using `docker-compose` for local and staging environments, running the API service and the vector database (Qdrant).

---

## 2. Technology Stack

- **Language**: Python 3.12.
- **Web Framework**: FastAPI, served by uvicorn. Request bodies are validated with pydantic models; authentication is a FastAPI dependency.
- **Datastore**: SQLite through the standard-library `sqlite3` module, with schema in `migrations/`.
- **Vector Database**: Qdrant (running in compose; not yet queried by the application).
- **Embeddings & LLM Integration**: `httpx` calls to a local Ollama instance (`nomic-embed-text`).
- **Tests**: `pytest` with FastAPI's `TestClient`.
- **Admin UI**: the TailAdmin **free** HTML template (v2.4.0, MIT) — plain HTML +
  Tailwind CSS v4 + Alpine.js, bundled by webpack. See section 6.
- **Containerization**: Docker & Docker Compose. Nothing runs on the host.

---

## 3. Architecture & Data Flow

```
┌────────────────────────────────────────────────────────┐
│                   Internal Users                       │
│        (Document Management & Global Search)           │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                   External Clients                     │
│         (Tenant-Scoped FAQ / Chatbot API)              │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│              FastAPI Service (app/)                    │
│     - Auth & Tenant Scoping (X-Admin-Secret / X-API-Key)│
│     - Document Ingestion & Chunking Pipeline           │
│     - RAG Context Retrieval Orchestration              │
└──────┬───────────────────────────────────┬─────────────┘
       │                                   │
       ▼                                   ▼
┌──────────────┐                 ┌───────────────────────┐
│ SQLite       │                 │ Local LLM / Ollama    │
│ (tenants,    │                 │ (Embeddings)          │
│  documents,  │                 │                       │
│  chunks)     │                 │                       │
└──────────────┘                 └───────────────────────┘
```

Application layout:

| Path | Purpose |
|------|---------|
| `app/main.py` | App factory, lifespan (runs the SQL migration), error handlers |
| `app/config.py` | Environment-driven `Config` |
| `app/db.py` | SQLite connection and startup migration |
| `app/auth.py` | `require_admin` / `require_tenant` dependencies, error envelope |
| `app/routes.py` | `/admin/*` and `/api/v1/*` endpoints, including document list/detail/delete/re-ingest and file upload |
| `app/services.py` | Chunking, text extraction (`.txt`/`.md`/`.pdf`), Ollama embeddings, shared ingest helper |
| `migrations/` | SQL schema, applied on startup |
| `tests/` | pytest suite |
| `ui/` | Vendored TailAdmin free template and the documents/sign-in pages |
| `ui/build/` | webpack output, built in Docker and served under `/console/` (never committed) |

---

## 4. Configuration & Environment

The application is configured via environment variables (supported via `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | API Port | `8080` |
| `DATABASE_URL` | SQLite connection string | `sqlite://data/local_rag.db` |
| `QDRANT_URL` | Vector Database URL | `http://localhost:6333` |
| `OLLAMA_URL` | External Ollama API URL | `http://localhost:11434` |
| `ADMIN_SECRET` | Secret key for internal admin access | `secret_admin_key` |
| `ENV` | Deployment environment (`local`, `staging`, `production`) | `local` |

**Note on Docker Networking:** When running the backend in Docker, use `http://host.docker.internal:11434` to reach an Ollama instance running on your host machine.

---

## 5. Code Standards & Contribution Guidelines

1. **Idiomatic Python**: PEP 8, type hints on public functions, pydantic models for request bodies. Keep functions small and named for what they do.
2. **Strict Multi-Tenancy**: Every query touching `documents` or `chunks` must filter on `tenant_id` at the SQL layer for tenant-facing paths. The tenant id always comes from the API key, never from the request body.
3. **Error Handling**: Raise `HTTPException` for client errors; the shared handler renders `{"error": {"code", "message"}}`. Unexpected exceptions return `500` and are logged, never leaked verbatim.
4. **Security**: The admin secret and tenant API keys are compared on every request; admin routes require `X-Admin-Secret`, tenant routes require `X-API-Key`. Never trust a `tenant_id` supplied by an external client.
5. **Testing**: `pytest` covers configuration, migration, chunking, embeddings, and every route. Tests must not require a running Qdrant or Ollama.
6. **Docker Only**: Run the service, the tests, and any tooling through Docker — do not assume a host Python toolchain.

```bash
# Full test suite
docker run --rm -v "$PWD:/src" -w /src python:3.12-slim \
  sh -c 'pip install -q -r requirements.txt && pytest -q'

# Service
docker compose up --build -d
```

---

## 6. Admin UI (TailAdmin free only)

The internal document management interface is served by FastAPI at
`/console/documents` (tenant management at `/console/tenants`; `/console/signin`
for sign-in; `/` and `/console` redirect to the documents page). Static assets
are served from `/console/`. It is a static bundle: HTML, Tailwind CSS,
Alpine.js, and `ui/src/js/documents.js` / `ui/src/js/tenants.js`, which talk to
the admin JSON API with `X-Admin-Secret`.

**Only TailAdmin free is allowed.** Do not add TailAdmin Pro components, Pro
assets, Pro page templates, or any code that depends on the Pro package. The
vendored template is TailAdmin free v2.4.0 (MIT); `ui/LICENSE` and
`ui/README.md` must stay in place as attribution.

- `ui/src/pages/` holds only three pages: `documents.html` (documents),
  `tenants.html` (tenant management) and `signin.html`. The sidebar links to
  Documents and Tenants only (demo pages — charts, calendar, profile, forms,
  UI elements — were removed).
- Tenant management is archive-only: there is no tenant delete control in the
  UI or a `DELETE /admin/tenants/*` route. Archiving sets `archived_at`; the
  archived API key then gets `403` on `/api/v1/*`.
- `/console/tenants` is served by FastAPI from the same `UI_DIR` guard as
  `/console/documents`.
- Layout partials live in `ui/src/partials/layout/app-layout/` and are inlined by
  webpack `<include>` directives at build time.
- The admin secret is validated against `GET /admin/tenants` and kept in
  `sessionStorage` only — never `localStorage`, never a cookie. Signing out
  clears it.
- Document, chunk, and tenant text is rendered with `textContent`; never assign
  API data to `innerHTML`.
- Operators never see raw tenant ids. The API keeps `tenant_id` in its payloads,
  but the interface resolves ids to tenant names with `GET /admin/tenants` and
  shows the name everywhere (table, chunk preview, tenant selects). Names that
  collide keep a short id suffix so they stay distinguishable.
- `ui/build/` is produced by `npm ci && npm run build` inside the `node:22-alpine`
  stage of the `Dockerfile`; the Python image only receives the built files, so no
  Node runtime ships. `ui/node_modules/` and `ui/build/` are git- and
  docker-ignored.

```bash
# Rebuild the UI bundle through Docker (never on the host)
docker run --rm -v "$PWD/ui:/ui" -w /ui node:22-alpine \
  sh -c 'npm ci && npm run build'

# Rebuild and restart the service (UI included)
docker compose up --build -d
```

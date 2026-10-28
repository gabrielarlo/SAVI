# Tasks

## 1. Python scaffolding

- [x] 1.1 Add `requirements.txt` (`fastapi`, `uvicorn[standard]`, `httpx`, `python-dotenv`, `pytest`) and verify `docker run --rm -v "$PWD:/src" python:3.12-slim pip install -r /src/requirements.txt` resolves without errors
- [x] 1.2 Implement `app/config.py` reading `PORT`, `DATABASE_URL`, `QDRANT_URL`, `OLLAMA_URL`, `ADMIN_SECRET`, `ENV` with the documented defaults and `.env` loading; verify `pytest tests/test_config.py` covers both the all-defaults and all-overrides cases
- [x] 1.3 Implement `app/db.py` (connect with `PRAGMA foreign_keys=ON`, `sqlite://` prefix stripping, directory creation) and the lifespan migration that `executescript`s `migrations/20261026000000_init.sql`; verify a test asserts `tenants`, `documents`, `chunks` exist and that running the migration twice succeeds

## 2. Ported behaviour

- [x] 2.1 Implement `chunk_text` in `app/services.py` (500-word windows, 50-word overlap); verify tests cover a 1000-word document whose second chunk starts at word 451, empty content producing no chunks, and sequential `chunk_index` values
- [x] 2.2 Implement the Ollama embedding call in `app/services.py` using `httpx` against `{OLLAMA_URL}/api/embeddings` with model `nomic-embed-text`; verify a mocked-transport test returns the vector and that a connection failure does not raise
- [x] 2.3 Implement `app/auth.py` with `require_admin` and `require_tenant` dependencies plus the `{"error": {"code", "message"}}` exception handler; verify tests cover valid admin secret, valid API key, missing credentials (`Invalid or missing authentication credentials`), and unknown API key, all as `401`
- [x] 2.4 Implement `POST /admin/tenants`, `POST /admin/documents`, and `POST /admin/search` in `app/routes.py`; verify tests assert the response bodies, the `lrk_` API key prefix, and that search results carry `tenant_id`
- [x] 2.5 Implement `POST /api/v1/chat`; verify a test seeds chunks for two tenants and asserts the response `sources` contain only the authenticated tenant's chunk and that a body `tenant_id` is ignored
- [x] 2.6 Implement `app/main.py` wiring the routes, dependencies, and lifespan into a FastAPI app; verify `pytest tests/test_api.py` exercises every route through `TestClient` and that role mismatches return `Internal admin access required` / `Tenant API key required`

## 3. Container

- [x] 3.1 Rewrite `Dockerfile` as a single-stage `python:3.12-slim` image (`pip install -r requirements.txt`, copy `app/` and `migrations/`, `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]`); verify `docker compose build app` succeeds and the cargo cache mounts and `ENV` build branch are gone
- [x] 3.2 Update the `app` service in `docker-compose.yml` to drop `build.args`, keep the runtime environment block and `sqlite_data` volume; verify `docker compose up -d` starts the service and `docker compose logs app` shows uvicorn listening

## 4. Remove the Rust tree

- [x] 4.1 Delete `src/`, `Cargo.toml`, and `Cargo.lock`; verify `grep -ri cargo --exclude-dir=.git --exclude-dir=openspec .` and `grep -rn "local_rag" Dockerfile docker-compose.yml` return no build references
- [x] 4.2 Rewrite `AGENTS.md` for the Python stack (FastAPI, stdlib `sqlite3`, pytest, Docker-only), keeping the multi-tenancy, security, and environment-variable rules; verify it contains no Rust/cargo/rustfmt guidance

## 5. Verification

- [x] 5.1 Run the full suite in Docker (`docker run --rm -v "$PWD:/src" -w /src python:3.12-slim sh -c 'pip install -q -r requirements.txt && pytest -q'`) and confirm all tests pass
- [x] 5.2 Smoke test the running stack with `curl`: create a tenant, ingest a document, search as admin, and chat as the tenant; confirm each returns `200` with the documented JSON shape
- [x] 5.3 Measure a clean rebuild (`docker compose build --no-cache app`) and confirm it completes in under one minute, then record the observed time in the change summary

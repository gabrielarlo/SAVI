# LocalRAG

Multi-tenant Retrieval-Augmented Generation service. Internal operators manage
documents, chunks, and tenants through an admin JSON API and a TailAdmin console;
external chatbots query only their own tenant's content. FastAPI + SQLite for
documents, chunks, and tenants; Ollama (`nomic-embed-text`) for embeddings.
Qdrant runs alongside but is not queried yet.

- Tenant isolation at the SQL layer — the tenant id always comes from the API key.
- Ingest `.txt`, `.md`, and `.pdf` via JSON or multipart upload; chunks are
  embedded on ingest and can be re-ingested.
- Everything runs in Docker. Nothing is installed on the host.

## Quick start

```bash
cp .env.example .env       # optional; defaults work for local
docker compose up --build -d
```

- API + docs: `http://localhost:8080` (`/docs` for the generated OpenAPI UI)
- Admin console: `http://localhost:8080/console/documents`
  (sign in at `/auth/signin` with username/password)
- Qdrant: `http://localhost:6333`

The stack starts the API and Qdrant. Ollama is **not** in the compose file — point
`OLLAMA_URL` at one you run yourself. From inside the container, a host Ollama is
`http://host.docker.internal:11434`; `http://localhost:11434` only works when the
app runs on the host.

## Configuration

Environment variables (see `.env.example`), read once at startup by
`app/config.py`:

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8080` | API port |
| `DATABASE_URL` | `sqlite://data/local_rag.db` | SQLite location |
| `QDRANT_URL` | `http://localhost:6333` | Vector database |
| `OLLAMA_URL` | `http://localhost:11434` | Embedding service |
| `ADMIN_SECRET` | `secret_admin_key` | Internal operator secret |
| `ENV` | `local` | Deployment environment |
| `CODE_NAME` | (none) | Chatbot persona name used in inquiry answers |
| `COMPANY_NAME` | (none) | Company name the assistant represents |
| `CHAT_MODEL` | `llama3.2:3b` | Ollama model for inquiry answers |
| `CHAT_THINK` | (auto) | Enable model thinking (`true`/`false`); auto-tuned per model |
| `CHAT_NUM_CTX` | (auto) | Context window size for chat generation |
| `CHAT_NUM_PREDICT` | (auto) | Max tokens to generate for chat answers |

`docker-compose.yml` sets `DATABASE_URL`, `QDRANT_URL`, `OLLAMA_URL`, and `ENV`
only. `ADMIN_SECRET` falls back to the code default, so set it explicitly
anywhere that is not your laptop.

## API

Two auth headers, one per audience. Errors share the envelope
`{"error": {"code": ..., "message": ...}}`.

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/admin/tenants` | `X-Admin-Secret` | Create tenant; returns its API key |
| `GET` | `/admin/tenants` | `X-Admin-Secret` | List tenants |
| `POST` | `/admin/documents` | `X-Admin-Secret` | Ingest `{tenant_id, title, content}` |
| `POST` | `/admin/documents/upload` | `X-Admin-Secret` | Multipart `.txt`/`.md`/`.pdf`, max 10 MB |
| `GET` | `/admin/documents` | `X-Admin-Secret` | List; optional `?tenant_id=` |
| `GET` | `/admin/documents/{id}` | `X-Admin-Secret` | Document plus its chunks |
| `DELETE` | `/admin/documents/{id}` | `X-Admin-Secret` | Delete document |
| `POST` | `/admin/documents/{id}/reingest` | `X-Admin-Secret` | Rebuild chunks |
| `POST` | `/admin/search` | `X-Admin-Secret` | Cross-tenant search |
| `POST` | `/api/v1/chat` | `X-API-Key` | Tenant-scoped answer + sources |

```bash
# create a tenant, then ingest into it
curl -s -X POST localhost:8080/admin/tenants -H 'X-Admin-Secret: secret_admin_key' \
  -H 'content-type: application/json' -d '{"name":"acme"}'

curl -s -X POST localhost:8080/admin/documents -H 'X-Admin-Secret: secret_admin_key' \
  -H 'content-type: application/json' \
  -d '{"tenant_id":"<id>","title":"FAQ","content":"Refunds take 5 days."}'
```

## Host requirements (staging / production)

The app runs in Docker, but the host must provide Docker, Ollama, and the
required models. Verify everything with the included doctor script:

```bash
set -a && . ./.env && set +a
./doctor.sh
```

It checks CPU/RAM/disk, Docker + compose, required env vars, Ollama reachability
and that `CHAT_MODEL` plus `nomic-embed-text` are pulled, Qdrant, and project
files. Exit code `0` means ready to deploy; `1` means something is missing.

## Tests

`pytest` needs no Qdrant and no Ollama. Run it in the same image the service uses:

```bash
docker run --rm -v "$PWD:/src" -w /src python:3.12-slim \
  sh -c 'pip install -q -r requirements.txt && pytest -q'
```

## Where things live

| Path | Purpose |
|---|---|
| `app/main.py` | App factory, lifespan (runs the SQL migration), error handlers |
| `app/config.py` | Environment-driven config |
| `app/auth.py` | `require_admin` / `require_tenant`, error envelope |
| `app/routes.py` | `/admin/*` and `/api/v1/*` endpoints |
| `app/services.py` | Chunking, text extraction, embeddings, ingest helper |
| `migrations/` | SQL schema, applied on startup |
| `tests/` | pytest suite |
| `ui/` | TailAdmin (free, MIT) console sources; built in Docker |
| `openspec/` | Specs and in-flight changes |

Architecture, code standards, and UI rules live in [`AGENTS.md`](AGENTS.md) —
read that before changing behavior or the console.

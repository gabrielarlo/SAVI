# Tasks

## 1. Draft the README

- [x] 1.1 Create root `README.md` with a one-paragraph "what this is" (multi-tenant RAG API: FastAPI + SQLite + Qdrant + Ollama embeddings) and a short feature list; verify the file exists at the repo root and stays under ~120 lines
- [x] 1.2 Add a "Quick start" section that only uses Docker — `docker compose up --build -d`, service at `http://localhost:8080`, console at `/console/documents`, sign-in with `X-Admin-Secret`; verify each command/URL appears and matches `docker-compose.yml`
- [x] 1.3 Add a configuration table (`PORT`, `DATABASE_URL`, `QDRANT_URL`, `OLLAMA_URL`, `ADMIN_SECRET`, `ENV`) with defaults, copied from `app/config.py`; verify every variable name and default matches the code exactly
- [x] 1.4 Add an API-at-a-glance section listing the `/admin/*` and `/api/v1/*` routes with their auth header (`X-Admin-Secret` vs `X-API-Key`) and one line each; verify against the decorators in `app/routes.py`
- [x] 1.5 Add a "Run the tests" section with the `docker run --rm -v "$PWD:/src" ... pytest -q` command, noting no Qdrant/Ollama is needed; verify the command matches the one in `AGENTS.md`
- [x] 1.6 Add a "Where things live" table (app layout) and a pointer to `AGENTS.md` for architecture, standards, and UI rules; verify no architecture diagram or Pro-UI guidance is duplicated

## 2. Verify

- [x] 2.1 Re-read `README.md` end to end and confirm every command is copy-pasteable, every path exists in the repo, and no secret literals are documented as production values
- [x] 2.2 Run `docker compose config -q` and the documented test command to confirm the README's instructions still work; both must exit 0

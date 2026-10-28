# service-configuration Specification

## Purpose

Defines the environment contract the service reads at startup so deployments can
point it at the right database, vector store, and model endpoint without code
changes.

## Requirements

### Requirement: Environment-driven configuration

The service SHALL read its settings from environment variables, loading a local
`.env` file first when one is present, and SHALL fall back to documented defaults
when a variable is unset.

| Variable | Default |
|---|---|
| `PORT` | `8080` |
| `DATABASE_URL` | `sqlite://data/local_rag.db` |
| `QDRANT_URL` | `http://localhost:6333` |
| `OLLAMA_URL` | `http://localhost:11434` |
| `ADMIN_SECRET` | `secret_admin_key` |
| `ENV` | `local` |
| `APP_NAME` | `LocalRAG` |
| `APP_SHORT_DESCRIPTION` | (unset) |
| `WHISPER_MODEL` | `small` |
| `WHISPER_LANGUAGE` | (unset) |
| `TTS_MODEL` | `phonon` |
| `TTS_VOICE` | (unset) |

#### Scenario: All variables unset

- **WHEN** the service starts with no relevant environment variables set
- **THEN** it listens on port `8080`, uses `sqlite://data/local_rag.db`, treats `ENV` as `local`, uses `LocalRAG` as the application name, uses the `small` Whisper model, and uses the `phonon` TTS model

#### Scenario: Values supplied

- **WHEN** `PORT=9090`, `DATABASE_URL=sqlite://test.db`, `QDRANT_URL=http://qdrant.test:6333`, `OLLAMA_URL=http://ollama.test:11434`, `ENV=prod`, `APP_NAME=SAVI`, `APP_SHORT_DESCRIPTION="SCB AI Virtual Intelligence"`, `WHISPER_MODEL=small`, and `TTS_MODEL=phonon` are set
- **THEN** the service uses exactly those values instead of the defaults

### Requirement: Startup schema initialisation

On startup the service SHALL apply `migrations/20261026000000_init.sql` so that
the `tenants`, `documents`, and `chunks` tables exist, creating the SQLite
database file if it is missing.

- Applying the migration twice MUST be safe.
- Startup MUST NOT require a reachable Qdrant or Ollama instance.

#### Scenario: Fresh database

- **WHEN** the service starts against a database file that does not exist
- **THEN** the file is created and the three tables are present

#### Scenario: Existing database

- **WHEN** the service restarts against an already-migrated database
- **THEN** startup succeeds and no data is lost

#### Scenario: Dependencies offline

- **WHEN** Qdrant and Ollama are unreachable
- **THEN** the service still starts and serves authenticated requests

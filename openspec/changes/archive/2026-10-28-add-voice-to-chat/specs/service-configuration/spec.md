# Spec Delta

## MODIFIED Requirements

### Requirement: Environment-driven configuration

The service SHALL read its settings from environment variables, loading a local
`.env` file first when one is present, and SHALL fall back to documented
defaults when a variable is unset.

| Variable | Default |
|---|---|
| `PORT` | `8080` |
| `DATABASE_URL` | `sqlite://data/local_rag.db` |
| `QDRANT_URL` | `http://localhost:6333` |
| `OLLAMA_URL` | `http://localhost:11434` |
| `ADMIN_SECRET` | `secret_admin_key` |
| `ENV` | `local` |
| `WHISPER_MODEL` | `small` |
| `WHISPER_LANGUAGE` | (unset) |
| `TTS_MODEL` | `phonon` |
| `TTS_VOICE` | (unset) |

#### Scenario: All variables unset

- **WHEN** the service starts with no relevant environment variables set
- **THEN** it listens on port `8080`, uses `sqlite://data/local_rag.db`, treats
  `ENV` as `local`, uses the `base` Whisper model, and uses the `phonon` TTS
  model

#### Scenario: Values supplied

- **WHEN** `PORT=9090`, `DATABASE_URL=sqlite://test.db`, `QDRANT_URL=http://qdrant.test:6333`, `OLLAMA_URL=http://ollama.test:11434`, `ENV=prod`, `WHISPER_MODEL=small`, and `TTS_MODEL=phonon` are set
- **THEN** the service uses exactly those values instead of the defaults
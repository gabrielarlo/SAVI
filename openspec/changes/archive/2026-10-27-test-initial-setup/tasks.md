# Tasks

## 1. Add setup smoke tests

- [x] 1.1 Test `Config::from_env` defaults and environment overrides with controlled environment values; verify the test passes without leaking environment changes.
- [x] 1.2 Add an isolated SQLite migration smoke test and assert the `tenants`, `documents`, and `chunks` tables are created; verify it runs without Qdrant or Ollama.

## 2. Verify

- [x] 2.1 Run `cargo test` and `cargo fmt --check`; confirm both pass.

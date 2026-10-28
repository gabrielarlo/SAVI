# Proposal

## Why

The repository has no automated tests for its initial setup path, so configuration or database migration regressions could go unnoticed. Add a focused, repeatable check so developers can verify the local service setup with the project's standard Rust test command.

## What Changes

- Add a small smoke test for the existing startup setup, focusing on configuration defaults and SQLite migration initialization.
- Keep the check independent of running Qdrant or Ollama services.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Rust tests around `src/config.rs` and SQLite migrations in `migrations/`.
- Verified using `cargo test`; the Rust toolchain is currently unavailable in this environment.

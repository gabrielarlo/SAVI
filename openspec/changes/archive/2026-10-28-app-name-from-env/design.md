# Design

## Context

See proposal.md. App identity is currently hardcoded as `"LocalRAG"` in
`app/main.py` (FastAPI title and `window.LOCALRAG_CODE_NAME`-adjacent
branding). Config already follows the env-driven pattern with `CODE_NAME`
and `COMPANY_NAME`; `APP_NAME`/`APP_SHORT_DESCRIPTION` extend it.

## Goals / Non-Goals

**Goals:**
- Read `APP_NAME` and `APP_SHORT_DESCRIPTION` from env with sensible defaults.
- Use `config.app_name` for the FastAPI title.
- Expose both values via `/console/config.js` for runtime branding.

**Non-Goals:**
- Rebuilding UI HTML titles at build time (static templates keep "LocalRAG"
  as a fallback; runtime JS may override where practical).
- Renaming internal code symbols or the repo.

## Decisions

- **Config fields**: add `app_name: str = DEFAULT_APP_NAME` (default
  `"LocalRAG"`) and `app_short_description: str | None` (default `None`),
  read from `APP_NAME`/`APP_SHORT_DESCRIPTION`, mirroring `CODE_NAME`.
  Default preserves current behavior when unset.
- **FastAPI title**: `FastAPI(title=config.app_name, ...)`.
- **console_config.js**: emit `window.LOCALRAG_APP_NAME` and
  `window.LOCALRAG_APP_SHORT_DESCRIPTION` alongside the existing
  `window.LOCALRAG_CODE_NAME`, using JSON encoding and the same fallback
  pattern in `chat-widget.html`.

## Risks / Trade-offs

- [Risk] UI static titles remain "LocalRAG" → Mitigation: runtime JS can
  override `document.title` from config.js; out of scope for this change's
  tests.

## Migration Plan

Add config fields, update main.py, update tests. No DB migration.

## Open Questions

None.

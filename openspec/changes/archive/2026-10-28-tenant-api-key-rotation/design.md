# Design

## Context

Tenants store a single `api_key`. There is no rotation metadata or
regeneration endpoint. Auth validates by direct key lookup.

## Goals / Non-Goals

**Goals:**
- Add rotation metadata and settings to tenants.
- Add retrieve/regenerate endpoints and expiry enforcement.
- Update tenant management UI for copy/regenerate/settings.

**Non-Goals:**
- No background scheduler; expiry is checked on authentication.
- No key versioning/history.

## Decisions

- **Migration**: ALTER tenants ADD COLUMN api_key_created_at, api_key_expires_at,
  auto_rotate (default 1), rotate_days (default 90). Backfill existing rows
  with created_at=now and expires_at=now+90 days.
- **Regeneration**: generate `lrk_` key, update key + created_at + expires_at.
- **Expiry check**: in get_role, if key matches and expired (skip when
  rotate_days/api_key_expires_at is null):
   - auto_rotate=1: rotate key, commit, raise 401 "API key expired and rotated".
   - else: raise 401 "API key expired".
- **Settings**: extend UpdateTenantRequest with optional auto_rotate and
  rotate_days (integer or null for "forever"); validate rotate_days is null or >= 1.
- **UI**: copy fetches key endpoint; regenerate confirms then shows modal;
  settings in edit modal.

## Risks / Trade-offs

- [Expiry check on every auth] → single row lookup, negligible.
- [Auto-rotation side effect in auth] → wrapped in try/except; on failure
  reject without rotating.
- [Migration backfill] → handled in migration SQL with CURRENT_TIMESTAMP.

## Migration Plan

Add migration file; apply on startup. Rebuild UI and restart.
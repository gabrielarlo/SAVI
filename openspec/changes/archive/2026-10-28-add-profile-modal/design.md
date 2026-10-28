# Design

## Context

The console has no modal component today; dialogs are inline. The user dropdown
is an Alpine.js component in `user-dropdown.html`. The avatar is a static image.
Self-profile management is not exposed by the API; only admin user CRUD exists.

## Goals / Non-Goals

**Goals:**
- Centered modals (fixed overlay with flex centering).
- Text-based avatar initials from username.
- Profile modal in user dropdown (no sidebar link).
- Optional self-profile endpoints.

**Non-Goals:**
- Full user management from the Profile modal (admin page remains).
- Avatar image upload.

## Decisions

**Modal centering.** Use a fixed overlay `inset-0 flex items-center justify-center`
with a backdrop; applies to all modals including chat if needed.

**Avatar initials.** Replace `<img>` with a `<span>` showing first two letters
uppercased, styled as a circle/square. Derive from session username; fallback
"AD" for admin secret.

**Header username.** Render the signed-in username in the dropdown label,
falling back to "Admin" for admin-secret sessions.

**Profile modal.** Alpine.js modal in `user-dropdown.html` or a partial. Form
posts to a new `/auth/profile` (GET/PATCH) or reuses admin endpoints. Given
self-service, prefer new endpoints that resolve the signed-in user from the
session token.

**Self-profile API.** Add `GET /auth/profile` and `PATCH /auth/profile` resolving
the user from `X-Session-Token` (or admin secret with no user). Password policy
enforced.

## Risks / Trade-offs

- Admin-secret sessions have no username; profile modal may be limited or
  disabled for them.
- Adding endpoints expands the auth surface; keep them minimal.

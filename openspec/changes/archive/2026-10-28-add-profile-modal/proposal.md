# Proposal

## Why

Modals in the console are not centered, the avatar always shows a static image
instead of a text-based initial derived from the signed-in user, and there is no
way for an operator to manage their own profile without leaving the console or
using the Users page.

## What Changes

- Fix modal positioning so dialogs are centered in the viewport.
- Add a "Profile" modal (opened from the user dropdown, not sidebar navigation)
  for managing the signed-in user's own profile (username and password).
- Replace the avatar image with a text-based avatar derived from the username
  (e.g. `savi_admin` → `SA`).
- Display the signed-in username in the header instead of the static "Admin"
  label.
- Keep all rendered text as text (no HTML injection).

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `admin-ui`: modal centering, text-based avatar, Profile modal entry point.
- `user-management`: self-profile read/update for the signed-in user.

## Impact

- **Frontend**: `ui/src/partials/layout/app-layout/header/user-dropdown.html`,
  new profile modal partial, `ui/src/js/users.js` or a new module.
- **Backend**: self-profile endpoints (optional but recommended) under `/auth`.
- **No schema change.**

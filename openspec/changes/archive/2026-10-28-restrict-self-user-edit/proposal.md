# Proposal

## Why

On the Users management page, an operator can edit or archive their own account,
which can lock them out or cause confusion. The signed-in user should not be able
to mutate their own user record from that page; self-management belongs in the
Profile modal.

## What Changes

- In the Users management UI, disable or hide Edit/Archive actions for the
  signed-in user's own row.
- Backend (optional) may reject self-mutation with `400`/`403` as a safeguard.
- Keep all other user management behavior unchanged.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `admin-ui`: restrict self-edit/archive on the Users page.
- `user-management`: (optional) reject self-mutation via admin endpoints.

## Impact

- **Frontend**: `ui/src/js/users.js`, `users.html`.
- **Backend**: `app/routes.py` (optional guard).
- **Tests**: UI behavior and/or route guard.
- **No schema change.**

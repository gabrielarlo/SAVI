# Design

## Context

The Users page renders Edit/Archive for every user including the signed-in one.
Self-mutation can lock out the operator. The signed-in username is available in
`sessionStorage` (`localrag.username`); admin-secret sessions have no username.

## Goals / Non-Goals

**Goals:**
- Disable self Edit/Archive in the UI.
- Optionally reject self-mutation on the backend using the session username.

**Non-Goals:**
- No new endpoints.
- No changes to admin-secret behavior beyond best-effort.

## Decisions

**UI guard.** In `users.js`, when rendering a row whose `username` equals the
signed-in username, disable Edit/Archive buttons.

**Backend guard.** Resolve the signed-in user from the session token in
`update_user`/`archive_user`; if the target id matches, return `400`. Admin
secret has no user, so skip.

## Risks / Trade-offs

- Admin-secret sessions cannot be matched to a user; backend guard only applies
  to session users.
- UI guard relies on stored username; if missing, actions remain enabled.

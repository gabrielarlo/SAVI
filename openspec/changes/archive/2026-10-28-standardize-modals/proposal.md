# Proposal

## Why

Native `<dialog>` elements lose their default centering under Tailwind preflight, so
the View (documents), Edit (tenants/users), and Create dialogs are off-center.
There is also no reusable modal component, and data mutation actions (documents,
tenants, users) lack a confirmation step.

## What Changes

- Add `m-auto` (or equivalent) to every native dialog so all modals are centered.
- Introduce a reusable modal component (overlay + panel) for consistent
  centering and maintenance.
- Add confirmation modals for all data mutation actions (documents, tenants,
  users) before the request is sent.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `admin-ui`: modal centering standardization, reusable modal component,
  confirmation dialogs for user mutations.

## Impact

- **Frontend**: `ui/src/pages/*`, `ui/src/css/style.css`, modal markup.
- **No backend change.**
- **Tests**: UI build.

# Design

## Context

Tenants table currently shows Name, ID, Created, Status, Actions. API key is
only available via copy action fetching endpoint.

## Goals / Non-Goals

**Goals:**
- Add an API key column with masked display and copy.

**Non-Goals:**
- No backend changes; reuse `/admin/tenants/{id}/api-key`.

## Decisions

- Add column header and cell in tenants.html.
- Render masked value from tenant data if available; otherwise fetch on copy.
- Keep full key out of DOM.

## Risks / Trade-offs

- [Masked value needs key] → fetch key lazily on copy; display placeholder.

## Migration Plan

Rebuild UI bundle and restart.
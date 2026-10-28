# Proposal

## Why

The dashboard currently renders a flat list of stat cards. Grouping metrics,
adding icons, linking cards to their management pages, and adding filters
(e.g. archived tenants, expiring API keys) makes it a useful navigation and
triage hub.

## What Changes

- Group dashboard metrics into sections (Overview, Tenants, Users, Activity,
  API keys).
- Add an SVG icon to each stat card.
- Make stat cards link to their relevant console page (documents, tenants,
  users).
- Add filter support on the tenants page for archived tenants and tenants with
  expiring (<=30 days) API keys, reachable from dashboard cards.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `admin-ui`: dashboard grouping, icons, links, and tenant filters.

## Impact

- `ui/src/pages/(admin-layout)/(main)/dashboard.html`
- `ui/src/js/dashboard.js`
- `ui/src/pages/(admin-layout)/(main)/tenants.html`
- `ui/src/js/tenants.js`
- `ui/build/` regenerated.
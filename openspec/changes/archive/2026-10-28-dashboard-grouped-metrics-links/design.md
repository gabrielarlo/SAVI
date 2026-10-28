# Design

## Context

Dashboard renders a flat grid of cards from `dashboard.js`. Tenants page
filters by status only. No icons or links currently.

## Goals / Non-Goals

**Goals:**
- Group cards into sections with headings.
- Add inline SVG icons and anchor links.
- Add client-side filter handling for archived/expiring tenants.

**Non-Goals:**
- No new backend endpoints; use existing stats and tenant list.

## Decisions

- **Grouping**: render section headings in HTML; JS appends cards into the
  correct section container by metric key.
- **Icons**: inline SVG strings (aria-hidden) per metric.
- **Links**: every card MUST be an `<a>` (no plain `<div>` cards), with a
  destination for each metric: tenants/active/archived → `/console/tenants`
  (archived → `?filter=archived`); documents and chunks → `/console/documents`;
  users/active/archived → `/console/users`; inquiries/inquiries today →
  `/console`; api_keys_blue → `/console/tenants`; api_keys_orange and
  api_keys_red → `/console/tenants?filter=expiring`.
- **Filters**: read `URLSearchParams` on tenants page; filter tenant list
  accordingly. Expiring = api_key_expires_at within 30 days and not null.

## Risks / Trade-offs

- [Filter logic duplication] → reuse existing match function.

## Migration Plan

Rebuild UI bundle and restart. No backend changes.
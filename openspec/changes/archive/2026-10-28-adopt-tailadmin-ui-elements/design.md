# Design

## Context

Console pages already use TailAdmin free layout. This change aligns inner
controls (buttons, badges, inputs, modals, alerts, tables) with the template's
documented UI element patterns. No API or schema changes.

## Goals / Non-Goals

**Goals:**
- Consistent TailAdmin UI element classes across console pages.
- Reuse shared partials where available (password input, modal).

**Non-Goals:**
- No new dependencies or components.
- No functional behavior changes.

## Decisions

- Audit each page against TailAdmin UI elements and apply matching classes.
- Keep all rendering text-based; no innerHTML for API data.
- No changes to JS data flow; only class/structure adjustments.

## Risks / Trade-offs

- [Large diff] → Limit to class/structure alignment; avoid logic changes.
- [Build required] → Rebuild UI bundle via Docker.

## Migration Plan

Rebuild UI bundle and restart service. No backend changes.
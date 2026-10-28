# Design

## Context

Multiple pages use native `<dialog>` elements. Tailwind preflight resets margins,
breaking centering. A shared CSS component (`.modal-overlay`, `.modal-panel`) was
introduced; native dialogs need `m-auto`.

## Goals / Non-Goals

**Goals:**
- All dialogs centered.
- Reusable modal classes applied consistently.
- Confirmation modals for user mutations.

**Non-Goals:**
- No backend changes.
- No new pages.

## Decisions

**Native dialogs.** Add `m-auto` to every `<dialog>` class list. For overlay
divs, use `.modal-overlay`.

**Reusable component.** Keep `.modal-overlay`/`.modal-panel` in `style.css` and
apply to new modals; document usage in CONTRIBUTING-UI.

**Confirmations.** Intercept submit/archive/delete clicks across documents,
tenants, and users to show a centered confirmation modal (native `<dialog>` with
`m-auto`) before proceeding.

## Risks / Trade-offs

- Native dialog centering depends on `m-auto`; must be applied to every dialog.
- Confirmation adds a step but prevents accidental mutations.

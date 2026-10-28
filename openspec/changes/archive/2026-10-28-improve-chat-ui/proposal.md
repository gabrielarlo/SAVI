# Proposal

## Why

The console chat widget is functional but visually plain, loses its conversation on
refresh, and its floating button is labeled only "Chat". Operators expect a
polished, persistent chat experience comparable to common chat UIs, with history
surviving reloads and an explicit "New conversation" reset.

## What Changes

- Redesign the chat widget UI (header, message bubbles, input bar, scroll area)
  to match common chat layouts.
- Persist chat messages in `sessionStorage` so the conversation survives page
  refresh; restore on load.
- Add a "New conversation" button that clears the persisted history and resets
  the view.
- Rename the floating launcher button to "Chat with <CODE_NAME>" using the
  configured persona name.
- Keep all text rendering as text (no HTML injection).

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `admin-ui`: update the console chat widget requirements (appearance,
  persistence, reset, launcher label).

## Impact

- **Frontend**: `ui/src/js/chat.js`, `ui/src/partials/layout/app-layout/header/chat-widget.html`,
  layout includes.
- **No backend or schema change.**
- **Tests**: UI bundle build; no new backend tests required.

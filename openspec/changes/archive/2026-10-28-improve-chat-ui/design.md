# Design

## Context

The chat widget lives in `ui/src/partials/layout/app-layout/header/chat-widget.html`
and `ui/src/js/chat.js`, included on every console page via the shared header.
`CODE_NAME` is available to the frontend only if injected; the widget can read it
from a global set at build/runtime. Conversation state currently lives only in
the DOM.

## Goals / Non-Goals

**Goals:**
- A visually polished chat panel (header, bubbles, input bar, scroll area).
- Persist messages in `sessionStorage` and restore on load.
- "New conversation" clears storage and resets the view.
- Launcher label uses `Chat with <CODE_NAME>`.

**Non-Goals:**
- No backend changes or new endpoints.
- No cross-tab sync (sessionStorage is tab-scoped, acceptable).
- No server-side history.

## Decisions

**Persistence key.** Store messages under `localrag.chatHistory` in
`sessionStorage` as JSON. On load, render restored messages. "New conversation"
removes the key and clears the message container.

**Persona label.** Inject `window.LOCALRAG_CODE_NAME` from the build or a small
inline script in the widget partial using a placeholder replaced at build time.
Simpler: render the label in the partial as `Chat with {{CODE_NAME}}` is not
possible at runtime without JS. Instead, set the label via JS reading a global;
default to "Chat" if unset. Also update the button text after fetching
`/admin/tenants`? No. Keep a global default "SAVI" fallback? Better: embed the
code name in the partial using a webpack DefinePlugin? Minimal: have chat.js
read `window.__CODE_NAME__` with fallback "Assistant"; and set a default in the
partial via a small inline script reading from a meta tag. Given no backend
template rendering, use a JS constant defaulting to "Assistant" and allow
override via `window.LOCALRAG_CODE_NAME`.

**Styling.** Use TailAdmin/Tailwind utility classes already available; no new
CSS framework. Bubbles: user right-aligned (brand color), assistant left-aligned
(gray). Header with persona name and "New conversation" button.

## Risks / Trade-offs

- If `CODE_NAME` changes, old persisted labels are not updated; acceptable.
- sessionStorage is cleared when the tab closes, matching "session" semantics.
- Restored messages are rendered with `textContent`, preserving the no-HTML rule.

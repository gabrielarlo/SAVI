# UI Guidelines — TailAdmin Free Only

> **Rule:** Use only TailAdmin **free** components/utilities. Do **not** add TailAdmin Pro
> imports, Pro assets, or Pro page templates. The MIT license (`ui/LICENSE`) and
> attribution (`ui/README.md`) must stay in place. Reference `AGENTS.md` §6 for the
> project-wide UI rules.

## Page scaffolding (from `ui/src/pages/...`)

Every admin page must follow the existing pattern (use `documents.html` / `tenants.html` as the canonical examples):

```html
<!doctype html>
<html lang="en">
  <head> ... <title>Page | LocalRAG</title> </head>
  <body
    x-data="{ page: 'documents', 'loaded': true, 'darkMode': false, 'stickyMenu': false, 'sidebarToggle': false, 'scrollTop': false }"
    x-init="
         darkMode = JSON.parse(localStorage.getItem('darkMode')) ?? false;
         $watch('darkMode', value => localStorage.setItem('darkMode', JSON.stringify(value)))"
    :class="{'dark bg-gray-900': darkMode === true}"
  >
    <include src="./partials/common/preloader.html"></include>
    <div class="flex h-screen overflow-hidden">
      <include src="./partials/layout/app-layout/sidebar/index.html"></include>
      <div class="relative flex flex-1 flex-col overflow-x-hidden overflow-y-auto">
        <include src="./partials/layout/app-layout/header/index.html" />
        <main id="main-content">
          <div class="mx-auto max-w-(--breakpoint-2xl) p-4 pb-20 md:p-6 md:pb-6">
            <div x-data="{ pageTitle: 'Page Title' }">
              <include src="./partials/common/page-breadcrumb.html" />
            </div>
            ...
          </div>
        </main>
      </div>
    </div>
  </body>
</html>
```

- `x-data.page` must equal the key the sidebar uses (`documents` / `tenants`) so `menu-item-active` highlights correctly.
- Use layout partials via webpack `<include>` directives — do not inline the entire layout.
- Output filename is flattened by `ui/webpack.config.js` (route folders are stripped); add a `GET /console/<page>` `FileResponse` route in `app/main.py` when the page is served by FastAPI.

## Sidebar menu item (from `ui/src/partials/layout/app-layout/sidebar/sidebar-nav-group-main.html`)

```html
<li>
  <a href="/console/tenants" class="group menu-item"
     :class="page === 'tenants' ? 'menu-item-active' : 'menu-item-inactive'">
    <svg :class="page === 'tenants' ? 'menu-item-icon-active' : 'menu-item-icon-inactive'" ...>
      <!-- free icon -->
    </svg>
    <span class="menu-item-text" :class="sidebarToggle ? 'xl:hidden' : ''">Tenants</span>
  </a>
</li>
```

Use the `menu-item`/`menu-item-active`/`menu-item-inactive` utilities defined in `ui/src/css/style.css`.

## Buttons, badges, table, dialog (recipes in use)

| Element | Classes/pattern | Notes |
| --- | --- | --- |
| Primary action | `rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-600` | Used for "Create Tenant", "Save changes". |
| Neutral/ghost | `rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-white/5` | Used for "Refresh", "Copy", dialog close. |
| Danger/warn action | `rounded-lg border border-red-500 px-3 py-1.5 text-sm font-medium text-red-500 transition hover:bg-red-50 dark:border-red-500/40 dark:hover:bg-red-500/15` | Used for "Archive" (active tenants only) and "Delete" (documents). |
| Status badge (active) | `rounded-full bg-green-100 px-2.5 py-0.5 text-sm text-green-700 dark:bg-green-500/15 dark:text-green-500` | Render via JS, text set with `textContent`. |
| Status badge (archived) | `rounded-full bg-gray-100 px-2.5 py-0.5 text-sm text-gray-600 dark:bg-gray-800 dark:text-gray-400` | No delete controls for archived tenants. |
| Table | Standard `<table>` with `thead/tr` `border-b border-gray-100 dark:border-gray-800`, body rows `border-b border-gray-100 last:border-0 dark:border-gray-800`. | Empty state: a paragraph with `hidden` toggled by JS. |
| Dialog/Modal | `<dialog>` with `backdrop:bg-gray-900/50`, max-width, border/ring, and an explicit close button. | Create key-reveal and edit use separate dialogs (see `tenants.html`). |

## Password input (reusable)
- Every password field MUST use the shared pattern: a relative wrapper `<div class="relative">`, an `<input type="password">` with right padding (`pr-10`), and an absolutely positioned toggle button (`absolute right-2 top-1/2 -translate-y-1/2`) inside the wrapper. The toggle MUST never render detached outside the field.
- Wire the toggle via the shared `wirePasswordToggle(input, toggle, icon)` helper exported from `ui/src/js/documents.js`; do not duplicate inline toggle logic.
- Sign-in forms MUST submit on Enter from either the username or password field (native `<form>` submit + explicit Enter handling).
- Reuse this pattern in every password field (sign-in, create, edit); do not duplicate markup.

## JS conventions

- **Auth**: secret in `sessionStorage` only (`localrag.adminSecret`), sent as `X-Admin-Secret` via a shared `request()` helper. `401` triggers sign-out.
- **Safety**: render all API/user text with `textContent` (never `innerHTML`). Follow the existing "textContent only" rule in `AGENTS.md` §6.
- **Forms**: `novalidate` + client-side messages in a dedicated message element.
- **Destructive actions**: require confirmation (`window.confirm`) before calling the API.
- **Shared helpers**: export helpers from `ui/src/js/documents.js` and import in feature modules (e.g. `tenants.js`), wire via `ui/src/js/index.js`.
- **Labels**: resolve tenant ids to names with a cached map; disambiguate collisions with a short id suffix.

## Consistency checklist

- [ ] Uses only TailAdmin free utilities (no Pro class names/packages)
- [ ] Page has correct `x-data.page` and sidebar link
- [ ] Dark mode classes present where the page uses them
- [ ] All dynamic strings rendered with `textContent`
- [ ] Secrets never in `localStorage`/cookies
- [ ] Destructive actions confirmed
- [ ] Empty states implemented
- [ ] If FastAPI serves the page, a `GET /console/<page>` route exists inside the `UI_DIR` guard

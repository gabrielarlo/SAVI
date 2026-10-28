# Tasks

## 1. Write the guidelines file

- [x] 1.1 Create `ui/CONTRIBUTING-UI.md` matching the existing pages' practice, with: TailAdmin-free-only rule (no Pro package, MIT attribution stays in place), page scaffolding recipe (`x-data` `page` key matching the sidebar link, breadcrumb include), menu-item markup recipe, button/badge/table/dialog recipes copied verbatim in spirit from `documents.html` and `tenants.html`, dark-mode conventions, and the security/consistency rules (`textContent`-only rendering, sessionStorage-only secret, never assign API data to `innerHTML`); verify nothing in the file contradicts `AGENTS.md` §6 and the file stays under 150 lines
- [x] 1.2 Do not invent components — every recipe cites an element that already exists in `ui/src/`; verify by grepping each cited class/element before it enters the file

## 2. Reference and verify

- [x] 2.1 Add one reference line in `AGENTS.md` §6 pointing to `ui/CONTRIBUTING-UI.md` for pattern standards; verify §6 content is not duplicated into or from the file
- [x] 2.2 Rebuild the UI bundle in the node container to prove the docs change does not touch the build, and run the pytest suite; both must pass unchanged (74 passed)

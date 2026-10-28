# Proposal

## Why

`AGENTS.md` §6 currently holds three loose bullets about TailAdmin free; component
choices (dialogs, buttons, badges, empty states) are decided ad hoc, which is how
`documents.html` and `tenants.html` drifted into partially repeated markup. A
dedicated UI guidelines file gives every future console change one referenced
source of pattern standards and keeps TailAdmin Pro out of the bundle — an
explicit hard rule of this project.

## What Changes

- Add `ui/CONTRIBUTING-UI.md` (working doc, not shipped to the bundle): a
  concise TailAdmin-free standards file defining, from the existing pages:
  page scaffolding (`x-data` `page` field, `page-breadcrumb` include, layout
  partials), menu items (`menu-item` utilities), TailAdmin button/table/badge/
  dialog recipes as used in `documents.html` and `tenants.html`, dark-mode
  conventions, `textContent`-only rendering, sessionStorage secret handling.
- State explicitly: only TailAdmin free utilities/components; no Pro package
  imports; `ui/LICENSE`/`ui/README.md` attribution stays.
- Reference the file from `AGENTS.md` §6 ("see ui/CONTRIBUTING-UI.md for the
  pattern standard") without duplicating its content.
- Documentation only: no code, no built output, no behavior change.

## Capabilities

### New Capabilities

None. A contributor-facing guideline documents existing practice; it does not
change any observable behavior the system specifies.

### Modified Capabilities

None.

## Impact

- New file: `ui/CONTRIBUTING-UI.md` (only).
- `AGENTS.md` §6: one added reference line.
- Not bundled, not served, not covered by specs. `.openspec.yaml` sets
  `skip_specs: true`.

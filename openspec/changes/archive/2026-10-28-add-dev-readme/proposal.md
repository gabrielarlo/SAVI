# Proposal

## Why

The repository has no `README.md`, so a new developer has to read `AGENTS.md`,
`docker-compose.yml`, and the source to learn how to run the service, call the API,
or run the tests. A short entry-point document closes that gap.

## What Changes

- Add a root `README.md` aimed at developers, not operators or end users.
- Cover, in this order: what the service is (one paragraph), prerequisites,
  run instructions (Docker only), configuration variables, the API surface at a
  glance, the admin console URL, the test command, and a pointer to `AGENTS.md`
  for architecture and code standards.
- Keep it concise: no marketing, no duplicated architecture diagram (link to
  `AGENTS.md` instead), no license rewrite (`ui/LICENSE` stays the attribution).
- Documentation only. No code, configuration, or behavior changes.

## Capabilities

### New Capabilities

None. Pure documentation change; no observable behavior is specified or altered.

### Modified Capabilities

None.

## Impact

- New file: `README.md` (root).
- No changes to `app/`, `migrations/`, `ui/`, `tests/`, Docker files, or the
  OpenSpec spec inventory.
- `openspec/changes/add-dev-readme/.openspec.yaml` sets `skip_specs: true`
  because specs describe behavior and behavior does not change.

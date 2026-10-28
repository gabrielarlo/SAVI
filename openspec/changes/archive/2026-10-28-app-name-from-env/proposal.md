# Proposal

## Why

The application name "LocalRAG" is hardcoded in the FastAPI title and UI
branding, so deploying under a different product name requires code edits.
The `.env` already carries `APP_NAME` and `APP_SHORT_DESCRIPTION`, but nothing
reads them. Make the identity env-driven with documented defaults.

## What Changes

- Add `APP_NAME` (default `LocalRAG`) and `APP_SHORT_DESCRIPTION` (default
  empty) to `Config` and `from_lookup`, mirroring `CODE_NAME`/`COMPANY_NAME`.
- Use `config.app_name` for the FastAPI application title instead of the
  hardcoded `"LocalRAG"`.
- Expose `app_name` and `app_short_description` through `/console/config.js`
  so the console can brand itself at runtime.
- Document both variables in `service-configuration`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `service-configuration`: add `APP_NAME` and `APP_SHORT_DESCRIPTION`
  environment variables with documented defaults.

## Impact

- `app/config.py`: new `app_name` and `app_short_description` fields.
- `app/main.py`: FastAPI title and `console_config.js` output.
- `tests/test_config.py`: coverage for the new fields.
- No database migration; no API contract change beyond config.js payload.

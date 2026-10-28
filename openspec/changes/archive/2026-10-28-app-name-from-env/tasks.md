# Tasks

## 1. Configuration

- [x] 1.1 Add `DEFAULT_APP_NAME` and `DEFAULT_APP_SHORT_DESCRIPTION` constants and `app_name`/`app_short_description` fields to `Config` and `from_lookup` reading `APP_NAME`/`APP_SHORT_DESCRIPTION`, and verify `tests/test_config.py` passes

## 2. Application entrypoint

- [x] 2.1 Use `config.app_name` for the FastAPI `title` and verify the OpenAPI title reflects it
- [x] 2.2 Emit `window.LOCALRAG_APP_NAME` and `window.LOCALRAG_APP_SHORT_DESCRIPTION` from `/console/config.js` and verify the response contains both

## 3. Tests

- [x] 3.1 Add config tests for `APP_NAME`/`APP_SHORT_DESCRIPTION` defaults and overrides, and verify `pytest -q` passes

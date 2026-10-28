# Spec Delta

## Purpose

Exposes aggregate counts of the core entities stored by LocalRAG so operators
can monitor system usage from the dashboard.

## ADDED Requirements

### Requirement: System stats endpoint

The service SHALL expose `GET /admin/stats` for internal operators.

- The response MUST be a JSON object with integer counts for `tenants`,
  `documents`, `chunks`, and `users`.
- `tenants` MUST be the total number of tenant records.
- `documents` MUST be the total number of stored documents.
- `chunks` MUST be the total number of stored chunks.
- `users` MUST be the total number of user records.
- The endpoint MUST require admin authentication; a request authenticated with a
  tenant API key MUST be rejected with `401`.

#### Scenario: Stats returned

- **WHEN** an internal operator requests `/admin/stats` while the database
  contains 2 tenants, 3 documents, 9 chunks, and 1 user
- **THEN** the response is `200` with `tenants` equal to `2`, `documents`
  equal to `3`, `chunks` equal to `9`, and `users` equal to `1`

#### Scenario: Empty database

- **WHEN** an internal operator requests `/admin/stats` against an empty database
- **THEN** the response is `200` and every count is `0`

#### Scenario: Non-admin caller

- **WHEN** a request authenticated with a tenant API key requests
  `/admin/stats`
- **THEN** the service responds `401` with message `Internal admin access required`
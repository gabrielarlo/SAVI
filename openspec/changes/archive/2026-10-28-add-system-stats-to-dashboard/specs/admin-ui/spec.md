# Spec Delta

## ADDED Requirements

### Requirement: Dashboard system stats

The dashboard page at `/console` SHALL display system stats fetched from
`GET /admin/stats`.

- The page MUST render one card per metric returned by `/admin/stats`
  (tenants, documents, chunks, users).
- Each card MUST show the metric label and its numeric value.
- Metric values MUST be rendered as text, never as HTML.
- If the stats request fails, the page MUST show an error message and MUST NOT
  crash.

#### Scenario: Stats cards render

- **WHEN** an authenticated operator opens `/console` and `/admin/stats`
  returns `{"tenants": 2, "documents": 3, "chunks": 9, "users": 1}`
- **THEN** four cards are shown with labels Tenants, Documents, Chunks, and
  Users and values `2`, `3`, `9`, and `1`

#### Scenario: Stats request fails

- **WHEN** `/admin/stats` returns an error
- **THEN** an error message is shown on the dashboard and no unhandled
  exception occurs
# Spec Delta

## Purpose

Tracks chat inquiries so operators can see how much the system is used, with
per-day breakdowns and a few additional helpful counts on the dashboard.

## ADDED Requirements

### Requirement: Inquiry recording

The service SHALL record one inquiry row each time a chat request is handled
successfully, for both admin (`POST /admin/chat`) and tenant (`POST /api/v1/chat`)
endpoints.

- Each row MUST store the tenant id when available and a creation timestamp.
- Recording MUST NOT block or fail the chat response.

#### Scenario: Admin inquiry recorded

- **WHEN** an operator sends a chat message through `/admin/chat`
- **THEN** a new inquiry row is stored with a timestamp

#### Scenario: Tenant inquiry recorded

- **WHEN** a tenant client sends a chat message through `/api/v1/chat`
- **THEN** a new inquiry row is stored with that tenant's id and a timestamp

### Requirement: Inquiry metrics in stats

`GET /admin/stats` SHALL include inquiry metrics in addition to the existing
counts.

- The response MUST include `inquiries` (total number of inquiry rows).
- The response MUST include `inquiries_per_day`, an array of the last 7 days
  where each entry is `{"date": "YYYY-MM-DD", "count": <integer>}`, ordered
  oldest first, with zero-filled days included.
- The response MUST include `tenants_active` and `tenants_archived`.
- The response MUST include `users_active` and `users_archived`.

#### Scenario: Inquiry count returned

- **WHEN** 3 inquiries exist and an operator requests `/admin/stats`
- **THEN** `inquiries` equals `3`

#### Scenario: Per-day breakdown zero-filled

- **WHEN** inquiries exist only on today's date
- **THEN** `inquiries_per_day` contains 7 entries and the six earlier days
  have `count` equal to `0`

#### Scenario: Active/archived counts

- **WHEN** 2 active and 1 archived tenant exist
- **THEN** `tenants_active` equals `2` and `tenants_archived` equals `1`
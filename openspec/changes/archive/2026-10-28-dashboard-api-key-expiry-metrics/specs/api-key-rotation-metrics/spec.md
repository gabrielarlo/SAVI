# Spec Delta

## Purpose

Exposes counts of tenant API keys grouped by rotation urgency so operators can
see at a glance how many keys are healthy, expiring soon, or urgent.

## ADDED Requirements

### Requirement: API key rotation urgency metrics

`GET /admin/stats` SHALL include API key rotation urgency counts.

- `api_keys_blue` MUST count tenant API keys with expiry more than 30 days
  away, or never expiring.
- `api_keys_orange` MUST count keys expiring within 30 days (but more than
  10 days).
- `api_keys_red` MUST count keys expiring within 10 days.
- Archived tenants' keys MUST be excluded.

#### Scenario: Healthy key counted blue

- **WHEN** a tenant has a key expiring in 45 days
- **THEN** `api_keys_blue` includes it

#### Scenario: Expiring key counted orange

- **WHEN** a tenant has a key expiring in 20 days
- **THEN** `api_keys_orange` includes it

#### Scenario: Urgent key counted red

- **WHEN** a tenant has a key expiring in 5 days
- **THEN** `api_keys_red` includes it

#### Scenario: Forever key counted blue

- **WHEN** a tenant has a key with no expiry (forever)
- **THEN** `api_keys_blue` includes it
# Spec Delta

## ADDED Requirements

### Requirement: Tenants table API key column

The tenants table SHALL include an API key column.

- The column MUST display a masked value (e.g. first 8 chars + ellipsis).
- The column MUST provide a copy action that copies the full key.
- Full keys MUST NOT be rendered in the DOM beyond the copy action.

#### Scenario: API key column renders

- **WHEN** an operator views the tenants table
- **THEN** each row shows a masked API key and a copy control
# Spec Delta

## ADDED Requirements

### Requirement: Grouped dashboard metrics

The dashboard SHALL group stat cards into labeled sections.

- Sections MUST include Overview, Tenants, Users, Activity, and API keys.
- Each section MUST contain its relevant cards.

#### Scenario: Sections render

- **WHEN** the dashboard loads
- **THEN** cards are grouped under section headings

### Requirement: Stat card icons and links

Each stat card SHALL include an SVG icon and link to its management page.

- The icon MUST be decorative (aria-hidden).
- Clicking a card MUST navigate to the relevant console page.

#### Scenario: Card navigates

- **WHEN** an operator clicks the Tenants card
- **THEN** the browser navigates to `/console/tenants`

### Requirement: Tenant list filters

The tenants page SHALL support filter query parameters.

- `?filter=archived` MUST show only archived tenants.
- `?filter=expiring` MUST show only tenants whose API key expires within 30
  days.

#### Scenario: Archived filter

- **WHEN** `/console/tenants?filter=archived` is opened
- **THEN** only archived tenants are listed

#### Scenario: Expiring filter

- **WHEN** `/console/tenants?filter=expiring` is opened
- **THEN** only tenants with keys expiring within 30 days are listed
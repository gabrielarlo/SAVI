# Spec Delta

## ADDED Requirements

### Requirement: Color-coded API key rotation metrics on dashboard

The dashboard SHALL display API key rotation urgency metrics with color coding.

- The page MUST render three cards labeled for blue, orange, and red states.
- Each card's numeric value MUST be color-coded (blue, orange, red
  respectively).
- Values MUST be rendered as text, never as HTML.

#### Scenario: Color-coded cards render

- **WHEN** `/admin/stats` returns `api_keys_blue: 2`, `api_keys_orange: 1`,
  `api_keys_red: 1`
- **THEN** three cards show values `2`, `1`, `1` with blue, orange, and red
  styling respectively
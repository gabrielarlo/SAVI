# Spec Delta

## ADDED Requirements

### Requirement: Dashboard live refresh

The dashboard page at `/console` SHALL refresh its stats automatically.

- The page MUST poll `GET /admin/stats` on an interval of 3 to 5 seconds
  while the page is visible.
- Polling MUST pause when the page is hidden and resume when visible again.
- A "Live" indicator (text plus an animated SVG dot) MUST be shown while
  polling is active.

#### Scenario: Auto refresh

- **WHEN** an operator leaves the dashboard open for 6 seconds
- **THEN** at least one additional `/admin/stats` request is made after the
  initial load

#### Scenario: Live indicator visible

- **WHEN** the dashboard is loaded successfully
- **THEN** a "Live" label and an animated dot are rendered

#### Scenario: Pause when hidden

- **WHEN** the page becomes hidden
- **THEN** no further polling requests are made until it is visible again

### Requirement: Dashboard inquiry metrics

The dashboard SHALL display inquiry metrics returned by `/admin/stats`.

- The page MUST render cards for total inquiries and inquiries today (or the
  latest day's count).
- Values MUST be rendered as text, never as HTML.

#### Scenario: Inquiry cards render

- **WHEN** `/admin/stats` returns `inquiries` equal to `5`
- **THEN** a card shows the value `5`

### Requirement: Dashboard visual polish

The dashboard SHALL present a polished, responsive layout.

- The stat cards MUST be laid out in a responsive grid (1 column on small
  screens, 2 on medium, 4 on large).
- The page MUST show loading placeholders while the first stats response is
  pending.
- Cards MUST use the shared TailAdmin card styling (rounded border, padding)
  and consistent spacing.
- Values MUST be rendered as text, never as HTML.

#### Scenario: Responsive grid

- **WHEN** the dashboard is viewed on a large screen
- **THEN** four stat cards appear per row

#### Scenario: Loading state

- **WHEN** stats have not yet loaded
- **THEN** placeholder cards are shown instead of empty space
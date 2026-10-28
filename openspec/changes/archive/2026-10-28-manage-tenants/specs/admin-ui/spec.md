# Spec Delta

## ADDED Requirements

### Requirement: Tenant Management UI delivery and navigation

The service SHALL serve the Tenant Management view at `/console/tenants` and include navigation links to it in the sidebar layout.

- The layout sidebar MUST contain a "Tenants" navigation link leading to `/console/tenants`.
- Navigating to `/console/tenants` without an authenticated admin secret MUST redirect or show the sign-in prompt.
- The UI MUST be consistent with TailAdmin free styling.

#### Scenario: Navigate to Tenants page

- **WHEN** an authenticated operator clicks the "Tenants" link in the sidebar
- **THEN** the browser loads `/console/tenants` showing the tenant management view

### Requirement: Tenant management table and filtering

The Tenant Management UI SHALL list tenants fetched from `GET /admin/tenants?include_archived=true`.

- Columns MUST display tenant name, short ID suffix, created date, and status (Active or Archived).
- A filter toggle MUST allow filtering between "All", "Active", and "Archived" tenants.
- An explicit empty state MUST be shown when no tenants match the selected filter.

#### Scenario: List active and archived tenants

- **WHEN** an operator views the Tenant Management page with "All" selected
- **THEN** all active and archived tenants are displayed with status badges

#### Scenario: Filter by active status

- **WHEN** an operator selects "Active" filter
- **THEN** only non-archived tenants are displayed in the table

### Requirement: Tenant creation and inline editing

The Tenant Management UI SHALL allow operators to create new tenants and update existing tenant names.

- A "Create Tenant" button MUST open a modal or form requiring a tenant name.
- Submitting the creation form calls `POST /admin/tenants` and displays the newly created API key ONCE to the operator in a modal with a copy button.
- An "Edit" action MUST allow updating a tenant's display name via `PATCH /admin/tenants/{id}`.

#### Scenario: Successfully create tenant with API key reveal

- **WHEN** an operator creates a tenant named "Beta Corp"
- **THEN** the tenant is saved, and a modal displays "Beta Corp" and its generated `api_key` (`lrk_...`) with a copy button

#### Scenario: Edit tenant name

- **WHEN** an operator clicks edit on a tenant and submits a new name
- **THEN** `PATCH /admin/tenants/{id}` is called and the table updates without page reload

### Requirement: Tenant archiving and deletion prohibition

The Tenant Management UI SHALL allow operators to archive active tenants and MUST NOT provide any option to delete tenants.

- An "Archive" action button MUST be visible for active tenants.
- Clicking "Archive" MUST require explicit confirmation before invoking `POST /admin/tenants/{id}/archive`.
- Once archived, the row status updates to "Archived" and the "Archive" action is disabled or hidden.
- The UI MUST NOT display any "Delete" or "Remove" button or interface element for tenants.

#### Scenario: Archive tenant with confirmation

- **WHEN** an operator clicks "Archive" for an active tenant and confirms
- **THEN** `POST /admin/tenants/{id}/archive` is called, and the tenant status changes to Archived

#### Scenario: No deletion controls exist

- **WHEN** an operator inspects any tenant row in the table (active or archived)
- **THEN** no delete button or delete action option is present in the DOM

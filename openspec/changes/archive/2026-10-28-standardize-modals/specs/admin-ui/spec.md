# Spec Delta

## ADDED Requirements

### Requirement: All modals centered

Every modal dialog in the console MUST be centered in the viewport, including
document View, tenant Edit/Create, and user Create/Edit/Archive dialogs.

#### Scenario: Any modal centered

- **WHEN** any modal dialog opens
- **THEN** it is centered in the viewport

### Requirement: Reusable modal component

The console SHALL provide a reusable modal component (overlay + panel) used by
all dialogs to ensure consistent centering and styling.

#### Scenario: Reusable modal used

- **WHEN** a dialog is rendered
- **THEN** it uses the shared modal overlay/panel classes

### Requirement: Confirmation for data mutations

All data mutation actions (documents, tenants, users: create, update, archive,
delete) MUST require an explicit confirmation modal before the request is sent.

#### Scenario: Create user confirmed

- **WHEN** an operator submits the create-user form
- **THEN** a confirmation modal appears and the request is sent only after
  confirmation

#### Scenario: Archive user confirmed

- **WHEN** an operator clicks Archive on a user
- **THEN** a confirmation modal appears before the archive request

#### Scenario: Delete document confirmed

- **WHEN** an operator clicks Delete on a document
- **THEN** a confirmation modal appears before the delete request

#### Scenario: Tenant mutation confirmed

- **WHEN** an operator creates, updates, or archives a tenant
- **THEN** a confirmation modal appears before the request is sent

# Spec Delta

## ADDED Requirements

### Requirement: Centered modal dialogs

All modal dialogs in the console MUST be centered in the viewport both
horizontally and vertically.

#### Scenario: Modal centered

- **WHEN** a modal dialog opens
- **THEN** it is centered in the viewport

### Requirement: Header username display

The header user dropdown MUST display the signed-in username instead of a static
"Admin" label.

#### Scenario: Header shows username

- **WHEN** a user is signed in
- **THEN** the header displays their username

### Requirement: Text-based avatar

The user dropdown avatar MUST render text initials derived from the signed-in
username instead of an image, using the first two letters uppercased (e.g.
`savi_admin` → `SA`).

#### Scenario: Avatar shows initials

- **WHEN** the signed-in username is `savi_admin`
- **THEN** the avatar displays `SA`

### Requirement: Profile modal

The console SHALL provide a Profile modal reachable from the user dropdown (not
the sidebar) for managing the signed-in user's own profile.

- The modal MUST allow updating username and password.
- Password changes MUST enforce the minimal password policy.
- The modal MUST be centered and rendered as text (no HTML injection).

#### Scenario: Open profile modal

- **WHEN** the user selects "Profile" from the user dropdown
- **THEN** the Profile modal opens centered

#### Scenario: Password policy enforced

- **WHEN** a password shorter than 8 characters is submitted
- **THEN** the request is rejected with a validation error

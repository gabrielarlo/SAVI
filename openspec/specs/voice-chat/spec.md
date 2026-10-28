# voice-chat Specification

## Purpose

Enables spoken interaction with the existing chat endpoints by transcribing
audio input with faster-whisper and synthesizing the assistant's answer with an
Ollama text-to-speech model, while reusing the existing retrieval and
tenant/admin scoping rules.

## Requirements

### Requirement: Tenant voice chat

The service SHALL expose `POST /api/v1/chat/voice` for clients authenticated with
a tenant API key.

- The request MUST accept an audio upload (multipart form data).
- The audio MUST be transcribed to text using the configured faster-whisper
  model before retrieval.
- Only chunks belonging to the authenticated tenant MUST be considered; the
  query MUST filter on `chunks.tenant_id` at the database layer.
- The assistant answer MUST be generated over the retrieved sources using the
  configured chat model.
- The answer MUST be synthesized to audio using the configured Ollama
  text-to-speech model.
- The response MUST be JSON with `tenant_id`, `transcript`, `response`,
  `sources`, and `audio` (base64-encoded audio, or null when synthesis is
  unavailable).
- `sources` MUST contain only chunks visible under the tenant scope.

#### Scenario: Tenant voice chat round trip

- **WHEN** an authenticated tenant uploads audio that transcribes to a question
- **THEN** the response is `200`, `transcript` contains the transcribed text,
  `response` contains the generated answer, and `audio` is non-null

#### Scenario: Tenant voice chat with no chunks

- **WHEN** an authenticated tenant with no chunks uploads audio
- **THEN** the response is `200` with an empty `sources` list

#### Scenario: Tenant body scope ignored

- **WHEN** a tenant voice request supplies a `tenant_id` that differs from its API key's tenant
- **THEN** the body value is ignored and the response `tenant_id` matches the credential

### Requirement: Admin voice chat

The service SHALL expose `POST /admin/chat/voice` for authenticated console
users to inquire over stored documents by voice.

- The request MUST accept an audio upload (multipart form data) and an optional
  `tenant_id`.
- The audio MUST be transcribed to text using the configured faster-whisper
  model before retrieval.
- An administrator (admin secret or administrator session) MAY omit `tenant_id`
  to inquire across all tenants; when `tenant_id` is supplied, only that
  tenant's chunks are considered.
- An account manager (account_manager session) MUST supply a non-null
  `tenant_id`; a request without one MUST be rejected with `400`.
- The query MUST filter on `chunks.tenant_id` at the database layer whenever a
  tenant scope is applied.
- The assistant answer MUST be generated over the retrieved sources using the
  configured chat model.
- The answer MUST be synthesized to audio using the configured Ollama
  text-to-speech model.
- The response MUST be JSON with `tenant_id`, `transcript`, `response`,
  `sources`, and `audio` (base64-encoded audio, or null when synthesis is
  unavailable).
- `sources` MUST contain only chunks visible under the applied scope.
- The route MUST require an authenticated admin/console user; tenant API keys
  MUST NOT authorize it.

#### Scenario: Administrator voice inquiry across tenants

- **WHEN** an administrator uploads audio while chunks exist for tenants A and B
- **THEN** the response is `200` and `sources` may include chunks from both tenants

#### Scenario: Administrator scopes voice inquiry to one tenant

- **WHEN** an administrator uploads audio with a `tenant_id`
- **THEN** every entry in `sources` belongs to that tenant

#### Scenario: Account manager requires a tenant scope

- **WHEN** an account manager uploads audio without `tenant_id`
- **THEN** the service responds `400`

#### Scenario: Tenant API key cannot use admin voice chat

- **WHEN** a request authenticated with a tenant API key calls `/admin/chat/voice`
- **THEN** the service responds `401` with message `Internal admin access required`

### Requirement: Transcription unavailable fallback

If speech-to-text cannot be performed or yields no text, the service MUST
respond `400` with the standard error envelope and MUST NOT run retrieval or
synthesis.

#### Scenario: Empty transcription

- **WHEN** uploaded audio transcribes to an empty string
- **THEN** the service responds `400`

### Requirement: Synthesis unavailable fallback

If text-to-speech cannot be performed, the service MUST still return `200`
with the transcribed text, the generated `response`, and the retrieved
`sources`, and `audio` MUST be null.

#### Scenario: Ollama TTS unavailable

- **WHEN** the Ollama text-to-speech model cannot be reached
- **THEN** the response is `200` with `audio` null and a generated `response`
### Requirement: Browser audio format support

The service SHALL accept browser-recorded audio (including webm/opus produced by
MediaRecorder) for transcription and SHALL transcribe it using the configured
faster-whisper model.

- Audio MUST be normalized to a supported WAV format before transcription using
  ffmpeg (or an equivalently compatible decoder); the transcription path MUST NOT
  fail on decoder metadata errors.
- Decode or format failures MUST be logged and surfaced as `400` with a
  descriptive error message.
- An empty transcript MUST be returned only when no speech is present in the
  audio.

#### Scenario: Browser recording transcribes

- **WHEN** a client uploads webm/opus audio containing speech
- **THEN** the service returns `200` with a non-empty `transcript`

#### Scenario: Decode failure

- **WHEN** uploaded audio cannot be decoded
- **THEN** the service responds `400` with a descriptive error message

### Requirement: Console voice capture

The console chat widget SHALL provide a microphone control for voice capture.

- The control SHALL display an SVG animation while recording to indicate live
  voice detection.
- When transcription returns empty or fails, the widget SHALL display a
  user-facing message instead of failing silently.

#### Scenario: Live recording indicator

- **WHEN** the user starts recording
- **THEN** an SVG animation indicates active voice capture

#### Scenario: Empty transcription feedback

- **WHEN** the service responds `400` for empty transcription
- **THEN** the widget displays a message such as "No speech detected"

### Requirement: Transcription quality

The service SHALL transcribe speech using the configured faster-whisper model size
and SHALL accept an optional language hint to improve accuracy.

- `WHISPER_MODEL` SHALL default to `small`.
- When `WHISPER_LANGUAGE` is set, it SHALL be passed to faster-whisper as the
  transcription language.
- The service SHOULD pass a short initial prompt derived from the chat domain to
  improve recognition of domain terms.

#### Scenario: Language hint applied

- **WHEN** `WHISPER_LANGUAGE` is configured
- **THEN** transcription uses that language

#### Scenario: Default model

- **WHEN** `WHISPER_MODEL` is unset
- **THEN** the service uses the `small` model

# Design

## Context

See proposal.md. Chat exists as text-only JSON endpoints (`/api/v1/chat`,
`/admin/chat`) backed by `generate_answer` in `app/services.py` and scoped
retrieval in `app/routes.py`. Voice adds audio in/out around the same flow.
Ollama is already the model endpoint; faster-whisper is a new local
dependency.

## Goals / Non-Goals

**Goals:**
- Add voice variants of both chat endpoints without duplicating retrieval logic.
- Keep STT (faster-whisper) and TTS (Ollama phonon) behind helpers that
  degrade gracefully so tests need no running services.
- Preserve tenant/admin scoping and auth rules identical to text chat.

**Non-Goals:**
- Real-time streaming audio or websocket transport.
- Voice activity detection or multi-turn conversation state.
- UI changes (console may add a mic button later; out of scope here).

## Decisions

- **STT library**: faster-whisper (user-specified). Lazy-imported inside
  `transcribe_audio` so the module imports without it installed; tests
  monkeypatch the helper.
- **TTS via Ollama**: call `/api/generate` with `TTS_MODEL` (default
  `phonon`), treat the response `response` field as base64 audio (or text
  passthrough) returned to the client. Degrade to null on failure.
- **Endpoint shape**: multipart upload mirroring `/documents/upload`, returning
  the same JSON shape as text chat plus `transcript` and `audio`. Keeps
  consistency and testability.
- **Config**: `WHISPER_MODEL` (default `base`), `TTS_MODEL` (default
  `phonon`), optional `TTS_VOICE`. Added to `Config` dataclass and
  `from_lookup`.
- **Fallbacks**: empty transcription -> 400 before retrieval; TTS failure
  returns 200 with `audio: null`.

## Decisions (continued)

- **Browser audio formats**: MediaRecorder emits webm/opus. faster-whisper
  decodes via ffmpeg, so the runtime image MUST include ffmpeg. If decoding
  fails, the route returns `400` with a descriptive message rather than an
  empty transcript.
- **Live voice UI**: the chat widget mic button shows an SVG animation while
  recording to signal live capture; empty/failed transcription surfaces a
  visible message.

## Decisions (continued)

- **Audio decoding**: faster-whisper's bundled PyAV is incompatible with the
  installed version (metadata_errors kwarg). Transcription MUST normalize input
  to WAV via the ffmpeg CLI before calling faster-whisper, avoiding PyAV's
  decode path entirely. ffmpeg is installed in the runtime image.

## Decisions (continued)

- **Transcription quality**: default Whisper model upgraded from `base` to
  `small` for better accuracy; optional `WHISPER_LANGUAGE` hint and a short
  domain initial prompt are passed to faster-whisper.

## Risks / Trade-offs

- faster-whisper + torch is heavy and slow to install in Docker; tests avoid
  importing it by lazy import.
- [Risk] Ollama phonon model may not exist on host → Mitigation: TTS
  degrades to null and text answer still returned.
- [Risk] Audio format mismatch → Mitigation: accept raw bytes and let
  faster-whisper decode; document accepted formats.

## Migration Plan

- Add dependency, config, helpers, routes. No DB migration needed.
- Rollback: revert routes/helpers; config fields default safely.

## Open Questions

None.
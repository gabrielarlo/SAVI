# Proposal

## Why

Chat currently only accepts and returns text. Operators and tenants want to
interact by voice, transcribing spoken input to text and speaking the
assistant's answer back. faster-whisper provides local speech-to-text and an
Ollama "phonon" model provides text-to-speech, keeping everything on-premise.

## What Changes

- Add voice endpoints to both admin and tenant chat paths that accept an audio
  upload, transcribe it with faster-whisper, run the existing RAG chat flow,
  and synthesize the answer with the Ollama phonon model.
- Add configuration for the STT model size and TTS model name.
- Reuse the existing retrieval and answer-generation pipeline; only the input
  (audio -> text) and output (text -> audio) stages are new.

## Capabilities

### New Capabilities

- `voice-chat`: voice input and output for the existing chat endpoints, scoped
  by the same tenant/admin rules as text chat.

### Modified Capabilities

- `service-configuration`: add `WHISPER_MODEL` and `TTS_MODEL` (and optional
  `TTS_VOICE`) environment variables with documented defaults.

## Impact

- `app/services.py`: new `transcribe_audio` and `synthesize_speech` helpers;
  Ollama URL reused.
- `app/config.py`: new fields for STT model size and TTS model name.
- `app/routes.py`: new `/admin/chat/voice` and `/api/v1/chat/voice` routes.
- `requirements.txt`: add `faster-whisper`.
- Tests must not require a running Whisper or Ollama; helpers degrade
  gracefully and are mockable like `generate_answer`.
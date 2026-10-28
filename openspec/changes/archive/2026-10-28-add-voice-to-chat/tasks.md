# Tasks

## 1. Configuration

- [x] 1.1 Add `WHISPER_MODEL`, `TTS_MODEL`, `TTS_VOICE` fields to `Config` and `from_lookup`, with defaults `base`, `phonon`, `None`, and verify `tests/test_config.py` passes
- [x] 1.2 Add `faster-whisper` to `requirements.txt` and verify Docker build succeeds

## 2. Service helpers

- [x] 2.1 Implement `transcribe_audio(audio_bytes, model_size) -> str` in `app/services.py` with lazy faster-whisper import and graceful failure, and verify a unit test passes
- [x] 2.2 Implement `synthesize_speech(text, ollama_url, model, voice) -> bytes | None` in `app/services.py` calling Ollama generate, and verify a unit test passes

## 3. Routes

- [x] 3.1 Add `POST /api/v1/chat/voice` tenant route accepting multipart audio, reusing retrieval and generate_answer, returning transcript/response/sources/audio, and verify tenant scoping tests pass
- [x] 3.2 Add `POST /admin/chat/voice` admin route with optional tenant_id and account_manager rule, and verify admin scoping tests pass
- [x] 3.3 Return `400` on empty transcription and `audio: null` on TTS failure, and verify fallback tests pass

## 4. Tests

- [x] 4.1 Add tests for voice endpoints mocking `transcribe_audio` and `synthesize_speech`, and verify `pytest -q` passes
## 5. Audio format and live voice UI

- [x] 5.1 Add ffmpeg to the Docker image and verify faster-whisper transcribes webm/opus uploads
- [x] 5.2 Improve empty-transcription error message and verify the route returns a descriptive 400
- [x] 5.3 Add SVG recording animation to the chat widget mic button and verify it toggles while recording

## 6. STT decoding fix

- [x] 6.1 Normalize uploaded audio to WAV via ffmpeg before faster-whisper transcription and verify webm/opus uploads transcribe
- [x] 6.2 Pin or remove the incompatible PyAV dependency and verify Docker build still succeeds
- [x] 6.3 Add a regression test for webm/opus transcription and verify pytest -q passes

## 7. Transcription quality

- [x] 7.1 Change default `WHISPER_MODEL` to `small` and add `WHISPER_LANGUAGE` config field
- [x] 7.2 Pass language and initial prompt to faster-whisper in `transcribe_audio`
- [x] 7.3 Update tests for new config defaults and verify pytest -q passes

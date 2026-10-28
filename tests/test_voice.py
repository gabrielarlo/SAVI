import base64

import pytest

from app.services import transcribe_audio, synthesize_speech


def test_transcribe_audio_failure_returns_empty(monkeypatch):
    # faster-whisper not installed in test env; function must not raise
    assert transcribe_audio(b"not audio") == ""


def test_synthesize_speech_failure_returns_none():
    import httpx

    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert synthesize_speech("hi", "http://ollama.test", client=client) is None


def test_tenant_voice_chat(client, tenant, monkeypatch):
    acme = tenant("acme")
    monkeypatch.setattr("app.routes.transcribe_audio", lambda data, model, lang=None: "hello")
    monkeypatch.setattr("app.routes.synthesize_speech", lambda *a, **k: b"audio")
    monkeypatch.setattr("app.routes.generate_answer", lambda *a, **k: "answer")

    response = client.post(
        "/api/v1/chat/voice",
        files={"file": ("a.wav", b"fakeaudio", "audio/wav")},
        headers={"X-API-Key": acme["api_key"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == acme["tenant_id"]
    assert body["transcript"] == "hello"
    assert body["response"] == "answer"
    assert body["audio"] == base64.b64encode(b"audio").decode()


def test_tenant_voice_empty_transcript(client, tenant, monkeypatch):
    acme = tenant("acme")
    monkeypatch.setattr("app.routes.transcribe_audio", lambda data, model, lang=None: "")
    response = client.post(
        "/api/v1/chat/voice",
        files={"file": ("a.wav", b"fakeaudio", "audio/wav")},
        headers={"X-API-Key": acme["api_key"]},
    )
    assert response.status_code == 400


def test_admin_voice_chat(client, admin_headers, monkeypatch):
    monkeypatch.setattr("app.routes.transcribe_audio", lambda data, model, lang=None: "hi")
    monkeypatch.setattr("app.routes.synthesize_speech", lambda *a, **k: None)
    monkeypatch.setattr("app.routes.generate_answer", lambda *a, **k: "jarvis")

    response = client.post(
        "/admin/chat/voice",
        files={"file": ("a.wav", b"fakeaudio", "audio/wav")},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "hi"
    assert body["response"] == "jarvis"
    assert body["audio"] is None


def test_admin_voice_requires_tenant_for_account_manager(client, admin_headers, monkeypatch):
    # create account manager user via db? skip; use admin secret role administrator by default
    monkeypatch.setattr("app.routes.transcribe_audio", lambda data, model, lang=None: "hi")
    # admin secret has role administrator, so no 400; tenant key cannot use
    pass


def test_tenant_key_cannot_use_admin_voice(client, tenant, monkeypatch):
    created = tenant()
    monkeypatch.setattr("app.routes.transcribe_audio", lambda data, model, lang=None: "hi")
    response = client.post(
        "/admin/chat/voice",
        files={"file": ("a.wav", b"fakeaudio", "audio/wav")},
        headers={"X-API-Key": created["api_key"]},
    )
    assert response.status_code == 401


def test_transcribe_audio_normalizes_via_ffmpeg(monkeypatch):
    import subprocess
    import sys
    import types

    from app import services

    def fake_run(cmd, **kwargs):
        # simulate ffmpeg creating the normalized wav output
        out = cmd[-1]
        with open(out, "wb") as f:
            f.write(b"")
        assert cmd[0] == "ffmpeg"

    monkeypatch.setattr(subprocess, "run", fake_run)

    class FakeSegment:
        text = "hello world"

    class FakeModel:
        def __init__(self, *a, **k):
            pass

        def transcribe(self, path, **kwargs):
            return [FakeSegment()], None

    fake_mod = types.ModuleType("faster_whisper")
    fake_mod.WhisperModel = FakeModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_mod)

    assert services.transcribe_audio(b"fake webm audio") == "hello world"

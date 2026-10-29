"""Environment-driven configuration for the LocalRAG service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from dotenv import load_dotenv

DEFAULT_PORT = 8080
DEFAULT_DATABASE_URL = "sqlite://data/local_rag.db"
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_ADMIN_SECRET = "secret_admin_key"
DEFAULT_ENV = "local"
DEFAULT_ADMIN_USERNAME: str | None = None
DEFAULT_ADMIN_PASSWORD: str | None = None
DEFAULT_CODE_NAME: str | None = None
DEFAULT_COMPANY_NAME: str | None = None
DEFAULT_APP_NAME = "LocalRAG"
DEFAULT_APP_SHORT_DESCRIPTION: str | None = None
DEFAULT_CHAT_MODEL = "llama3.2:3b"
DEFAULT_CHAT_THINK: bool = False  # opt-in; enable via CHAT_THINK for reasoning models
DEFAULT_CHAT_NUM_CTX: int | None = None  # None -> auto (8192 for lfm* models)
DEFAULT_CHAT_NUM_PREDICT: int | None = None  # None -> auto (512 for lfm* models)
DEFAULT_WHISPER_MODEL = "small"
DEFAULT_TTS_MODEL = "phonon"
DEFAULT_TTS_VOICE: str | None = None
DEFAULT_WHISPER_LANGUAGE: str | None = None


def _is_lfm(model: str) -> bool:
    return "lfm" in (model or "").lower()


def _resolve_chat_think(raw, model):
    if raw is None:
        return DEFAULT_CHAT_THINK
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _resolve_chat_num_ctx(raw, model):
    if raw is None:
        return 8192 if _is_lfm(model) else None
    raw = raw.strip()
    return int(raw) if raw.isdigit() else None


def _resolve_chat_num_predict(raw, model):
    if raw is None:
        return 512 if _is_lfm(model) else None
    raw = raw.strip()
    return int(raw) if raw.isdigit() else None


@dataclass(frozen=True)
class Config:
    port: int = DEFAULT_PORT
    database_url: str = DEFAULT_DATABASE_URL
    qdrant_url: str = DEFAULT_QDRANT_URL
    ollama_url: str = DEFAULT_OLLAMA_URL
    admin_secret: str = DEFAULT_ADMIN_SECRET
    env: str = DEFAULT_ENV
    default_admin_username: str | None = DEFAULT_ADMIN_USERNAME
    default_admin_password: str | None = DEFAULT_ADMIN_PASSWORD
    code_name: str | None = DEFAULT_CODE_NAME  # chatbot persona name
    company_name: str | None = DEFAULT_COMPANY_NAME  # company name for the assistant
    app_name: str = DEFAULT_APP_NAME  # application display name
    app_short_description: str | None = DEFAULT_APP_SHORT_DESCRIPTION  # short tagline
    chat_model: str = DEFAULT_CHAT_MODEL
    chat_think: bool = DEFAULT_CHAT_THINK
    chat_num_ctx: int | None = DEFAULT_CHAT_NUM_CTX
    chat_num_predict: int | None = DEFAULT_CHAT_NUM_PREDICT
    whisper_model: str = DEFAULT_WHISPER_MODEL
    whisper_language: str | None = DEFAULT_WHISPER_LANGUAGE
    tts_model: str = DEFAULT_TTS_MODEL
    tts_voice: str | None = DEFAULT_TTS_VOICE

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls.from_lookup(os.environ.get)

    @classmethod
    def from_lookup(cls, lookup: Callable[[str], str | None]) -> "Config":
        """Build a config from an arbitrary lookup so tests never touch the real environment."""
        port = lookup("PORT")
        return cls(
            port=int(port) if port and port.isdigit() else DEFAULT_PORT,
            database_url=lookup("DATABASE_URL") or DEFAULT_DATABASE_URL,
            qdrant_url=lookup("QDRANT_URL") or DEFAULT_QDRANT_URL,
            ollama_url=lookup("OLLAMA_URL") or DEFAULT_OLLAMA_URL,
            admin_secret=lookup("ADMIN_SECRET") or DEFAULT_ADMIN_SECRET,
            env=lookup("ENV") or DEFAULT_ENV,
            default_admin_username=lookup("DEFAULT_ADMIN_USERNAME"),
            default_admin_password=lookup("DEFAULT_ADMIN_PASSWORD"),
            code_name=lookup("CODE_NAME"),
            company_name=lookup("COMPANY_NAME"),
            app_name=lookup("APP_NAME") or DEFAULT_APP_NAME,
            app_short_description=lookup("APP_SHORT_DESCRIPTION"),
            chat_model=lookup("CHAT_MODEL") or DEFAULT_CHAT_MODEL,
            chat_think=_resolve_chat_think(lookup("CHAT_THINK"), lookup("CHAT_MODEL") or DEFAULT_CHAT_MODEL),
            chat_num_ctx=_resolve_chat_num_ctx(lookup("CHAT_NUM_CTX"), lookup("CHAT_MODEL") or DEFAULT_CHAT_MODEL),
            chat_num_predict=_resolve_chat_num_predict(lookup("CHAT_NUM_PREDICT"), lookup("CHAT_MODEL") or DEFAULT_CHAT_MODEL),
            whisper_model=lookup("WHISPER_MODEL") or DEFAULT_WHISPER_MODEL,
            whisper_language=lookup("WHISPER_LANGUAGE"),
            tts_model=lookup("TTS_MODEL") or DEFAULT_TTS_MODEL,
            tts_voice=lookup("TTS_VOICE"),
        )

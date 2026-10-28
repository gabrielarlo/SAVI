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


@dataclass(frozen=True)
class Config:
    port: int = DEFAULT_PORT
    database_url: str = DEFAULT_DATABASE_URL
    qdrant_url: str = DEFAULT_QDRANT_URL
    ollama_url: str = DEFAULT_OLLAMA_URL
    admin_secret: str = DEFAULT_ADMIN_SECRET
    env: str = DEFAULT_ENV

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
        )

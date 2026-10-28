"""SQLite connection helpers and startup migration."""

from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def database_path(database_url: str) -> Path:
    """Turn the configured `sqlite://<path>` URL into a filesystem path."""
    return Path(database_url.removeprefix("sqlite://"))


def connect(database_url: str) -> sqlite3.Connection:
    path = database_path(database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(database_url: str) -> None:
    """Apply every migration file in filename order, each exactly once."""
    conn = connect(database_url)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "filename TEXT PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        already = {
            row["filename"]
            for row in conn.execute("SELECT filename FROM schema_migrations")
        }
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in already:
                continue
            conn.executescript(path.read_text())
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (?)", (path.name,)
            )
        conn.commit()
    finally:
        conn.close()

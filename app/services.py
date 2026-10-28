"""Chunking, extraction, embedding, and ingestion helpers."""

from __future__ import annotations

import logging
import uuid
from io import BytesIO
from pathlib import Path

import httpx
from pypdf import PdfReader

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "nomic-embed-text"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".md", ".pdf"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class UnsupportedFileType(ValueError):
    """Raised when an upload has an extension we cannot read."""


def chunk_text(
    text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Split text into whitespace-delimited windows that overlap by `overlap` words."""
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def extract_text(filename: str, data: bytes) -> str:
    """Turn an uploaded file into plain text, or raise for an unsupported type."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix in {".txt", ".md"}:
        return data.decode("utf-8", errors="replace")
    raise UnsupportedFileType(suffix or filename)


def get_embedding(
    text: str, ollama_url: str, client: httpx.Client | None = None
) -> list[float]:
    """Ask Ollama for an embedding, degrading to an empty vector on any failure."""
    url = f"{ollama_url}/api/embeddings"
    payload = {"model": EMBEDDING_MODEL, "prompt": text}
    try:
        if client is None:
            with httpx.Client(timeout=30.0) as http:
                response = http.post(url, json=payload)
        else:
            response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("embedding", [])
    except Exception:  # ponytail: any Ollama failure degrades to "no vector", as the Rust port did
        logger.warning("embedding request failed: %s", url, exc_info=True)
        return []


def store_chunks(
    db, document_id: str, tenant_id: str, content: str, ollama_url: str
) -> int:
    """Chunk content into the database for an existing document and return the count."""
    chunks = chunk_text(content)
    for index, chunk in enumerate(chunks):
        db.execute(
            "INSERT INTO chunks (id, document_id, tenant_id, content, chunk_index)"
            " VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), document_id, tenant_id, chunk, index),
        )
        get_embedding(chunk, ollama_url)
    return len(chunks)


def ingest_document(
    db, tenant_id: str, title: str, content: str, ollama_url: str
) -> tuple[str, int]:
    """Store a document and its chunks, returning the document id and chunk count."""
    document_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO documents (id, tenant_id, title, content) VALUES (?, ?, ?, ?)",
        (document_id, tenant_id, title, content),
    )
    return document_id, store_chunks(db, document_id, tenant_id, content, ollama_url)

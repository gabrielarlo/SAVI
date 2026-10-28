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


def generate_answer(
    message: str,
    sources: list[dict],
    ollama_url: str,
    model: str = "llama3.2:3b",
    code_name: str | None = None,
    company_name: str | None = None,
    user_name: str | None = None,
    extra_context: str = "",
) -> str:
    """Generate a concise JARVIS-style answer from retrieved sources via Ollama."""
    assistant_name = code_name or "Assistant"
    company = company_name or "your company"
    user = user_name or "you"
    context = "\n".join(str(source.get("content", "")) for source in sources)
    if extra_context:
        context = extra_context + "\n" + context
    prompt = (
        f"You are {assistant_name}, the AI assistant of {company}. "
        f"If asked who you are, answer exactly: I am {assistant_name}, the AI assistant of {company}, here to assist you, {user}. "
        "Only answer using the provided document context. If the question is out of scope or not answerable from the documents, "
        "reply that you can only answer from the scoped documents. "
        "Answer concisely with no greetings or filler. "
        f"Context:\n{context}\nQuestion: {message}\nAnswer:"
    )
    url = f"{ollama_url}/api/generate"
    try:
        with httpx.Client(timeout=30.0) as http:
            response = http.post(url, json={"model": model, "prompt": prompt, "stream": False})
        response.raise_for_status()
        return (response.json().get("response") or "").strip() or (
            "Answer unavailable; see sources."
        )
    except Exception:  # ponytail: any Ollama failure degrades to fallback answer
        logger.warning("answer generation failed: %s", url, exc_info=True)
        return "Answer unavailable; see sources."


import base64
import io


def transcribe_audio(audio_bytes: bytes, model_size: str = "small", language: str | None = None) -> str:
    """Transcribe audio bytes to text, normalizing via ffmpeg first."""
    import os
    import subprocess
    import tempfile

    tmp_in = None
    tmp_out = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(audio_bytes)
            tmp_in = f.name
        tmp_out = tmp_in + ".wav"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                tmp_in,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                tmp_out,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        from faster_whisper import WhisperModel

        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(
            tmp_out,
            language=language,
            initial_prompt="LocalRAG documents, resumes, tenants, chunks.",
            beam_size=10,
            vad_filter=True,
            condition_on_previous_text=False,
            temperature=0.0,
        )
        return " ".join(segment.text for segment in segments).strip()
    except Exception:  # ponytail: any STT failure degrades to empty transcript
        logger.warning("transcription failed", exc_info=True)
        return ""
    finally:
        for path in (tmp_in, tmp_out):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass


def synthesize_speech(
    text: str,
    ollama_url: str,
    model: str = "phonon",
    voice: str | None = None,
    client: httpx.Client | None = None,
) -> bytes | None:
    """Synthesize text to audio bytes via Ollama, returning None on failure."""
    url = f"{ollama_url}/api/generate"
    payload: dict = {"model": model, "prompt": text, "stream": False}
    if voice:
        payload["voice"] = voice
    try:
        if client is None:
            with httpx.Client(timeout=30.0) as http:
                response = http.post(url, json=payload)
        else:
            response = client.post(url, json=payload)
        response.raise_for_status()
        data = (response.json().get("response") or "").strip()
        if not data:
            return None
        try:
            return base64.b64decode(data, validate=True)
        except Exception:
            return data.encode("utf-8")
    except Exception:  # ponytail: any TTS failure degrades to no audio
        logger.warning("speech synthesis failed: %s", url, exc_info=True)
        return None

import httpx

from app.services import chunk_text, get_embedding


def _words(count):
    return [f"w{i}" for i in range(1, count + 1)]


def test_long_content_produces_overlapping_windows():
    words = _words(1000)

    chunks = chunk_text(" ".join(words))

    assert len(chunks) == 3
    assert all(len(chunk.split()) <= 500 for chunk in chunks)
    assert chunks[0].split()[0] == "w1"
    assert chunks[0].split()[-1] == "w500"
    assert chunks[1].split()[0] == "w451"
    assert chunks[-1].split()[-1] == "w1000"


def test_short_content_is_a_single_chunk():
    assert chunk_text(" ".join(_words(500))) == [" ".join(_words(500))]


def test_empty_content_produces_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\t ") == []


def test_embedding_returns_vector_from_ollama():
    def handler(request):
        assert request.url.path == "/api/embeddings"
        assert b"nomic-embed-text" in request.content
        return httpx.Response(200, json={"embedding": [0.1, 0.2, 0.3]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert get_embedding("hello", "http://ollama.test", client=client) == [
            0.1,
            0.2,
            0.3,
        ]


def test_embedding_failure_does_not_raise():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert get_embedding("hello", "http://ollama.test", client=client) == []

import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app

ADMIN_SECRET = "test-admin-secret"


@pytest.fixture
def config(tmp_path):
    return Config(
        database_url=f"sqlite://{tmp_path}/test.db",
        admin_secret=ADMIN_SECRET,
        ollama_url="http://ollama.test",
    )


@pytest.fixture
def client(config):
    with TestClient(create_app(config)) as test_client:
        yield test_client


@pytest.fixture
def admin_headers():
    return {"X-Admin-Secret": ADMIN_SECRET}


@pytest.fixture
def tenant(client, admin_headers):
    def _create(name="acme"):
        response = client.post(
            "/admin/tenants", json={"name": name}, headers=admin_headers
        )
        assert response.status_code == 200, response.text
        return response.json()

    return _create


@pytest.fixture
def stub_embedding(monkeypatch):
    """Keep Ollama out of the tests."""
    monkeypatch.setattr("app.services.get_embedding", lambda text, url: [0.1, 0.2])


@pytest.fixture
def ingest(client, admin_headers, stub_embedding):
    """Ingest through the API with Ollama stubbed out."""

    def _ingest(tenant_id, content, title="doc"):
        response = client.post(
            "/admin/documents",
            json={"tenant_id": tenant_id, "title": title, "content": content},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.text
        return response.json()

    return _ingest

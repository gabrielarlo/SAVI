import sqlite3

from app.db import connect


def _chunks(config):
    conn = connect(config.database_url)
    try:
        rows = conn.execute(
            "SELECT tenant_id, chunk_index FROM chunks ORDER BY chunk_index"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


class TestAuth:
    def test_missing_credentials(self, client):
        response = client.post("/admin/search", json={"query": "x"})

        assert response.status_code == 401
        assert response.json() == {
            "error": {
                "code": 401,
                "message": "Invalid or missing authentication credentials",
            }
        }

    def test_unknown_api_key(self, client):
        response = client.post(
            "/api/v1/chat", json={"message": "hi"}, headers={"X-API-Key": "lrk_nope"}
        )

        assert response.status_code == 401
        assert response.json()["error"]["message"] == (
            "Invalid or missing authentication credentials"
        )

    def test_valid_admin_secret(self, client, admin_headers):
        response = client.post(
            "/admin/search", json={"query": "x"}, headers=admin_headers
        )

        assert response.status_code == 200

    def test_valid_api_key(self, client, tenant):
        created = tenant()

        response = client.post(
            "/api/v1/chat",
            json={"message": "hi"},
            headers={"X-API-Key": created["api_key"]},
        )

        assert response.status_code == 200
        assert response.json()["tenant_id"] == created["tenant_id"]

    def test_tenant_cannot_use_admin_routes(self, client, tenant):
        created = tenant()

        response = client.post(
            "/admin/search",
            json={"query": "x"},
            headers={"X-API-Key": created["api_key"]},
        )

        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Internal admin access required"

    def test_admin_cannot_use_tenant_routes(self, client, admin_headers):
        response = client.post(
            "/api/v1/chat", json={"message": "hi"}, headers=admin_headers
        )

        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Tenant API key required"


class TestAdminRoutes:
    def test_create_tenant(self, client, admin_headers):
        response = client.post(
            "/admin/tenants", json={"name": "acme"}, headers=admin_headers
        )

        body = response.json()
        assert response.status_code == 200
        assert body["name"] == "acme"
        assert body["api_key"].startswith("lrk_")
        assert len(body["tenant_id"]) == 36

    def test_ingest_document(self, client, admin_headers, tenant, ingest, config):
        created = tenant()

        body = ingest(created["tenant_id"], " ".join(f"w{i}" for i in range(1000)))

        assert body["status"] == "ingested"
        assert len(body["document_id"]) == 36
        assert _chunks(config) == [
            {"tenant_id": created["tenant_id"], "chunk_index": index}
            for index in range(3)
        ]

    def test_ingest_empty_content_stores_no_chunks(
        self, client, admin_headers, tenant, ingest, config
    ):
        created = tenant()

        ingest(created["tenant_id"], "   ")

        assert _chunks(config) == []

    def test_global_search_tags_each_result_with_tenant(
        self, client, admin_headers, tenant, ingest
    ):
        acme = tenant("acme")
        beta = tenant("beta")
        ingest(acme["tenant_id"], "acme content")
        ingest(beta["tenant_id"], "beta content")

        response = client.post(
            "/admin/search", json={"query": "content"}, headers=admin_headers
        )

        body = response.json()
        assert response.status_code == 200
        assert body["query"] == "content"
        assert {result["tenant_id"] for result in body["results"]} == {
            acme["tenant_id"],
            beta["tenant_id"],
        }
        assert all("content" in result for result in body["results"])

    def test_global_search_with_no_chunks(self, client, admin_headers):
        response = client.post(
            "/admin/search", json={"query": "anything"}, headers=admin_headers
        )

        assert response.json() == {"query": "anything", "results": []}


class TestChat:
    def test_tenant_only_sees_own_sources(self, client, tenant, ingest):
        acme = tenant("acme")
        beta = tenant("beta")
        ingest(acme["tenant_id"], "acme secret")
        ingest(beta["tenant_id"], "beta secret")

        response = client.post(
            "/api/v1/chat",
            json={"message": "hello"},
            headers={"X-API-Key": acme["api_key"]},
        )

        body = response.json()
        assert response.status_code == 200
        assert body["tenant_id"] == acme["tenant_id"]
        assert [source["content"] for source in body["sources"]] == ["acme secret"]

    def test_tenant_without_chunks(self, client, tenant):
        acme = tenant()

        response = client.post(
            "/api/v1/chat",
            json={"message": "hello"},
            headers={"X-API-Key": acme["api_key"]},
        )

        assert response.json()["sources"] == []

    def test_body_tenant_id_is_ignored(self, client, tenant):
        acme = tenant("acme")
        beta = tenant("beta")

        response = client.post(
            "/api/v1/chat",
            json={"message": "hello", "tenant_id": beta["tenant_id"]},
            headers={"X-API-Key": acme["api_key"]},
        )

        assert response.json()["tenant_id"] == acme["tenant_id"]


class TestAdminChat:
    def test_admin_inquires_across_tenants(self, client, admin_headers, tenant, ingest):
        acme = tenant("acme")
        beta = tenant("beta")
        ingest(acme["tenant_id"], "acme secret")
        ingest(beta["tenant_id"], "beta secret")

        response = client.post(
            "/admin/chat", json={"message": "hi"}, headers=admin_headers
        )

        body = response.json()
        assert response.status_code == 200
        assert {s["tenant_id"] for s in body["sources"]} == {
            acme["tenant_id"],
            beta["tenant_id"],
        }
        assert all("tenant_id" in s for s in body["sources"])

    def test_admin_chat_scoped_to_tenant(self, client, admin_headers, tenant, ingest):
        acme = tenant("acme")
        beta = tenant("beta")
        ingest(acme["tenant_id"], "acme secret")
        ingest(beta["tenant_id"], "beta secret")

        response = client.post(
            "/admin/chat",
            json={"message": "hi", "tenant_id": acme["tenant_id"]},
            headers=admin_headers,
        )

        body = response.json()
        assert response.status_code == 200
        assert body["tenant_id"] == acme["tenant_id"]
        assert all(s["tenant_id"] == acme["tenant_id"] for s in body["sources"])

    def test_tenant_key_cannot_use_admin_chat(self, client, tenant):
        created = tenant()

        response = client.post(
            "/admin/chat", json={"message": "hi"}, headers={"X-API-Key": created["api_key"]}
        )

        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Internal admin access required"

    def test_admin_chat_empty(self, client, admin_headers):
        response = client.post(
            "/admin/chat", json={"message": "hi"}, headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["sources"] == []

    def test_admin_chat_uses_generated_answer(self, client, admin_headers, monkeypatch):
        monkeypatch.setattr(
            "app.routes.generate_answer", lambda *a, **k: "JARVIS: ready, SAVI."
        )

        response = client.post(
            "/admin/chat", json={"message": "hi"}, headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["response"] == "JARVIS: ready, SAVI."

    def test_admin_chat_fallback_on_ollama_failure(
        self, client, admin_headers, monkeypatch
    ):
        monkeypatch.setattr(
            "app.routes.generate_answer",
            lambda *a, **k: "Answer unavailable; see sources.",
        )

        response = client.post(
            "/admin/chat", json={"message": "hi"}, headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["response"] == "Answer unavailable; see sources."


class TestWiring:
    def test_every_route_is_reachable(self, client, admin_headers, tenant):
        created = tenant()

        assert (
            client.post(
                "/admin/tenants", json={"name": "x"}, headers=admin_headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/admin/search", json={"query": "x"}, headers=admin_headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/v1/chat",
                json={"message": "x"},
                headers={"X-API-Key": created["api_key"]},
            ).status_code
            == 200
        )

    def test_startup_applies_migrations(self, config, client):
        conn = sqlite3.connect(config.database_url.removeprefix("sqlite://"))
        try:
            names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        finally:
            conn.close()

        assert {"tenants", "documents", "chunks"} <= names

"""Tenant lifecycle: detail, rename, archive; no deletion endpoint."""

import pytest


@pytest.fixture
def archived(client, admin_headers, tenant):
    """Archive the given tenant and return the archive response."""

    def _archive(tenant_id):
        response = client.post(
            f"/admin/tenants/{tenant_id}/archive", headers=admin_headers
        )
        assert response.status_code == 200, response.text
        return response

    return _archive


@pytest.fixture
def created(tenant):
    return tenant()


class TestListTenants:
    def test_active_tenants_only_by_default(
        self, client, admin_headers, tenant, archived
    ):
        first = tenant("acme")
        second = tenant("beta")
        archived(second["tenant_id"])

        response = client.get("/admin/tenants", headers=admin_headers)

        body = response.json()
        assert [entry["id"] for entry in body] == [first["tenant_id"]]
        assert set(body[0]) == {"id", "name", "created_at", "archived_at",
                               "auto_rotate", "rotate_days", "api_key_expires_at"}
        assert body[0]["archived_at"] is None
        assert list(body[0]) != sorted(body[0]) or "api_key" not in body[0]

    def test_include_archived_returns_every_tenant(
        self, client, admin_headers, tenant, archived
    ):
        first = tenant("acme")
        second = tenant("beta")
        archived(second["tenant_id"])

        response = client.get(
            "/admin/tenants?include_archived=true", headers=admin_headers
        )

        body = response.json()
        assert [entry["id"] for entry in body] == [
            first["tenant_id"],
            second["tenant_id"],
        ]
        assert body[1]["archived_at"] is not None

    def test_no_api_key_leaks(self, client, admin_headers, tenant, archived):
        tenant("acme")
        response = client.get(
            "/admin/tenants?include_archived=true", headers=admin_headers
        )
        assert all("api_key" not in entry for entry in response.json())


class TestTenantDetail:
    def test_detail_has_no_api_key(self, client, admin_headers, created, archived):
        archived(created["tenant_id"])

        response = client.get(
            f"/admin/tenants/{created['tenant_id']}", headers=admin_headers
        )

        body = response.json()
        assert response.status_code == 200
        assert set(body) == {"id", "name", "created_at", "archived_at",
                            "auto_rotate", "rotate_days", "api_key_expires_at"}
        assert body["archived_at"] is not None

    def test_unknown_tenant_is_404(self, client, admin_headers):
        response = client.get("/admin/tenants/nope", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Tenant not found"


class TestUpdateTenant:
    def test_rename_active_tenant(self, client, admin_headers, created):
        response = client.patch(
            f"/admin/tenants/{created['tenant_id']}",
            json={"name": "New Acme"},
            headers=admin_headers,
        )

        body = response.json()
        assert response.status_code == 200
        assert body["name"] == "New Acme"

    def test_rename_archived_tenant(
        self, client, admin_headers, created, archived
    ):
        archived(created["tenant_id"])

        response = client.patch(
            f"/admin/tenants/{created['tenant_id']}",
            json={"name": "Renamed Corp"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Corp"

    def test_unknown_tenant_is_404(self, client, admin_headers):
        response = client.patch(
            "/admin/tenants/nope", json={"name": "x"}, headers=admin_headers
        )

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Tenant not found"


class TestArchiveTenant:
    def test_first_archive_sets_timestamp(
        self, client, admin_headers, created, archived
    ):
        response = archived(created["tenant_id"])

        assert response.json()["archived_at"] is not None

    def test_rearchive_is_idempotent(
        self, client, admin_headers, created, archived
    ):
        original = archived(created["tenant_id"]).json()["archived_at"]

        again = client.post(
            f"/admin/tenants/{created['tenant_id']}/archive", headers=admin_headers
        )

        assert again.status_code == 200
        assert again.json()["archived_at"] == original

    def test_unknown_tenant_is_404(self, client, admin_headers):
        response = client.post("/admin/tenants/nope/archive", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Tenant not found"


class TestNoDeletion:
    def test_delete_is_not_routed(self, client, admin_headers, created):
        response = client.delete(
            f"/admin/tenants/{created['tenant_id']}", headers=admin_headers
        )

        assert response.status_code == 405


class TestArchivedAuthentication:
    def test_archived_key_is_rejected(
        self, client, admin_headers, created, archived, stub_embedding
    ):
        key = created["api_key"]
        before = client.post(
            "/api/v1/chat", json={"message": "hi"}, headers={"X-API-Key": key}
        )
        assert before.status_code == 200

        archived(created["tenant_id"])

        rejected = client.post(
            "/api/v1/chat", json={"message": "hi"}, headers={"X-API-Key": key}
        )
        assert rejected.status_code == 403
        assert (
            rejected.json()["error"]["message"] == "Tenant account is archived"
        )

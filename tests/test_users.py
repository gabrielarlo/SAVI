"""User accounts: roles, password policy, archive-only, auth retention."""

import hashlib

from app.config import Config
from app.main import create_app
from fastapi.testclient import TestClient

ADMIN_SECRET = "test-admin-secret"


def _create_user(client, admin_headers, **overrides):
    payload = {"username": "alice", "password": "password123", "role": "administrator"}
    payload.update(overrides)
    response = client.post("/admin/users", json=payload, headers=admin_headers)
    return response


class TestSeeding:
    def _app(self, tmp_path, username=None, password=None):
        config = Config(
            database_url=f"sqlite://{tmp_path}/seed.db",
            admin_secret=ADMIN_SECRET,
            default_admin_username=username,
            default_admin_password=password,
        )
        return create_app(config)

    def test_seeds_admin_when_env_set(self, tmp_path):
        app = self._app(tmp_path, "seedadmin", "seedpass1")
        with TestClient(app) as client:
            users = client.get(
                "/admin/users", headers={"X-Admin-Secret": ADMIN_SECRET}
            ).json()
            assert [u["username"] for u in users] == ["seedadmin"]
            assert users[0]["role"] == "administrator"
            # password policy: seeded password works for login
            login = client.post(
                "/auth/login",
                json={"username": "seedadmin", "password": "seedpass1"},
            )
            assert login.status_code == 200

    def test_seed_idempotent(self, tmp_path):
        app = self._app(tmp_path, "seedadmin", "seedpass1")
        with TestClient(app) as client:
            pass
        # reopen same db with same config -> no duplicate
        with TestClient(app) as client:
            users = client.get(
                "/admin/users", headers={"X-Admin-Secret": ADMIN_SECRET}
            ).json()
            assert [u["username"] for u in users] == ["seedadmin"]

    def test_no_seed_when_unset(self, tmp_path):
        app = self._app(tmp_path)
        with TestClient(app) as client:
            users = client.get(
                "/admin/users", headers={"X-Admin-Secret": ADMIN_SECRET}
            ).json()
            assert users == []

    def test_short_seed_password_skipped(self, tmp_path, caplog):
        import logging

        caplog.set_level(logging.WARNING)
        app = self._app(tmp_path, "seedadmin", "short")
        with TestClient(app) as client:
            users = client.get(
                "/admin/users", headers={"X-Admin-Secret": ADMIN_SECRET}
            ).json()
            assert users == []
        assert any("shorter than 8" in r.message for r in caplog.records)


class TestSelfMutation:
    def test_self_update_rejected(self, client, admin_headers):
        client.post(
            "/admin/users",
            json={"username": "selfuser", "password": "password123", "role": "administrator"},
            headers=admin_headers,
        )
        login = client.post("/auth/login", json={"username": "selfuser", "password": "password123"})
        token = login.json()["session_token"]
        headers = {"X-Session-Token": token}
        profile = client.get("/auth/profile", headers=headers).json()
        response = client.patch(
            f"/admin/users/{profile['id']}",
            json={"username": "changed"},
            headers=headers,
        )
        assert response.status_code == 400

    def test_self_archive_rejected(self, client, admin_headers):
        client.post(
            "/admin/users",
            json={"username": "selfuser2", "password": "password123", "role": "administrator"},
            headers=admin_headers,
        )
        login = client.post("/auth/login", json={"username": "selfuser2", "password": "password123"})
        token = login.json()["session_token"]
        headers = {"X-Session-Token": token}
        profile = client.get("/auth/profile", headers=headers).json()
        response = client.post(
            f"/admin/users/{profile['id']}/archive",
            headers=headers,
        )
        assert response.status_code == 400


class TestProfile:
    def test_read_and_update_profile(self, client, admin_headers):
        client.post(
            "/admin/users",
            json={"username": "profuser", "password": "password123", "role": "account_manager"},
            headers=admin_headers,
        )
        login = client.post("/auth/login", json={"username": "profuser", "password": "password123"})
        assert login.status_code == 200
        token = login.json()["session_token"]
        headers = {"X-Session-Token": token}

        profile = client.get("/auth/profile", headers=headers)
        assert profile.status_code == 200
        assert profile.json()["username"] == "profuser"
        assert "password_hash" not in profile.json()

        updated = client.patch(
            "/auth/profile", json={"password": "newpassword1"}, headers=headers
        )
        assert updated.status_code == 200

        relogin = client.post("/auth/login", json={"username": "profuser", "password": "newpassword1"})
        assert relogin.status_code == 200

    def test_profile_short_password_rejected(self, client, admin_headers):
        client.post(
            "/admin/users",
            json={"username": "profuser2", "password": "password123", "role": "account_manager"},
            headers=admin_headers,
        )
        login = client.post("/auth/login", json={"username": "profuser2", "password": "password123"})
        token = login.json()["session_token"]
        headers = {"X-Session-Token": token}

        response = client.patch(
            "/auth/profile", json={"password": "short"}, headers=headers
        )
        assert response.status_code == 400

    def test_profile_requires_session(self, client, admin_headers):
        response = client.get("/auth/profile", headers=admin_headers)
        assert response.status_code == 401


class TestUserCRUD:
    def test_create_and_list(self, client, admin_headers):
        response = _create_user(client, admin_headers)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["username"] == "alice"
        assert body["role"] == "administrator"
        assert "password" not in body and "password_hash" not in body

        listed = client.get("/admin/users", headers=admin_headers).json()
        assert [u["username"] for u in listed] == ["alice"]
        assert all("password_hash" not in u for u in listed)

    def test_short_password_rejected(self, client, admin_headers):
        response = _create_user(client, admin_headers, password="short")
        assert response.status_code == 400
        assert "8 characters" in response.json()["error"]["message"]

    def test_invalid_role_rejected(self, client, admin_headers):
        response = _create_user(client, admin_headers, role="superuser")
        assert response.status_code == 400

    def test_update_user(self, client, admin_headers):
        created = _create_user(client, admin_headers).json()
        response = client.patch(
            f"/admin/users/{created['id']}",
            json={"username": "alice2", "role": "account_manager"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["username"] == "alice2"
        assert response.json()["role"] == "account_manager"

    def test_update_password_policy(self, client, admin_headers):
        created = _create_user(client, admin_headers).json()
        short = client.patch(
            f"/admin/users/{created['id']}",
            json={"password": "tiny"},
            headers=admin_headers,
        )
        assert short.status_code == 400
        ok = client.patch(
            f"/admin/users/{created['id']}",
            json={"password": "longenough"},
            headers=admin_headers,
        )
        assert ok.status_code == 200

    def test_archive_and_no_delete(self, client, admin_headers):
        created = _create_user(client, admin_headers).json()
        archived = client.post(
            f"/admin/users/{created['id']}/archive", headers=admin_headers
        )
        assert archived.status_code == 200
        assert archived.json()["archived_at"] is not None
        rearchive = client.post(
            f"/admin/users/{created['id']}/archive", headers=admin_headers
        )
        assert rearchive.status_code == 200
        assert rearchive.json()["archived_at"] == archived.json()["archived_at"]

        deleted = client.delete(
            f"/admin/users/{created['id']}", headers=admin_headers
        )
        assert deleted.status_code == 405

    def test_unknown_user_404(self, client, admin_headers):
        for method, path in [
            ("GET", "/admin/users/nope"),
            ("PATCH", "/admin/users/nope"),
            ("POST", "/admin/users/nope/archive"),
        ]:
            if method == "GET":
                r = client.get(path, headers=admin_headers)
            elif method == "PATCH":
                r = client.patch(path, json={"username": "x"}, headers=admin_headers)
            else:
                r = client.post(path, headers=admin_headers)
            assert r.status_code == 404, (method, path, r.status_code)


class TestPasswordStorage:
    def test_password_hashed_at_rest(self, client, admin_headers, tmp_path):
        from app import db

        created = _create_user(client, admin_headers).json()
        # find the db url via config
        # Re-open the same db by scanning tmp_path? Use client's app config instead.
        app = client.app
        url = app.state.config.database_url
        conn = db.connect(url)
        try:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?", (created["id"],)
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert row["password_hash"] != "password123"
        assert ":" in row["password_hash"]


class TestLogin:
    def test_valid_login(self, client, admin_headers):
        _create_user(client, admin_headers)
        response = client.post(
            "/auth/login",
            json={"username": "alice", "password": "password123"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["username"] == "alice"
        assert body["role"] == "administrator"
        assert "session_token" in body

    def test_wrong_password_generic_401(self, client, admin_headers):
        _create_user(client, admin_headers)
        response = client.post(
            "/auth/login",
            json={"username": "alice", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Invalid username or password"

    def test_unknown_user_generic_401(self, client):
        response = client.post(
            "/auth/login",
            json={"username": "nobody", "password": "whatever123"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Invalid username or password"

    def test_archived_user_cannot_login(self, client, admin_headers):
        created = _create_user(client, admin_headers).json()
        client.post(f"/admin/users/{created['id']}/archive", headers=admin_headers)
        response = client.post(
            "/auth/login",
            json={"username": "alice", "password": "password123"},
        )
        assert response.status_code == 401


class TestAdminSecretRetention:
    def test_admin_secret_still_works_after_user_auth(self, client, admin_headers):
        response = client.get("/admin/tenants", headers=admin_headers)
        assert response.status_code == 200

    def test_session_token_grants_admin_access(self, client, admin_headers):
        _create_user(client, admin_headers)
        token = client.post(
            "/auth/login",
            json={"username": "alice", "password": "password123"},
        ).json()["session_token"]
        response = client.get(
            "/admin/tenants", headers={"X-Session-Token": token}
        )
        assert response.status_code == 200
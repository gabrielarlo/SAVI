import app.main as main
from fastapi.testclient import TestClient


def _app_with_ui(tmp_path, monkeypatch, config):
    ui = tmp_path / "build"
    ui.mkdir()
    (ui / "dashboard.html").write_text("<h1>Dashboard</h1>")
    (ui / "documents.html").write_text("<h1>admin console</h1>")
    (ui / "tenants.html").write_text("<h1>tenant console</h1>")
    (ui / "signin.html").write_text("<h1>sign in</h1>")
    (ui / "style.css").write_text("body { color: red }")
    monkeypatch.setattr(main, "UI_DIR", ui)
    return main.create_app(config)


class TestAdminConsole:
    def test_tenants_page_is_served_without_credentials(
        self, tmp_path, monkeypatch, config
    ):
        app = _app_with_ui(tmp_path, monkeypatch, config)

        with TestClient(app) as client:
            assert client.get("/console/tenants").status_code == 200

    def test_tenants_page_is_missing_without_a_built_ui(
        self, tmp_path, monkeypatch, config
    ):
        monkeypatch.setattr(main, "UI_DIR", tmp_path / "missing")
        app = main.create_app(config)

        with TestClient(app) as client:
            assert client.get("/console/tenants").status_code == 404


class TestRootRedirect:
    def test_root_redirects_to_the_console(self, tmp_path, monkeypatch, config):
        app = _app_with_ui(tmp_path, monkeypatch, config)

        with TestClient(app) as client:
            response = client.get("/", follow_redirects=False)
            assert response.status_code == 307
            assert response.headers["location"] == "/console"

            response = client.get("/console", follow_redirects=False)
            assert response.status_code == 307
            assert response.headers["location"] == "/console/"

            response = client.get("/console/", follow_redirects=False)
            assert response.status_code == 200

            page = client.get("/", follow_redirects=True)
            assert page.status_code == 200
            assert "Dashboard" in page.text

    def test_pages_and_assets_are_served_without_credentials(
        self, tmp_path, monkeypatch, config
    ):
        app = _app_with_ui(tmp_path, monkeypatch, config)

        with TestClient(app) as client:
            signin = client.get("/auth/signin")
            stylesheet = client.get("/console/style.css")

        assert signin.status_code == 200
        assert "sign in" in signin.text
        assert stylesheet.status_code == 200
        assert "color: red" in stylesheet.text

    def test_api_works_without_a_built_ui(self, tmp_path, monkeypatch, config):
        monkeypatch.setattr(main, "UI_DIR", tmp_path / "missing")
        app = main.create_app(config)

        with TestClient(app) as client:
            assert client.get("/").status_code == 404
            assert client.get("/console/documents").status_code == 404
            response = client.get(
                "/admin/documents", headers={"X-Admin-Secret": config.admin_secret}
            )

        assert response.status_code == 200
        assert response.json() == []

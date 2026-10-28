"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import logging

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth import hash_password, install_error_handlers
from app.config import Config
from app.db import connect, migrate
from app.routes import admin_router, auth_router, external_router

UI_DIR = Path(__file__).resolve().parent.parent / "ui" / "build"

logger = logging.getLogger(__name__)


def create_app(config: Config | None = None) -> FastAPI:
    config = config or Config.from_env()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        migrate(config.database_url)
        if config.default_admin_username and config.default_admin_password:
            if len(config.default_admin_password) < 8:
                logger.warning(
                    "DEFAULT_ADMIN_PASSWORD is shorter than 8 characters; "
                    "skipping default admin seed"
                )
            else:
                conn = connect(config.database_url)
                try:
                    existing = conn.execute(
                        "SELECT 1 FROM users WHERE username = ?",
                        (config.default_admin_username,),
                    ).fetchone()
                    if existing is None:
                        import uuid as _uuid

                        conn.execute(
                            "INSERT INTO users (id, username, password_hash, role)"
                            " VALUES (?, ?, ?, 'administrator')",
                            (
                                str(_uuid.uuid4()),
                                config.default_admin_username,
                                hash_password(config.default_admin_password),
                            ),
                        )
                        conn.commit()
                        logger.info("Seeded default admin user %s", config.default_admin_username)
                finally:
                    conn.close()
        yield

    app = FastAPI(title="LocalRAG", lifespan=lifespan)
    app.state.config = config
    install_error_handlers(app)
    app.include_router(admin_router)
    app.include_router(external_router)
    app.include_router(auth_router)

    # The admin console is optional: an API-only image (or a checkout without a
    # built ui/) must still import and serve the JSON API.
    if UI_DIR.is_dir():
        @app.get("/", include_in_schema=False)
        def redirect_root() -> RedirectResponse:
            return RedirectResponse("/console")

        @app.get("/console", include_in_schema=False)
        def console_dashboard_redirect() -> RedirectResponse:
            return RedirectResponse("/console/")

        @app.get("/console/", include_in_schema=False)
        def console_dashboard() -> FileResponse:
            return FileResponse(UI_DIR / "dashboard.html")

        @app.get("/console/documents", include_in_schema=False)
        def console_documents() -> FileResponse:
            return FileResponse(UI_DIR / "documents.html")

        @app.get("/console/tenants", include_in_schema=False)
        def console_tenants() -> FileResponse:
            return FileResponse(UI_DIR / "tenants.html")

        @app.get("/console/users", include_in_schema=False)
        def console_users() -> FileResponse:
            return FileResponse(UI_DIR / "users.html")

        @app.get("/console/signin", include_in_schema=False)
        def console_signin_redirect() -> RedirectResponse:
            return RedirectResponse("/auth/signin")

        @app.get("/auth/signin", include_in_schema=False)
        def auth_signin() -> FileResponse:
            return FileResponse(UI_DIR / "signin.html")

        # style.css, bundle.js and images/ resolve relative to the page URL.
        app.mount("/console", StaticFiles(directory=UI_DIR), name="console")

    return app


app = create_app()

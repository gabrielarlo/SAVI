"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth import install_error_handlers
from app.config import Config
from app.db import migrate
from app.routes import admin_router, external_router

UI_DIR = Path(__file__).resolve().parent.parent / "ui" / "build"


def create_app(config: Config | None = None) -> FastAPI:
    config = config or Config.from_env()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        migrate(config.database_url)
        yield

    app = FastAPI(title="LocalRAG", lifespan=lifespan)
    app.state.config = config
    install_error_handlers(app)
    app.include_router(admin_router)
    app.include_router(external_router)

    # The admin console is optional: an API-only image (or a checkout without a
    # built ui/) must still import and serve the JSON API.
    if UI_DIR.is_dir():
        @app.get("/console", include_in_schema=False)
        @app.get("/console/", include_in_schema=False)
        @app.get("/", include_in_schema=False)
        def redirect_to_console() -> RedirectResponse:
            return RedirectResponse("/console/documents")

        @app.get("/console/documents", include_in_schema=False)
        def console_documents() -> FileResponse:
            return FileResponse(UI_DIR / "documents.html")

        @app.get("/console/tenants", include_in_schema=False)
        def console_tenants() -> FileResponse:
            return FileResponse(UI_DIR / "tenants.html")

        @app.get("/console/signin", include_in_schema=False)
        def console_signin() -> FileResponse:
            return FileResponse(UI_DIR / "signin.html")

        # style.css, bundle.js and images/ resolve relative to the page URL.
        app.mount("/console", StaticFiles(directory=UI_DIR), name="console")

    return app


app = create_app()

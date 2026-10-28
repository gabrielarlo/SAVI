"""Authentication dependencies and the shared error envelope."""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import Config
from app.db import connect

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = "Invalid or missing authentication credentials"


@dataclass(frozen=True)
class AdminRole:
    """Authenticated internal operator."""


@dataclass(frozen=True)
class TenantRole:
    """Authenticated external client, scoped to a single tenant."""

    tenant_id: str


def get_config(request: Request) -> Config:
    return request.app.state.config


def get_db(request: Request) -> Iterator:
    conn = connect(request.app.state.config.database_url)
    try:
        yield conn
    finally:
        conn.close()


def get_role(
    x_admin_secret: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    config: Config = Depends(get_config),
    db=Depends(get_db),
) -> AdminRole | TenantRole:
    if x_admin_secret and secrets.compare_digest(
        x_admin_secret.encode(), config.admin_secret.encode()
    ):
        return AdminRole()

    if x_api_key:
        row = db.execute(
            "SELECT id, archived_at FROM tenants WHERE api_key = ?", (x_api_key,)
        ).fetchone()
        if row is not None and row["archived_at"] is None:
            return TenantRole(row["id"])
        if row is not None and row["archived_at"] is not None:
            raise HTTPException(status_code=403, detail="Tenant account is archived")

    raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)


def require_admin(role: AdminRole | TenantRole = Depends(get_role)) -> AdminRole:
    if not isinstance(role, AdminRole):
        raise HTTPException(status_code=401, detail="Internal admin access required")
    return role


def require_tenant(role: AdminRole | TenantRole = Depends(get_role)) -> TenantRole:
    if not isinstance(role, TenantRole):
        raise HTTPException(status_code=401, detail="Tenant API key required")
    return role


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": status_code, "message": message}},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_: Request, exc: StarletteHTTPException):
        return _error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        logger.exception("unhandled error", exc_info=exc)
        return _error_response(500, "Internal server error")

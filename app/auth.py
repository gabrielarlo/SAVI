"""Authentication dependencies and the shared error envelope."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from typing import Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import Config
from app.db import connect

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = "Invalid or missing authentication credentials"
INVALID_LOGIN = "Invalid username or password"
PBKDF2_ITERATIONS = 100_000
SESSION_TTL_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class AdminRole:
    """Authenticated internal operator."""

    username: str | None = None
    role: str = "administrator"


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


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PBKDF2_ITERATIONS
    )
    return salt.hex() + ":" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":")
    except ValueError:
        return False
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(actual, expected)


def issue_session_token(username: str, secret: str) -> str:
    expiry = int(time.time()) + SESSION_TTL_SECONDS
    payload = f"{username}:{expiry}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()


def verify_session_token(token: str, secret: str) -> str | None:
    try:
        decoded = urlsafe_b64decode(token.encode()).decode()
        username, expiry_str, sig = decoded.rsplit(":", 2)
        expiry = int(expiry_str)
    except (ValueError, TypeError):
        return None
    if expiry < int(time.time()):
        return None
    payload = f"{username}:{expiry}"
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return username


def get_role(
    x_admin_secret: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None),
    config: Config = Depends(get_config),
    db=Depends(get_db),
) -> AdminRole | TenantRole:
    if x_admin_secret and secrets.compare_digest(
        x_admin_secret.encode(), config.admin_secret.encode()
    ):
        return AdminRole(role="administrator")

    if x_session_token:
        username = verify_session_token(x_session_token, config.admin_secret)
        if username:
            row = db.execute(
                "SELECT role, archived_at FROM users WHERE username = ?", (username,)
            ).fetchone()
            if row is not None and row["archived_at"] is None:
                return AdminRole(username=username, role=row["role"])

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

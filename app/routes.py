"""HTTP routes for internal operators and external tenants."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.auth import (
    AdminRole,
    TenantRole,
    get_config,
    get_db,
    hash_password,
    INVALID_LOGIN,
    issue_session_token,
    require_admin,
    require_tenant,
    verify_password,
)
from app.config import Config
from app.services import (
    ALLOWED_UPLOAD_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    extract_text,
    generate_answer,
    ingest_document,
    store_chunks,
)

admin_router = APIRouter(prefix="/admin", tags=["admin"])
external_router = APIRouter(prefix="/api/v1", tags=["external"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])


class CreateTenantRequest(BaseModel):
    name: str


class UpdateTenantRequest(BaseModel):
    name: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str


class UpdateUserRequest(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class IngestRequest(BaseModel):
    tenant_id: str
    title: str
    content: str


class SearchRequest(BaseModel):
    query: str


class ChatRequest(BaseModel):
    message: str
    tenant_id: str | None = None


def _user_or_404(db, user_id: str):
    row = db.execute(
        "SELECT id, username, role, archived_at, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return row


def _tenant_or_404(db, tenant_id: str):
    row = db.execute(
        "SELECT id, name, created_at, archived_at FROM tenants WHERE id = ?",
        (tenant_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return row


def _document_or_404(db, document_id: str):
    row = db.execute(
        "SELECT id, tenant_id, title, content, created_at FROM documents WHERE id = ?",
        (document_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return row


@admin_router.post("/tenants")
def create_tenant(
    payload: CreateTenantRequest,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    tenant_id = str(uuid.uuid4())
    api_key = f"lrk_{uuid.uuid4().hex}"
    db.execute(
        "INSERT INTO tenants (id, name, api_key) VALUES (?, ?, ?)",
        (tenant_id, payload.name, api_key),
    )
    db.commit()
    return {"tenant_id": tenant_id, "name": payload.name, "api_key": api_key}


@admin_router.get("/tenants")
def list_tenants(
    include_archived: bool = False,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    sql = "SELECT id, name, created_at, archived_at FROM tenants"
    if not include_archived:
        sql += " WHERE archived_at IS NULL"
    sql += " ORDER BY created_at ASC"
    return [dict(row) for row in db.execute(sql).fetchall()]


@admin_router.get("/tenants/{tenant_id}")
def get_tenant(
    tenant_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    return dict(_tenant_or_404(db, tenant_id))


@admin_router.patch("/tenants/{tenant_id}")
def update_tenant(
    tenant_id: str,
    payload: UpdateTenantRequest,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    tenant = _tenant_or_404(db, tenant_id)
    db.execute("UPDATE tenants SET name = ? WHERE id = ?", (payload.name, tenant_id))
    db.commit()
    return dict(_tenant_or_404(db, tenant_id))


@admin_router.post("/tenants/{tenant_id}/archive")
def archive_tenant(
    tenant_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    _tenant_or_404(db, tenant_id)
    db.execute(
        "UPDATE tenants SET archived_at = CURRENT_TIMESTAMP"
        " WHERE id = ? AND archived_at IS NULL",
        (tenant_id,),
    )
    db.commit()
    return dict(_tenant_or_404(db, tenant_id))


@admin_router.post("/documents")
def ingest_document_json(
    payload: IngestRequest,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
    config: Config = Depends(get_config),
):
    document_id, _chunks = ingest_document(
        db, payload.tenant_id, payload.title, payload.content, config.ollama_url
    )
    db.commit()
    return {"document_id": document_id, "status": "ingested"}


@admin_router.get("/documents")
def list_documents(
    tenant_id: str | None = None,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    sql = (
        "SELECT d.id, d.tenant_id, d.title, d.created_at, COUNT(c.id) AS chunk_count"
        " FROM documents d LEFT JOIN chunks c ON c.document_id = d.id"
    )
    params: tuple = ()
    if tenant_id:
        sql += " WHERE d.tenant_id = ?"
        params = (tenant_id,)
    sql += " GROUP BY d.id ORDER BY d.created_at DESC"
    return [dict(row) for row in db.execute(sql, params).fetchall()]


@admin_router.get("/documents/{document_id}")
def get_document(
    document_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    document = _document_or_404(db, document_id)
    chunks = db.execute(
        "SELECT id, chunk_index, content FROM chunks WHERE document_id = ?"
        " ORDER BY chunk_index ASC",
        (document_id,),
    ).fetchall()
    return {**dict(document), "chunks": [dict(chunk) for chunk in chunks]}


@admin_router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    deleted = db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    db.commit()
    if deleted.rowcount == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document_id": document_id, "status": "deleted"}


@admin_router.post("/documents/{document_id}/reingest")
def reingest_document(
    document_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
    config: Config = Depends(get_config),
):
    document = _document_or_404(db, document_id)
    db.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
    count = store_chunks(
        db,
        document_id,
        document["tenant_id"],
        document["content"],
        config.ollama_url,
    )
    db.commit()
    return {"document_id": document_id, "status": "reingested", "chunks": count}


@admin_router.post("/documents/upload")
def upload_document(
    tenant_id: str = Form(...),
    title: str | None = Form(None),
    file: UploadFile = File(...),
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
    config: Config = Depends(get_config),
):
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix or filename}'."
            " Allowed: .txt, .md, .pdf",
        )

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413, detail="File too large: limit is 10 MB"
        )

    document_id, count = ingest_document(
        db,
        tenant_id,
        title or Path(filename).stem,
        extract_text(filename, data),
        config.ollama_url,
    )
    db.commit()
    return {"document_id": document_id, "status": "ingested", "chunks": count}


@admin_router.post("/search")
def global_search(
    payload: SearchRequest,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    rows = db.execute("SELECT id, tenant_id, content FROM chunks LIMIT 5").fetchall()
    return {"query": payload.query, "results": [dict(row) for row in rows]}


@admin_router.post("/chat")
def admin_chat(
    payload: ChatRequest,
    role: AdminRole = Depends(require_admin),
    db=Depends(get_db),
    config: Config = Depends(get_config),
):
    if getattr(role, "role", "administrator") == "account_manager" and not payload.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")

    sql = "SELECT id, tenant_id, content FROM chunks"
    params: tuple = ()
    if payload.tenant_id:
        sql += " WHERE tenant_id = ?"
        params = (payload.tenant_id,)
    sql += " LIMIT 5"
    rows = db.execute(sql, params).fetchall()
    sources = [
        {"id": row["id"], "tenant_id": row["tenant_id"], "content": row["content"]}
        for row in rows
    ]

    # Document-level context so the model can answer meta questions such as
    # "how many documents do I have?".
    count_sql = "SELECT COUNT(*) AS n FROM documents"
    title_sql = "SELECT title FROM documents"
    count_params: tuple = ()
    title_params: tuple = ()
    if payload.tenant_id:
        count_sql += " WHERE tenant_id = ?"
        title_sql += " WHERE tenant_id = ?"
        count_params = (payload.tenant_id,)
        title_params = (payload.tenant_id,)
    doc_count = db.execute(count_sql, count_params).fetchone()["n"]
    titles = [r["title"] for r in db.execute(title_sql, title_params).fetchall()]
    extra_context = f"There are {doc_count} documents. Titles: {', '.join(titles)}."

    response = generate_answer(
        payload.message,
        sources,
        config.ollama_url,
        config.chat_model,
        config.code_name,
        extra_context,
    )
    return {
        "tenant_id": payload.tenant_id,
        "response": response,
        "sources": sources,
    }


@auth_router.post("/login")
def login(
    payload: LoginRequest,
    db=Depends(get_db),
    config: Config = Depends(get_config),
):
    row = db.execute(
        "SELECT username, password_hash, role, archived_at FROM users WHERE username = ?",
        (payload.username,),
    ).fetchone()
    if (
        row is None
        or row["archived_at"] is not None
        or not verify_password(payload.password, row["password_hash"])
    ):
        raise HTTPException(status_code=401, detail=INVALID_LOGIN)
    return {
        "username": row["username"],
        "role": row["role"],
        "session_token": issue_session_token(row["username"], config.admin_secret),
    }


@admin_router.get("/users")
def list_users(
    include_archived: bool = False,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    sql = "SELECT id, username, role, created_at, archived_at FROM users"
    if not include_archived:
        sql += " WHERE archived_at IS NULL"
    sql += " ORDER BY created_at ASC"
    return [dict(row) for row in db.execute(sql).fetchall()]


@admin_router.get("/users/{user_id}")
def get_user(
    user_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    return dict(_user_or_404(db, user_id))


@admin_router.post("/users")
def create_user(
    payload: CreateUserRequest,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    if payload.role not in ("administrator", "account_manager"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )
    user_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
        (user_id, payload.username, hash_password(payload.password), payload.role),
    )
    db.commit()
    return dict(_user_or_404(db, user_id))


@admin_router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    _user_or_404(db, user_id)
    if payload.username is not None:
        db.execute("UPDATE users SET username = ? WHERE id = ?", (payload.username, user_id))
    if payload.role is not None:
        if payload.role not in ("administrator", "account_manager"):
            raise HTTPException(status_code=400, detail="Invalid role")
        db.execute("UPDATE users SET role = ? WHERE id = ?", (payload.role, user_id))
    if payload.password is not None:
        if len(payload.password) < 8:
            raise HTTPException(
                status_code=400, detail="Password must be at least 8 characters"
            )
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(payload.password), user_id),
        )
    db.commit()
    return dict(_user_or_404(db, user_id))


@external_router.post("/chat")
def tenant_chat(
    _payload: ChatRequest,
    role: TenantRole = Depends(require_tenant),
    db=Depends(get_db),
):
    rows = db.execute(
        "SELECT id, content FROM chunks WHERE tenant_id = ? LIMIT 3",
        (role.tenant_id,),
    ).fetchall()
    return {
        "tenant_id": role.tenant_id,
        "response": "RAG response based on tenant context",
        "sources": [dict(row) for row in rows],
    }


@admin_router.post("/users/{user_id}/archive")
def archive_user(
    user_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    _user_or_404(db, user_id)
    db.execute(
        "UPDATE users SET archived_at = CURRENT_TIMESTAMP"
        " WHERE id = ? AND archived_at IS NULL",
        (user_id,),
    )
    db.commit()
    return dict(_user_or_404(db, user_id))

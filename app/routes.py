"""HTTP routes for internal operators and external tenants."""

from __future__ import annotations

import uuid
from pathlib import Path
import base64

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
    synthesize_speech,
    transcribe_audio,
)

admin_router = APIRouter(prefix="/admin", tags=["admin"])
external_router = APIRouter(prefix="/api/v1", tags=["external"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])


class CreateTenantRequest(BaseModel):
    name: str


class _Unset:
    pass


_UNSET = _Unset()


class UpdateTenantRequest(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    name: str | None = None
    auto_rotate: bool | None = None
    rotate_days: int | None | _Unset = _UNSET


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


class ProfileUpdateRequest(BaseModel):
    username: str | None = None
    password: str | None = None


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
        "SELECT id, name, created_at, archived_at, auto_rotate, rotate_days, "
        "api_key_expires_at FROM tenants WHERE id = ?",
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
        "INSERT INTO tenants (id, name, api_key, api_key_created_at, "
        "api_key_expires_at, auto_rotate, rotate_days) "
        "VALUES (?, ?, ?, CURRENT_TIMESTAMP, datetime('now', '+90 days'), 1, 90)",
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
    sql = "SELECT id, name, created_at, archived_at, auto_rotate, rotate_days, " \
          "api_key_expires_at FROM tenants"
    if not include_archived:
        sql += " WHERE archived_at IS NULL"
    sql += " ORDER BY created_at ASC"
    return [dict(row) for row in db.execute(sql).fetchall()]


@admin_router.get("/stats")
def system_stats(
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    from datetime import date, timedelta, datetime

    tenants_total = db.execute("SELECT COUNT(*) FROM tenants").fetchone()[0]
    tenants_active = db.execute(
        "SELECT COUNT(*) FROM tenants WHERE archived_at IS NULL"
    ).fetchone()[0]
    tenants_archived = tenants_total - tenants_active

    users_total = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    users_active = db.execute(
        "SELECT COUNT(*) FROM users WHERE archived_at IS NULL"
    ).fetchone()[0]
    users_archived = users_total - users_active

    # Per-day inquiry counts for the last 7 days, zero-filled.
    today = date.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    day_keys = [d.isoformat() for d in days]
    counts = {k: 0 for k in day_keys}
    for row in db.execute(
        "SELECT date(created_at) AS d, COUNT(*) AS n FROM inquiries "
        "WHERE date(created_at) >= ? GROUP BY date(created_at)",
        (day_keys[0],),
    ).fetchall():
        if row["d"] in counts:
            counts[row["d"]] = row["n"]

    # API key rotation urgency (archived tenants excluded).
    from datetime import datetime, timedelta

    blue = orange = red = 0
    now = datetime.utcnow()
    red_cutoff = now + timedelta(days=10)
    orange_cutoff = now + timedelta(days=30)
    for row in db.execute(
        "SELECT api_key_expires_at FROM tenants WHERE archived_at IS NULL"
    ).fetchall():
        exp = row["api_key_expires_at"]
        if exp is None:
            blue += 1
            continue
        try:
            exp_dt = datetime.fromisoformat(str(exp).replace(" ", "T"))
        except ValueError:
            blue += 1
            continue
        if exp_dt <= red_cutoff:
            red += 1
        elif exp_dt <= orange_cutoff:
            orange += 1
        else:
            blue += 1

    return {
        "tenants": tenants_total,
        "tenants_active": tenants_active,
        "tenants_archived": tenants_archived,
        "documents": db.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
        "chunks": db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
        "users": users_total,
        "users_active": users_active,
        "users_archived": users_archived,
        "inquiries": db.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0],
        "inquiries_per_day": [
            {"date": k, "count": counts[k]} for k in day_keys
        ],
        "api_keys_blue": blue,
        "api_keys_orange": orange,
        "api_keys_red": red,
    }


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
    if payload.name is not None:
        db.execute("UPDATE tenants SET name = ? WHERE id = ?", (payload.name, tenant_id))
    if payload.auto_rotate is not None:
        db.execute(
            "UPDATE tenants SET auto_rotate = ? WHERE id = ?",
            (1 if payload.auto_rotate else 0, tenant_id),
        )
    if payload.rotate_days is not _UNSET:
        if payload.rotate_days is not None and payload.rotate_days < 1:
            raise HTTPException(status_code=400, detail="rotate_days must be >= 1")
        db.execute(
            "UPDATE tenants SET rotate_days = ? WHERE id = ?", (payload.rotate_days, tenant_id)
        )
        if payload.rotate_days is None:
            db.execute(
                "UPDATE tenants SET api_key_expires_at = NULL WHERE id = ?", (tenant_id,)
            )
        else:
            db.execute(
                "UPDATE tenants SET api_key_expires_at = datetime('now', '+' || ? || ' days') "
                "WHERE id = ?",
                (payload.rotate_days, tenant_id),
            )
    db.commit()
    return dict(_tenant_or_404(db, tenant_id))


@admin_router.get("/tenants/{tenant_id}/api-key")
def get_tenant_api_key(
    tenant_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    _tenant_or_404(db, tenant_id)
    row = db.execute(
        "SELECT api_key FROM tenants WHERE id = ?", (tenant_id,)
    ).fetchone()
    return {"api_key": row["api_key"]}


@admin_router.post("/tenants/{tenant_id}/regenerate-key")
def regenerate_tenant_api_key(
    tenant_id: str,
    _: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    _tenant_or_404(db, tenant_id)
    new_key = f"lrk_{uuid.uuid4().hex}"
    db.execute(
        "UPDATE tenants SET api_key = ?, api_key_created_at = CURRENT_TIMESTAMP, "
        "api_key_expires_at = datetime('now', '+' || rotate_days || ' days') "
        "WHERE id = ?",
        (new_key, tenant_id),
    )
    db.commit()
    return {"api_key": new_key}


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
    if len(titles) > 10:
        titles = titles[:10] + [f"... ({len(titles) - 10} more)"]
    extra_context = f"There are {doc_count} documents. Titles: {', '.join(titles)}."

    user_name = getattr(role, "username", None) or "admin"
    response = generate_answer(
        payload.message,
        sources,
        config.ollama_url,
        config.chat_model,
        config.code_name,
        config.company_name,
        user_name,
        extra_context,
    )
    try:
        db.execute(
            "INSERT INTO inquiries (id, tenant_id) VALUES (?, ?)",
            (str(uuid.uuid4()), payload.tenant_id),
        )
        db.commit()
    except Exception:  # ponytail: inquiry tracking must never break chat
        pass
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


@auth_router.get("/profile")
def get_profile(
    role: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    if not getattr(role, "username", None):
        raise HTTPException(status_code=401, detail="Console session required")
    row = db.execute(
        "SELECT id, username, role, created_at, archived_at FROM users WHERE username = ?",
        (role.username,),
    ).fetchone()
    if row is None or row["archived_at"] is not None:
        raise HTTPException(status_code=401, detail="Console session required")
    return {"id": row["id"], "username": row["username"], "role": row["role"]}


@auth_router.patch("/profile")
def update_profile(
    payload: ProfileUpdateRequest,
    role: AdminRole = Depends(require_admin),
    db=Depends(get_db),
    config: Config = Depends(get_config),
):
    if not getattr(role, "username", None):
        raise HTTPException(status_code=401, detail="Console session required")
    row = db.execute(
        "SELECT id, username, role, archived_at FROM users WHERE username = ?",
        (role.username,),
    ).fetchone()
    if row is None or row["archived_at"] is not None:
        raise HTTPException(status_code=401, detail="Console session required")
    user_id = row["id"]
    username_changed = payload.username is not None and payload.username != row["username"]
    if payload.username is not None:
        db.execute("UPDATE users SET username = ? WHERE id = ?", (payload.username, user_id))
    if payload.password is not None:
        if len(payload.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(payload.password), user_id),
        )
    db.commit()
    updated = db.execute(
        "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    result = {"id": updated["id"], "username": updated["username"], "role": updated["role"]}
    if username_changed:
        result["session_token"] = issue_session_token(updated["username"], config.admin_secret)
    return result


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
    role: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    row = _user_or_404(db, user_id)
    if getattr(role, "username", None) and row["username"] == role.username:
        raise HTTPException(status_code=400, detail="Cannot modify your own account")
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
    try:
        db.execute(
            "INSERT INTO inquiries (id, tenant_id) VALUES (?, ?)",
            (str(uuid.uuid4()), role.tenant_id),
        )
        db.commit()
    except Exception:  # ponytail: inquiry tracking must never break chat
        pass
    return {
        "tenant_id": role.tenant_id,
        "response": "RAG response based on tenant context",
        "sources": [dict(row) for row in rows],
    }


@admin_router.post("/users/{user_id}/archive")
def archive_user(
    user_id: str,
    role: AdminRole = Depends(require_admin),
    db=Depends(get_db),
):
    row = _user_or_404(db, user_id)
    if getattr(role, "username", None) and row["username"] == role.username:
        raise HTTPException(status_code=400, detail="Cannot modify your own account")
    db.execute(
        "UPDATE users SET archived_at = CURRENT_TIMESTAMP"
        " WHERE id = ? AND archived_at IS NULL",
        (user_id,),
    )
    db.commit()
    return dict(_user_or_404(db, user_id))


@admin_router.post("/chat/voice")
def admin_chat_voice(
    file: UploadFile = File(...),
    tenant_id: str | None = Form(None),
    role: AdminRole = Depends(require_admin),
    db=Depends(get_db),
    config: Config = Depends(get_config),
):
    if getattr(role, "role", "administrator") == "account_manager" and not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large: limit is 10 MB")

    transcript = transcribe_audio(data, config.whisper_model, config.whisper_language)
    if not transcript:
        raise HTTPException(status_code=400, detail="No speech detected in the audio; please try again.")

    sql = "SELECT id, tenant_id, content FROM chunks"
    params: tuple = ()
    if tenant_id:
        sql += " WHERE tenant_id = ?"
        params = (tenant_id,)
    sql += " LIMIT 5"
    rows = db.execute(sql, params).fetchall()
    sources = [
        {"id": row["id"], "tenant_id": row["tenant_id"], "content": row["content"]}
        for row in rows
    ]

    count_sql = "SELECT COUNT(*) AS n FROM documents"
    title_sql = "SELECT title FROM documents"
    count_params: tuple = ()
    title_params: tuple = ()
    if tenant_id:
        count_sql += " WHERE tenant_id = ?"
        title_sql += " WHERE tenant_id = ?"
        count_params = (tenant_id,)
        title_params = (tenant_id,)
    doc_count = db.execute(count_sql, count_params).fetchone()["n"]
    titles = [r["title"] for r in db.execute(title_sql, title_params).fetchall()]
    if len(titles) > 10:
        titles = titles[:10] + [f"... ({len(titles) - 10} more)"]
    extra_context = f"There are {doc_count} documents. Titles: {', '.join(titles)}."

    user_name = getattr(role, "username", None) or "admin"
    response = generate_answer(
        transcript,
        sources,
        config.ollama_url,
        config.chat_model,
        config.code_name,
        config.company_name,
        user_name,
        extra_context,
    )

    audio_bytes = synthesize_speech(
        response, config.ollama_url, config.tts_model, config.tts_voice
    )
    audio = base64.b64encode(audio_bytes).decode() if audio_bytes else None

    return {
        "tenant_id": tenant_id,
        "transcript": transcript,
        "response": response,
        "sources": sources,
        "audio": audio,
    }


@external_router.post("/chat/voice")
def tenant_chat_voice(
    file: UploadFile = File(...),
    role: TenantRole = Depends(require_tenant),
    db=Depends(get_db),
    config: Config = Depends(get_config),
):
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large: limit is 10 MB")

    transcript = transcribe_audio(data, config.whisper_model, config.whisper_language)
    if not transcript:
        raise HTTPException(status_code=400, detail="No speech detected in the audio; please try again.")

    rows = db.execute(
        "SELECT id, content FROM chunks WHERE tenant_id = ? LIMIT 3",
        (role.tenant_id,),
    ).fetchall()
    sources = [{"id": row["id"], "content": row["content"]} for row in rows]

    response = generate_answer(
        transcript,
        [{"id": s["id"], "content": s["content"]} for s in sources],
        config.ollama_url,
        config.chat_model,
    )

    audio_bytes = synthesize_speech(
        response, config.ollama_url, config.tts_model, config.tts_voice
    )
    audio = base64.b64encode(audio_bytes).decode() if audio_bytes else None

    return {
        "tenant_id": role.tenant_id,
        "transcript": transcript,
        "response": response,
        "sources": sources,
        "audio": audio,
    }

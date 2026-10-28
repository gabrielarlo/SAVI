import sqlite3
from pathlib import Path

import pytest

from app.services import (
    MAX_UPLOAD_BYTES,
    UnsupportedFileType,
    extract_text,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _chunks(config, document_id=None):
    conn = sqlite3.connect(config.database_url.removeprefix("sqlite://"))
    conn.row_factory = sqlite3.Row
    try:
        sql = "SELECT id, document_id, tenant_id, chunk_index FROM chunks"
        params = ()
        if document_id:
            sql += " WHERE document_id = ?"
            params = (document_id,)
        return [dict(row) for row in conn.execute(sql + " ORDER BY chunk_index", params)]
    finally:
        conn.close()


def _upload(client, headers, tenant_id, filename, data, title=None):
    form = {"tenant_id": tenant_id}
    if title is not None:
        form["title"] = title
    return client.post(
        "/admin/documents/upload",
        data=form,
        files={"file": (filename, data)},
        headers=headers,
    )


class TestListTenants:
    def test_lists_tenants_without_api_keys(self, client, admin_headers, tenant):
        tenant("acme")
        tenant("beta")

        response = client.get("/admin/tenants", headers=admin_headers)

        assert response.status_code == 200
        body = response.json()
        assert [entry["name"] for entry in body] == ["acme", "beta"]
        assert set(body[0]) == {"id", "name", "created_at", "archived_at"}

    def test_empty_list(self, client, admin_headers):
        response = client.get("/admin/tenants", headers=admin_headers)

        assert response.json() == []

    def test_tenant_credential_is_rejected(self, client, tenant):
        created = tenant()

        response = client.get(
            "/admin/tenants", headers={"X-API-Key": created["api_key"]}
        )

        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Internal admin access required"


class TestListDocuments:
    def test_lists_every_document_with_chunk_count(
        self, client, admin_headers, tenant, ingest
    ):
        acme = tenant("acme")
        beta = tenant("beta")
        ingest(acme["tenant_id"], "acme content", title="acme doc")
        ingest(beta["tenant_id"], " ".join(f"w{i}" for i in range(1000)), title="beta doc")

        response = client.get("/admin/documents", headers=admin_headers)

        assert response.status_code == 200
        body = {entry["title"]: entry for entry in response.json()}
        assert set(body) == {"acme doc", "beta doc"}
        assert body["acme doc"]["chunk_count"] == 1
        assert body["beta doc"]["chunk_count"] == 3
        assert body["beta doc"]["tenant_id"] == beta["tenant_id"]
        assert set(body["acme doc"]) == {
            "id",
            "tenant_id",
            "title",
            "created_at",
            "chunk_count",
        }

    def test_filters_by_tenant(self, client, admin_headers, tenant, ingest):
        acme = tenant("acme")
        beta = tenant("beta")
        ingest(acme["tenant_id"], "acme content", title="acme doc")
        ingest(beta["tenant_id"], "beta content", title="beta doc")

        response = client.get(
            f"/admin/documents?tenant_id={acme['tenant_id']}", headers=admin_headers
        )

        assert [entry["title"] for entry in response.json()] == ["acme doc"]

    def test_orders_newest_first(self, client, admin_headers, tenant, ingest, config):
        acme = tenant()
        old = ingest(acme["tenant_id"], "old content", title="old")
        ingest(acme["tenant_id"], "new content", title="new")

        conn = sqlite3.connect(config.database_url.removeprefix("sqlite://"))
        try:
            conn.execute(
                "UPDATE documents SET created_at = '2000-01-01 00:00:00' WHERE id = ?",
                (old["document_id"],),
            )
            conn.commit()
        finally:
            conn.close()

        response = client.get("/admin/documents", headers=admin_headers)

        assert [entry["title"] for entry in response.json()] == ["new", "old"]

    def test_empty_list(self, client, admin_headers):
        response = client.get("/admin/documents", headers=admin_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_tenant_credential_is_rejected(self, client, tenant):
        created = tenant()

        response = client.get(
            "/admin/documents", headers={"X-API-Key": created["api_key"]}
        )

        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Internal admin access required"


class TestDocumentDetail:
    def test_returns_document_with_ordered_chunks(
        self, client, admin_headers, tenant, ingest
    ):
        acme = tenant()
        created = ingest(
            acme["tenant_id"], " ".join(f"w{i}" for i in range(1000)), title="big"
        )

        response = client.get(
            f"/admin/documents/{created['document_id']}", headers=admin_headers
        )

        body = response.json()
        assert response.status_code == 200
        assert body["title"] == "big"
        assert body["tenant_id"] == acme["tenant_id"]
        assert body["content"].startswith("w0 w1")
        assert "created_at" in body
        assert [chunk["chunk_index"] for chunk in body["chunks"]] == [0, 1, 2]
        assert set(body["chunks"][0]) == {"id", "chunk_index", "content"}

    def test_missing_document(self, client, admin_headers):
        response = client.get("/admin/documents/nope", headers=admin_headers)

        assert response.status_code == 404
        assert response.json() == {
            "error": {"code": 404, "message": "Document not found"}
        }


class TestDeleteDocument:
    def test_removes_document_and_chunks(
        self, client, admin_headers, tenant, ingest, config
    ):
        acme = tenant()
        created = ingest(acme["tenant_id"], " ".join(f"w{i}" for i in range(1000)))
        document_id = created["document_id"]
        assert _chunks(config, document_id)

        response = client.delete(
            f"/admin/documents/{document_id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json() == {"document_id": document_id, "status": "deleted"}
        assert _chunks(config, document_id) == []
        assert (
            client.get(
                f"/admin/documents/{document_id}", headers=admin_headers
            ).status_code
            == 404
        )

    def test_missing_document(self, client, admin_headers):
        response = client.delete("/admin/documents/nope", headers=admin_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == 404


class TestReingestDocument:
    def test_replaces_chunks_from_index_zero(
        self, client, admin_headers, tenant, ingest, config
    ):
        acme = tenant()
        created = ingest(
            acme["tenant_id"], " ".join(f"w{i}" for i in range(1000)), title="big"
        )
        document_id = created["document_id"]
        before = _chunks(config, document_id)

        response = client.post(
            f"/admin/documents/{document_id}/reingest", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json() == {
            "document_id": document_id,
            "status": "reingested",
            "chunks": 3,
        }
        after = _chunks(config, document_id)
        assert [chunk["chunk_index"] for chunk in after] == [0, 1, 2]
        assert {chunk["id"] for chunk in after}.isdisjoint(
            {chunk["id"] for chunk in before}
        )

    def test_missing_document(self, client, admin_headers):
        response = client.post(
            "/admin/documents/nope/reingest", headers=admin_headers
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == 404


class TestUpload:
    def test_text_upload(
        self, client, admin_headers, tenant, stub_embedding
    ):
        acme = tenant()

        response = _upload(
            client, admin_headers, acme["tenant_id"], "notes.txt", b"hello world"
        )

        body = response.json()
        assert response.status_code == 200
        assert body["status"] == "ingested"
        assert body["chunks"] == 1

        document = client.get(
            f"/admin/documents/{body['document_id']}", headers=admin_headers
        ).json()
        assert document["content"] == "hello world"
        assert document["title"] == "notes"

    def test_explicit_title_wins(self, client, admin_headers, tenant, stub_embedding):
        acme = tenant()

        response = _upload(
            client,
            admin_headers,
            acme["tenant_id"],
            "notes.txt",
            b"hello",
            title="Custom title",
        )

        document = client.get(
            f"/admin/documents/{response.json()['document_id']}", headers=admin_headers
        ).json()
        assert document["title"] == "Custom title"

    def test_markdown_upload(self, client, admin_headers, tenant, stub_embedding):
        acme = tenant()

        response = _upload(
            client, admin_headers, acme["tenant_id"], "readme.md", b"# Title\n\nbody"
        )

        assert response.status_code == 200
        assert response.json()["chunks"] == 1

    def test_pdf_upload(self, client, admin_headers, tenant, stub_embedding):
        acme = tenant()

        response = _upload(
            client,
            admin_headers,
            acme["tenant_id"],
            "sample.pdf",
            (FIXTURES / "sample.pdf").read_bytes(),
        )

        body = response.json()
        assert response.status_code == 200
        assert body["chunks"] == 1

        document = client.get(
            f"/admin/documents/{body['document_id']}", headers=admin_headers
        ).json()
        assert "LocalRAG sample document." in document["content"]
        assert "Page two of the sample." in document["content"]
        assert document["title"] == "sample"

    def test_scanned_pdf_stores_no_chunks(
        self, client, admin_headers, tenant, stub_embedding
    ):
        acme = tenant()

        response = _upload(
            client,
            admin_headers,
            acme["tenant_id"],
            "scanned.pdf",
            (FIXTURES / "scanned.pdf").read_bytes(),
        )

        body = response.json()
        assert response.status_code == 200
        assert body["chunks"] == 0

        document = client.get(
            f"/admin/documents/{body['document_id']}", headers=admin_headers
        ).json()
        assert document["content"] == ""
        assert document["chunks"] == []

    def test_non_utf8_text_is_decoded_with_replacement(
        self, client, admin_headers, tenant, stub_embedding
    ):
        acme = tenant()

        response = _upload(
            client, admin_headers, acme["tenant_id"], "latin1.txt", b"caf\xe9 au lait"
        )

        document = client.get(
            f"/admin/documents/{response.json()['document_id']}", headers=admin_headers
        ).json()
        assert document["content"] == "caf\ufffd au lait"

    def test_unsupported_type(self, client, admin_headers, tenant, stub_embedding):
        acme = tenant()

        response = _upload(
            client, admin_headers, acme["tenant_id"], "notes.docx", b"whatever"
        )

        assert response.status_code == 415
        assert "Unsupported file type" in response.json()["error"]["message"]
        assert client.get("/admin/documents", headers=admin_headers).json() == []

    def test_oversized_file(self, client, admin_headers, tenant, stub_embedding):
        acme = tenant()

        response = _upload(
            client,
            admin_headers,
            acme["tenant_id"],
            "big.txt",
            b"x" * (MAX_UPLOAD_BYTES + 1),
        )

        assert response.status_code == 413
        assert "10 MB" in response.json()["error"]["message"]
        assert client.get("/admin/documents", headers=admin_headers).json() == []

    def test_tenant_credential_is_rejected(self, client, tenant):
        created = tenant()

        response = _upload(
            client,
            {"X-API-Key": created["api_key"]},
            created["tenant_id"],
            "notes.txt",
            b"hello",
        )

        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Internal admin access required"


class TestExtractText:
    def test_plain_text(self):
        assert extract_text("notes.txt", b"hello") == "hello"

    def test_invalid_utf8_is_replaced(self):
        assert extract_text("notes.md", b"caf\xe9") == "caf\ufffd"

    def test_pdf_pages_joined_with_newline(self):
        text = extract_text("sample.pdf", (FIXTURES / "sample.pdf").read_bytes())

        assert text.split("\n") == [
            "LocalRAG sample document.",
            "Second line on page one.",
            "Page two of the sample.",
        ]

    def test_pdf_without_text_layer(self):
        assert extract_text("scanned.pdf", (FIXTURES / "scanned.pdf").read_bytes()) == ""

    def test_unsupported_extension(self):
        with pytest.raises(UnsupportedFileType):
            extract_text("notes.docx", b"hello")

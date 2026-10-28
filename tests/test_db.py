from app import db


def _tables(database_url):
    conn = db.connect(database_url)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        return {row["name"] for row in rows}
    finally:
        conn.close()


def test_migration_creates_initial_tables(tmp_path):
    url = f"sqlite://{tmp_path}/nested/local_rag.db"

    db.migrate(url)

    assert {"tenants", "documents", "chunks"} <= _tables(url)


def test_migration_is_idempotent_and_keeps_data(tmp_path):
    url = f"sqlite://{tmp_path}/local_rag.db"
    db.migrate(url)

    conn = db.connect(url)
    conn.execute(
        "INSERT INTO tenants (id, name, api_key) VALUES ('t1', 'acme', 'lrk_test')"
    )
    conn.commit()
    conn.close()

    db.migrate(url)

    conn = db.connect(url)
    try:
        assert conn.execute("SELECT COUNT(*) FROM tenants").fetchone()[0] == 1
    finally:
        conn.close()


def test_migration_runs_every_file_exactly_once(tmp_path):
    url = f"sqlite://{tmp_path}/local_rag.db"

    db.migrate(url)
    db.migrate(url)  # applying the same database twice must succeed
    recorded = {
        row["filename"] for row in db.connect(url).execute("SELECT filename FROM schema_migrations")
    }
    files = {path.name for path in db.MIGRATIONS_DIR.glob("*.sql")}
    assert recorded == files

    conn = db.connect(url)
    try:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(tenants)")
        }
    finally:
        conn.close()
    assert "archived_at" in columns


def test_users_table_is_created_and_unique(tmp_path):
    url = f"sqlite://{tmp_path}/local_rag.db"

    db.migrate(url)

    conn = db.connect(url)
    try:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
        assert {"id", "username", "password_hash", "role", "archived_at", "created_at"} <= columns
        conn.execute(
            "INSERT INTO users (id, username, password_hash, role)"
            " VALUES ('u1', 'alice', 'h', 'administrator')"
        )
        conn.commit()
        try:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, role)"
                " VALUES ('u2', 'alice', 'h2', 'account_manager')"
            )
        except Exception as exc:
            assert "UNIQUE" in str(exc).upper()
        else:
            raise AssertionError("duplicate username was accepted")
    finally:
        conn.close()
    url = f"sqlite://{tmp_path}/local_rag.db"
    db.migrate(url)

    conn = db.connect(url)
    try:
        try:
            conn.execute(
                "INSERT INTO documents (id, tenant_id, title, content)"
                " VALUES ('d1', 'missing', 't', 'c')"
            )
        except Exception as exc:  # sqlite3.IntegrityError
            assert "FOREIGN KEY" in str(exc)
        else:
            raise AssertionError("foreign key constraint was not enforced")
    finally:
        conn.close()
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('administrator','account_manager')),
    archived_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

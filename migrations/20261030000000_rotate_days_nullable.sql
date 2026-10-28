PRAGMA foreign_keys = OFF;

CREATE TABLE IF NOT EXISTS tenants_new (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived_at DATETIME,
    api_key_created_at DATETIME,
    api_key_expires_at DATETIME,
    auto_rotate INTEGER NOT NULL DEFAULT 1,
    rotate_days INTEGER
);

INSERT INTO tenants_new (id, name, api_key, created_at, archived_at,
  api_key_created_at, api_key_expires_at, auto_rotate, rotate_days)
SELECT id, name, api_key, created_at, archived_at,
  api_key_created_at, api_key_expires_at, auto_rotate, rotate_days
FROM tenants;

DROP TABLE tenants;
ALTER TABLE tenants_new RENAME TO tenants;

PRAGMA foreign_keys = ON;
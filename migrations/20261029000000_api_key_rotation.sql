ALTER TABLE tenants ADD COLUMN api_key_created_at DATETIME;
ALTER TABLE tenants ADD COLUMN api_key_expires_at DATETIME;
ALTER TABLE tenants ADD COLUMN auto_rotate INTEGER NOT NULL DEFAULT 1;
ALTER TABLE tenants ADD COLUMN rotate_days INTEGER NOT NULL DEFAULT 90;

UPDATE tenants
SET api_key_created_at = CURRENT_TIMESTAMP,
    api_key_expires_at = datetime('now', '+90 days')
WHERE api_key_created_at IS NULL;
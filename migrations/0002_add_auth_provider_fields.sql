-- Migration: add auth_provider fields to users + rename password_hash -> hashed_password
-- Run this against your PostgreSQL database once.
-- Safe to run multiple times due to IF NOT EXISTS / DO checks.

BEGIN;

-- 1. Rename password_hash → hashed_password (aligns with service layer)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE users RENAME COLUMN password_hash TO hashed_password;
    END IF;
END
$$;

-- 2. Make hashed_password nullable (pure-OAuth accounts have no password)
ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;

-- 3. Add auth_provider column (e.g. "google", "github")
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider  VARCHAR(32)  DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider_id VARCHAR(255) DEFAULT NULL;

-- 4. Indexes for fast OAuth lookups
CREATE INDEX IF NOT EXISTS ix_users_auth_provider    ON users (auth_provider);
CREATE INDEX IF NOT EXISTS ix_users_auth_provider_id ON users (auth_provider_id);

COMMIT;

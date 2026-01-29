-- ==================== Authentication System Migration ====================
-- Extends the user table and adds OAuth support for Apple, Google, and Email login
-- PostgreSQL 16

-- ==================== Modify user table ====================
-- Add new columns for multi-auth support

-- Add email column (nullable for backward compatibility)
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Add email_verified flag
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- Add avatar_url column
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Add display_name column (user's display name, different from username)
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);

-- Make password nullable (for OAuth users who don't have password)
ALTER TABLE "user" ALTER COLUMN password DROP NOT NULL;

-- Create index on email
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_email ON "user"(email) WHERE email IS NOT NULL;

-- ==================== Table: user_oauth ====================
-- OAuth provider connections for users (supports multiple providers per user)
CREATE TABLE IF NOT EXISTS user_oauth (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    provider VARCHAR(20) NOT NULL,  -- 'google', 'apple', 'email'
    provider_user_id VARCHAR(255) NOT NULL,  -- Provider's unique user ID
    provider_email VARCHAR(255),
    provider_data JSONB DEFAULT '{}',  -- Additional data from provider
    created_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    
    CONSTRAINT fk_user_oauth_user FOREIGN KEY (user_id) 
        REFERENCES "user"(user_id) ON DELETE CASCADE,
    CONSTRAINT uk_user_oauth_provider UNIQUE (provider, provider_user_id),
    CONSTRAINT chk_provider CHECK (provider IN ('google', 'apple', 'email', 'firebase'))
);

-- Indexes for user_oauth table
CREATE INDEX IF NOT EXISTS idx_user_oauth_user_id ON user_oauth(user_id);
CREATE INDEX IF NOT EXISTS idx_user_oauth_provider ON user_oauth(provider);
CREATE INDEX IF NOT EXISTS idx_user_oauth_provider_email ON user_oauth(provider_email);

-- Comments for user_oauth table
COMMENT ON TABLE user_oauth IS 'OAuth provider connections for users';
COMMENT ON COLUMN user_oauth.provider IS 'OAuth provider: google, apple, or email';
COMMENT ON COLUMN user_oauth.provider_user_id IS 'Unique user ID from the OAuth provider';
COMMENT ON COLUMN user_oauth.provider_data IS 'Additional data returned from OAuth provider';

-- ==================== Table: email_verification_tokens ====================
-- Email verification tokens for registration and password reset
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),  -- Nullable for pre-registration verification
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(20) NOT NULL,  -- 'verification', 'password_reset'
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    
    CONSTRAINT chk_token_type CHECK (token_type IN ('verification', 'password_reset'))
);

-- Indexes for email_verification_tokens table
CREATE INDEX IF NOT EXISTS idx_email_tokens_email ON email_verification_tokens(email);
CREATE INDEX IF NOT EXISTS idx_email_tokens_token ON email_verification_tokens(token);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires ON email_verification_tokens(expires_at);

-- Comments for email_verification_tokens table
COMMENT ON TABLE email_verification_tokens IS 'Tokens for email verification and password reset';
COMMENT ON COLUMN email_verification_tokens.token_type IS 'Token type: verification or password_reset';

-- ==================== Table: refresh_tokens ====================
-- Refresh tokens for extended sessions
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB DEFAULT '{}',  -- Device information for security
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    
    CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) 
        REFERENCES "user"(user_id) ON DELETE CASCADE
);

-- Indexes for refresh_tokens table
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- Comments for refresh_tokens table
COMMENT ON TABLE refresh_tokens IS 'Refresh tokens for extended user sessions';

-- ==================== Triggers ====================
-- Create trigger for updated_at on user_oauth table
CREATE TRIGGER update_user_oauth_updated_at
    BEFORE UPDATE ON user_oauth
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==================== Clean up expired tokens (optional scheduled job) ====================
-- Function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    -- Delete expired email verification tokens
    DELETE FROM email_verification_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP AT TIME ZONE 'UTC';
    
    -- Delete expired and revoked refresh tokens
    DELETE FROM refresh_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP AT TIME ZONE 'UTC' 
       OR revoked_at IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- ==================== Grant Permissions ====================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- ==================== Migration Complete ====================
-- Run this script to extend the database for multi-auth support



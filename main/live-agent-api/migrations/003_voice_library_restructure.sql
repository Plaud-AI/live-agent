-- Migration: Voice Library Restructure
-- Description: Restructure voices table to support voice library with multiple providers
-- Date: 2024-12-23

-- ==================== Step 1: Create system user for voice library ====================
-- Insert system user if not exists (for voice library owner)
INSERT INTO "user" (user_id, username, password)
VALUES ('system_voice_library', 'system_voice_library', 'not_for_login')
ON CONFLICT (user_id) DO NOTHING;

-- ==================== Step 2: Add new columns to voices table ====================
-- Add reference_id column (will hold the provider's voice ID like Fish Audio ID or MiniMax ID)
ALTER TABLE voices ADD COLUMN IF NOT EXISTS reference_id VARCHAR(100);

-- Add category column (clone or library)
ALTER TABLE voices ADD COLUMN IF NOT EXISTS category VARCHAR(20) NOT NULL DEFAULT 'clone';

-- Add provider column (fishspeech or minimax)
ALTER TABLE voices ADD COLUMN IF NOT EXISTS provider VARCHAR(20) NOT NULL DEFAULT 'fishspeech';

-- Add tags column (JSONB for flexible filtering)
ALTER TABLE voices ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '{}';

-- ==================== Step 3: Migrate existing data ====================
-- Copy existing voice_id to reference_id
UPDATE voices SET reference_id = voice_id WHERE reference_id IS NULL;

-- Generate new voice_id in voice_{ulid} format for existing records
-- Using gen_random_uuid() as fallback since ULID extension may not be available
UPDATE voices 
SET voice_id = 'voice_' || REPLACE(gen_random_uuid()::text, '-', '')
WHERE voice_id NOT LIKE 'voice_%';

-- ==================== Step 4: Update constraints ====================
-- Drop old unique constraint
ALTER TABLE voices DROP CONSTRAINT IF EXISTS uk_voices_owner_voice;

-- Drop old index on voice_id
DROP INDEX IF EXISTS idx_voices_voice_id;

-- Add new unique constraint on voice_id (now the primary business key)
-- Use idempotent pattern: DROP IF EXISTS + ADD
ALTER TABLE voices DROP CONSTRAINT IF EXISTS uk_voices_voice_id;
ALTER TABLE voices ADD CONSTRAINT uk_voices_voice_id UNIQUE (voice_id);

-- Add index on reference_id for provider lookups
CREATE INDEX IF NOT EXISTS idx_voices_reference_id ON voices(reference_id);

-- Add index on category for filtering
CREATE INDEX IF NOT EXISTS idx_voices_category ON voices(category);

-- Add index on provider for filtering
CREATE INDEX IF NOT EXISTS idx_voices_provider ON voices(provider);

-- Add GIN index on tags for JSONB queries
CREATE INDEX IF NOT EXISTS idx_voices_tags_gin ON voices USING GIN (tags);

-- Composite index for voice library queries (category + tags filters)
CREATE INDEX IF NOT EXISTS idx_voices_library_lookup ON voices(category, provider);

-- ==================== Step 5: Add constraints ====================
-- Add check constraint for category (idempotent: drop first if exists)
ALTER TABLE voices DROP CONSTRAINT IF EXISTS chk_voices_category;
ALTER TABLE voices ADD CONSTRAINT chk_voices_category 
    CHECK (category IN ('clone', 'library'));

-- Add check constraint for provider (idempotent: drop first if exists)
ALTER TABLE voices DROP CONSTRAINT IF EXISTS chk_voices_provider;
ALTER TABLE voices ADD CONSTRAINT chk_voices_provider 
    CHECK (provider IN ('fishspeech', 'minimax'));

-- ==================== Step 6: Update agents.voice_id references ====================
-- Update agents that reference cloned voices to use new voice_id format
-- This updates agent.voice_id to match the new voice_id in voices table
UPDATE agents a
SET voice_id = v.voice_id
FROM voices v
WHERE a.voice_id = v.reference_id
  AND v.reference_id IS NOT NULL;

-- ==================== Step 7: Add comments ====================
COMMENT ON COLUMN voices.voice_id IS 'Primary business key in voice_{ulid} format';
COMMENT ON COLUMN voices.reference_id IS 'Provider-specific voice ID (Fish Audio ID, MiniMax ID, etc.)';
COMMENT ON COLUMN voices.category IS 'Voice category: clone (user cloned) or library (preset voice library)';
COMMENT ON COLUMN voices.provider IS 'TTS provider: fishspeech or minimax';
COMMENT ON COLUMN voices.tags IS 'JSONB tags for filtering: {gender, age, language, style, accent, description}';

-- ==================== Migration Complete ====================


-- Migration: Update Clone Voices Structure and Agent References
-- Description: 
--   1. Set default values for existing clone voices (category, provider)
--   2. Update agent.voice_id to use voices.voice_id where reference_id matches
-- Date: 2024-12-23

-- ==================== Step 1: Update existing clone voices ====================
-- Set category = 'clone' and provider = 'fishspeech' for voices that don't have these set
-- (These are the original Fish Audio cloned voices)

UPDATE voices
SET 
    category = 'clone',
    provider = 'fishspeech'
WHERE category IS NULL OR category = '';

-- Ensure all clone voices have proper tags structure (empty object if null)
UPDATE voices
SET tags = '{}'::jsonb
WHERE tags IS NULL;

-- ==================== Step 2: Update agent.voice_id references ====================
-- For agents whose voice_id matches a reference_id in voices table,
-- update to use the new voice_id (voice_{ulid} format)

-- First, let's see what will be updated (for verification)
-- SELECT a.agent_id, a.voice_id as old_voice_id, v.voice_id as new_voice_id, v.reference_id
-- FROM agents a
-- JOIN voices v ON a.voice_id = v.reference_id
-- WHERE a.voice_id IS NOT NULL AND a.voice_id != '';

-- Perform the update
UPDATE agents a
SET voice_id = v.voice_id
FROM voices v
WHERE a.voice_id = v.reference_id
  AND a.voice_id IS NOT NULL 
  AND a.voice_id != ''
  AND v.reference_id IS NOT NULL;

-- ==================== Step 3: Verify updates ====================
-- Log counts for verification (these will show in psql output)
DO $$
DECLARE
    clone_count INTEGER;
    library_count INTEGER;
    agent_with_voice_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO clone_count FROM voices WHERE category = 'clone';
    SELECT COUNT(*) INTO library_count FROM voices WHERE category = 'library';
    SELECT COUNT(*) INTO agent_with_voice_count FROM agents WHERE voice_id LIKE 'voice_%';
    
    RAISE NOTICE 'Clone voices: %', clone_count;
    RAISE NOTICE 'Library voices: %', library_count;
    RAISE NOTICE 'Agents with voice_ prefixed voice_id: %', agent_with_voice_count;
END $$;

-- ==================== Migration Complete ====================


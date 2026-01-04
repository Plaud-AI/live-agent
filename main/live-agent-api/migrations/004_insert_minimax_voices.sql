-- Migration: Insert MiniMax Voice Library Data
-- Generated: 2025-12-23T06:53:51.261437+00:00
-- Total voices: 455

-- Ensure system user exists
INSERT INTO "user" (user_id, username, password)
VALUES ('system_voice_library', 'system_voice_library', 'not_for_login')
ON CONFLICT (user_id) DO NOTHING;

-- Insert library voices

-- Expressive Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDE4', 'English_expressive_narrator', 'system_voice_library', 'library', 'minimax', 'Expressive Narrator', 'An expressive adult male voice with a British accent, perfect for engaging audiobook narration.', '{"age": "adult", "style": "audiobook", "accent": "EN-British", "gender": "male", "language": "en", "description": "An expressive adult male voice with a British accent, perfect for engaging audiobook narration."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVT2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Radiant Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDE5', 'English_radiant_girl', 'system_voice_library', 'library', 'minimax', 'Radiant Girl', 'A radiant and lively young adult female voice with a general American accent, full of energy and brightness.', '{"age": "young_adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A radiant and lively young adult female voice with a general American accent, full of energy and brightness."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVT3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Magnetic-voiced Male
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDE6', 'English_magnetic_voiced_man', 'system_voice_library', 'library', 'minimax', 'Magnetic-voiced Male', 'A magnetic and persuasive adult male voice with a general American accent, ideal for advertisements and promotions.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A magnetic and persuasive adult male voice with a general American accent, ideal for advertisements and promotions."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVT4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Compelling Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDE7', 'English_compelling_lady1', 'system_voice_library', 'library', 'minimax', 'Compelling Lady', 'A compelling adult female voice with a British accent, suitable for broadcast and formal announcements. Clear and authoritative.', '{"age": "adult", "style": "audiobook", "accent": "EN-British", "gender": "female", "language": "en", "description": "A compelling adult female voice with a British accent, suitable for broadcast and formal announcements. Clear and authoritative."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVT5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Aussie Bloke
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDE8', 'English_Aussie_Bloke', 'system_voice_library', 'library', 'minimax', 'Aussie Bloke', 'A friendly, bright adult male voice with a distinct Australian accent, conveying a cheerful and approachable tone.', '{"age": "adult", "style": "social_media", "accent": "EN-Australian", "gender": "male", "language": "en", "description": "A friendly, bright adult male voice with a distinct Australian accent, conveying a cheerful and approachable tone."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVT6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Captivating Female
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDE9', 'English_captivating_female1', 'system_voice_library', 'library', 'minimax', 'Captivating Female', 'A captivating adult female voice with a general American accent, ideal for news reporting and documentary narration.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A captivating adult female voice with a general American accent, ideal for news reporting and documentary narration."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVT7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Upbeat Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEA', 'English_Upbeat_Woman', 'system_voice_library', 'library', 'minimax', 'Upbeat Woman', 'An upbeat and bright adult female voice with a general American accent, perfect for energetic and positive messaging.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An upbeat and bright adult female voice with a general American accent, perfect for energetic and positive messaging."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVT8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Trustworthy Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEB', 'English_Trustworth_Man', 'system_voice_library', 'library', 'minimax', 'Trustworthy Man', 'A trustworthy and resonant adult male voice with a general American accent, conveying sincerity and reliability.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A trustworthy and resonant adult male voice with a general American accent, conveying sincerity and reliability."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVT9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEC', 'English_CalmWoman', 'system_voice_library', 'library', 'minimax', 'Calm Woman', 'A calm and soothing adult female voice with a general American accent, excellent for audiobooks and meditation guides.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A calm and soothing adult female voice with a general American accent, excellent for audiobooks and meditation guides."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Upset Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDED', 'English_UpsetGirl', 'system_voice_library', 'library', 'minimax', 'Upset Girl', 'A young adult female voice with a British accent, effectively conveying sadness and distress.', '{"age": "young_adult", "style": "characters", "accent": "EN-British", "gender": "female", "language": "en", "description": "A young adult female voice with a British accent, effectively conveying sadness and distress."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle-voiced Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEE', 'English_Gentle-voiced_man', 'system_voice_library', 'library', 'minimax', 'Gentle-voiced Man', 'A gentle and resonant adult male voice with a general American accent, warm and reassuring.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A gentle and resonant adult male voice with a general American accent, warm and reassuring."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Whispering girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEF', 'English_Whispering_girl_v3', 'system_voice_library', 'library', 'minimax', 'Whispering girl', 'A young adult female voice delivering a soft whisper, perfect for ASMR content and intimate narration.', '{"age": "young_adult", "style": "characters", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A young adult female voice delivering a soft whisper, perfect for ASMR content and intimate narration."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Diligent Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEG', 'English_Diligent_Man', 'system_voice_library', 'library', 'minimax', 'Diligent Man', 'A diligent and sincere adult male voice with an Indian accent, conveying honesty and hard work.', '{"age": "adult", "style": "advertisement", "accent": "EN-Indian", "gender": "male", "language": "en", "description": "A diligent and sincere adult male voice with an Indian accent, conveying honesty and hard work."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Graceful Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEH', 'English_Graceful_Lady', 'system_voice_library', 'library', 'minimax', 'Graceful Lady', 'A graceful and elegant middle-aged female voice with a classic British accent, exuding sophistication.', '{"age": "middle_aged", "style": "audiobook", "accent": "EN-British", "gender": "female", "language": "en", "description": "A graceful and elegant middle-aged female voice with a classic British accent, exuding sophistication."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Husky MetalHead
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEJ', 'English_Husky_MetalHead', 'system_voice_library', 'library', 'minimax', 'Husky MetalHead', 'A husky, lo-fi adult male voice, perfect for a raw, alternative, or metal-style narration.', '{"age": "adult", "style": "characters", "accent": "English", "gender": "male", "language": "en", "description": "A husky, lo-fi adult male voice, perfect for a raw, alternative, or metal-style narration."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reserved Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEK', 'English_ReservedYoungMan', 'system_voice_library', 'library', 'minimax', 'Reserved Young Man', 'A reserved and cold adult male voice with a general American accent, conveying distance and introspection.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A reserved and cold adult male voice with a general American accent, conveying distance and introspection."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Playful Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEM', 'English_PlayfulGirl', 'system_voice_library', 'library', 'minimax', 'Playful Girl', 'A playful female youth voice with a general American accent, ideal for cartoons and children''s entertainment.', '{"age": "youth", "style": "characters", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A playful female youth voice with a general American accent, ideal for cartoons and children''s entertainment."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Man With Deep Voice
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEN', 'English_ManWithDeepVoice', 'system_voice_library', 'library', 'minimax', 'Man With Deep Voice', 'An adult male with a deep, commanding voice and a general American accent, projecting authority and strength.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An adult male with a deep, commanding voice and a general American accent, projecting authority and strength."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Teacher
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEP', 'English_GentleTeacher', 'system_voice_library', 'library', 'minimax', 'Gentle Teacher', 'A gentle and mild-mannered adult male teacher voice with an Indian accent, patient and instructive.', '{"age": "adult", "style": "informative", "accent": "EN-Indian", "gender": "male", "language": "en", "description": "A gentle and mild-mannered adult male teacher voice with an Indian accent, patient and instructive."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Mature Partner
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDEQ', 'English_MaturePartner', 'system_voice_library', 'library', 'minimax', 'Mature Partner', 'A mature, gentle middle-aged male voice with a British accent, suitable for a caring and supportive partner role.', '{"age": "middle_aged", "style": "audiobook", "accent": "EN-British", "gender": "male", "language": "en", "description": "A mature, gentle middle-aged male voice with a British accent, suitable for a caring and supportive partner role."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Guy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDER', 'English_FriendlyPerson', 'system_voice_library', 'library', 'minimax', 'Friendly Guy', 'A friendly and natural-sounding adult male voice with a general American accent, like an approachable guy-next-door.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A friendly and natural-sounding adult male voice with a general American accent, like an approachable guy-next-door."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bossy Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBWFNW8S97THMDKQDES', 'English_MatureBoss', 'system_voice_library', 'library', 'minimax', 'Bossy Lady', 'A mature, middle-aged female voice with a general American accent, conveying authority and a commanding presence.', '{"age": "middle_aged", "style": "audiobook", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A mature, middle-aged female voice with a general American accent, conveying authority and a commanding presence."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Male Debater
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KQS', 'English_Debator', 'system_voice_library', 'library', 'minimax', 'Male Debater', 'A tough, middle-aged male voice with a general American accent, perfect for debates and assertive arguments.', '{"age": "middle_aged", "style": "characters", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A tough, middle-aged male voice with a general American accent, perfect for debates and assertive arguments."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR5HX7QPVJ1BHHFRVTR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Whispering Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KQT', 'whisper_man', 'system_voice_library', 'library', 'minimax', 'Whispering Man', 'A mysterious adult male voice with a general American accent, delivered in a soft whisper for suspenseful content.', '{"age": "adult", "style": "characters", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A mysterious adult male voice with a general American accent, delivered in a soft whisper for suspenseful content."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Abbess
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KQV', 'English_Abbess', 'system_voice_library', 'library', 'minimax', 'Abbess', 'An adult female voice for an abbess character, speaking warily with a general American accent.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An adult female voice for an abbess character, speaking warily with a general American accent."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Lovely Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KQW', 'English_LovelyGirl', 'system_voice_library', 'library', 'minimax', 'Lovely Girl', 'A lovely and sweet female youth voice with a British accent, full of charm and innocence.', '{"age": "youth", "style": "characters", "accent": "EN-British", "gender": "female", "language": "en", "description": "A lovely and sweet female youth voice with a British accent, full of charm and innocence."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Whispering Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KQX', 'whisper_woman_1', 'system_voice_library', 'library', 'minimax', 'Whispering Woman', 'A soft, whispering adult female voice with a general American accent, creating a sense of intimacy and calm.', '{"age": "adult", "style": "characters", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A soft, whispering adult female voice with a general American accent, creating a sense of intimacy and calm."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KQY', 'English_Steadymentor', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A young adult male voice with a general American accent, projecting an air of arrogant reliability.', '{"age": "young_adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A young adult male voice with a general American accent, projecting an air of arrogant reliability."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Deep-voiced Gentleman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KQZ', 'English_Deep-VoicedGentleman', 'system_voice_library', 'library', 'minimax', 'Deep-voiced Gentleman', 'A deep-voiced and wise adult male gentleman with a classic British accent, sounding experienced and thoughtful.', '{"age": "adult", "style": "characters", "accent": "EN-British", "gender": "male", "language": "en", "description": "A deep-voiced and wise adult male gentleman with a classic British accent, sounding experienced and thoughtful."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Determined Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR0', 'English_DeterminedMan', 'system_voice_library', 'library', 'minimax', 'Determined Man', 'A determined adult male voice with a general American accent, conveying focus and unwavering resolve.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A determined adult male voice with a general American accent, conveying focus and unwavering resolve."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR1', 'English_Wiselady', 'system_voice_library', 'library', 'minimax', 'Wise Lady', 'A wise and genial middle-aged female voice with a British accent, offering kind and insightful words.', '{"age": "middle_aged", "style": "audiobook", "accent": "EN-British", "gender": "female", "language": "en", "description": "A wise and genial middle-aged female voice with a British accent, offering kind and insightful words."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Captivating Storyteller
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR2', 'English_CaptivatingStoryteller', 'system_voice_library', 'library', 'minimax', 'Captivating Storyteller', 'A captivating senior male storyteller with a cold, detached tone and a general American accent.', '{"age": "senior", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A captivating senior male storyteller with a cold, detached tone and a general American accent."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Attractive Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR3', 'English_AttractiveGirl', 'system_voice_library', 'library', 'minimax', 'Attractive Woman', 'An attractive and alluring adult female voice with a general American accent, projecting charm and appeal.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An attractive and alluring adult female voice with a general American accent, projecting charm and appeal."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Decent Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR4', 'English_DecentYoungMan', 'system_voice_library', 'library', 'minimax', 'Decent Young Man', 'A decent and respectable adult male voice with a British accent, sounding polite and well-mannered.', '{"age": "adult", "style": "informative", "accent": "EN-British", "gender": "male", "language": "en", "description": "A decent and respectable adult male voice with a British accent, sounding polite and well-mannered."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sentimental Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR5', 'English_SentimentalLady', 'system_voice_library', 'library', 'minimax', 'Sentimental Lady', 'A sentimental and elegant middle-aged female voice with a British accent, perfect for nostalgic or emotional readings.', '{"age": "middle_aged", "style": "audiobook", "accent": "EN-British", "gender": "female", "language": "en", "description": "A sentimental and elegant middle-aged female voice with a British accent, perfect for nostalgic or emotional readings."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Imposing Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR6', 'English_ImposingManner', 'system_voice_library', 'library', 'minimax', 'Imposing Queen', 'The imposing voice of an adult queen with a powerful British accent, commanding respect and authority.', '{"age": "adult", "style": "audiobook", "accent": "EN-British", "gender": "female", "language": "en", "description": "The imposing voice of an adult queen with a powerful British accent, commanding respect and authority."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Teen Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR7', 'English_SadTeen', 'system_voice_library', 'library', 'minimax', 'Teen Boy', 'A frustrated young adult male voice with a British accent, perfect for a teen character expressing annoyance.', '{"age": "young_adult", "style": "characters", "accent": "EN-British", "gender": "male", "language": "en", "description": "A frustrated young adult male voice with a British accent, perfect for a teen character expressing annoyance."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Thoughtful Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR8', 'English_ThoughtfulMan', 'system_voice_library', 'library', 'minimax', 'Thoughtful Man', 'A thoughtful young adult male voice, speaking solicitously with a general American accent to show care and concern.', '{"age": "young_adult", "style": "informative", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A thoughtful young adult male voice, speaking solicitously with a general American accent to show care and concern."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Passionate Warrior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KR9', 'English_PassionateWarrior', 'system_voice_library', 'library', 'minimax', 'Passionate Warrior', 'An energetic and passionate young adult male warrior voice with a general American accent, ready for battle.', '{"age": "young_adult", "style": "characters", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An energetic and passionate young adult male warrior voice with a general American accent, ready for battle."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAKZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Decent Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KRA', 'English_DecentBoy', 'system_voice_library', 'library', 'minimax', 'Decent Boy', 'A decent young man with an English accent, sounding earnest and respectable.', '{"age": "young_adult", "style": "informative", "accent": "England", "gender": "male", "language": "en", "description": "A decent young man with an English accent, sounding earnest and respectable."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR6GGE1CJ3JW11EZAM0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Scholar
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBXGN07RK26VC4X0KRB', 'English_WiseScholar', 'system_voice_library', 'library', 'minimax', 'Wise Scholar', 'A wise, conversational young adult scholar with a British accent, making complex topics accessible and engaging.', '{"age": "young_adult", "style": "audiobook", "accent": "EN-British", "gender": "male", "language": "en", "description": "A wise, conversational young adult scholar with a British accent, making complex topics accessible and engaging."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9M2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Soft-Spoken Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21J4', 'English_Soft-spokenGirl', 'system_voice_library', 'library', 'minimax', 'Soft-Spoken Girl', 'An adorable, soft-spoken female youth voice with a general American accent, gentle and sweet.', '{"age": "youth", "style": "characters", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An adorable, soft-spoken female youth voice with a general American accent, gentle and sweet."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9M3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Serene Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21J5', 'English_SereneWoman', 'system_voice_library', 'library', 'minimax', 'Serene Woman', 'A serene and friendly young adult female voice with a general American accent, calm and welcoming.', '{"age": "young_adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A serene and friendly young adult female voice with a general American accent, calm and welcoming."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9M4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21J6', 'English_ConfidentWoman', 'system_voice_library', 'library', 'minimax', 'Confident Woman', 'A confident and firm young adult female voice with a general American accent, assertive and clear.', '{"age": "young_adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A confident and firm young adult female voice with a general American accent, assertive and clear."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9M5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Patient Man(旧版不上线)
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21J7', 'English_PatientMan', 'system_voice_library', 'library', 'minimax', 'Patient Man(旧版不上线)', 'A patient adult male voice with a British accent, speaking in a calm and understanding manner.', '{"age": "adult", "style": "audiobook", "accent": "EN-British", "gender": "male", "language": "en", "description": "A patient adult male voice with a British accent, speaking in a calm and understanding manner."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9M6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Comedian
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21J8', 'English_Comedian', 'system_voice_library', 'library', 'minimax', 'Comedian', 'A breezy young adult male comedian with a British accent, delivering lines with a light and humorous touch.', '{"age": "young_adult", "style": "advertisement", "accent": "EN-British", "gender": "male", "language": "en", "description": "A breezy young adult male comedian with a British accent, delivering lines with a light and humorous touch."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9M7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gorgeous Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21J9', 'English_GorgeousLady', 'system_voice_library', 'library', 'minimax', 'Gorgeous Lady', 'An elegant and gorgeous adult female voice with a general American accent, exuding sophistication and style.', '{"age": "adult", "style": "characters", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An elegant and gorgeous adult female voice with a general American accent, exuding sophistication and style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9M8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bossy Leader
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JA', 'English_BossyLeader', 'system_voice_library', 'library', 'minimax', 'Bossy Leader', 'A bossy adult male leader with a general American accent, speaking unconcernedly with an air of command.', '{"age": "adult", "style": "advertisement", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A bossy adult male leader with a general American accent, speaking unconcernedly with an air of command."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9M9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Lovely Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JB', 'English_LovelyLady', 'system_voice_library', 'library', 'minimax', 'Lovely Lady', 'A lovely and vibrant adult female voice with a general American accent, full of life and energy.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A lovely and vibrant adult female voice with a general American accent, full of life and energy."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Strong-Willed Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JC', 'English_Strong-WilledBoy', 'system_voice_library', 'library', 'minimax', 'Strong-Willed Boy', 'A mature-sounding and strong-willed young adult male with a British accent, showing determination beyond his years.', '{"age": "young_adult", "style": "characters", "accent": "EN-British", "gender": "male", "language": "en", "description": "A mature-sounding and strong-willed young adult male with a British accent, showing determination beyond his years."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Deep-tonedMan
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JD', 'English_Deep-tonedMan', 'system_voice_library', 'library', 'minimax', 'Deep-tonedMan', 'A charismatic, deep-toned middle-aged man with a general American accent, naturally drawing in listeners.', '{"age": "middle_aged", "style": "characters", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A charismatic, deep-toned middle-aged man with a general American accent, naturally drawing in listeners."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Stressed Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JE', 'English_StressedLady', 'system_voice_library', 'library', 'minimax', 'Stressed Lady', 'An unsure, stressed middle-aged female voice with a general American accent, conveying anxiety and uncertainty.', '{"age": "middle_aged", "style": "characters", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An unsure, stressed middle-aged female voice with a general American accent, conveying anxiety and uncertainty."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Assertive Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JF', 'English_AssertiveQueen', 'system_voice_library', 'library', 'minimax', 'Assertive Queen', 'An assertive yet guarded young adult queen with a general American accent, projecting authority while remaining cautious.', '{"age": "young_adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An assertive yet guarded young adult queen with a general American accent, projecting authority while remaining cautious."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9ME.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Female Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JG', 'English_AnimeCharacter', 'system_voice_library', 'library', 'minimax', 'Female Narrator', 'A sincere middle-aged female narrator with a British accent, perfect for trustworthy and heartfelt storytelling.', '{"age": "middle_aged", "style": "characters", "accent": "EN-British", "gender": "female", "language": "en", "description": "A sincere middle-aged female narrator with a British accent, perfect for trustworthy and heartfelt storytelling."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Jovial Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JH', 'English_Jovialman', 'system_voice_library', 'library', 'minimax', 'Jovial Man', 'A jovial and mature middle-aged male voice with a general American accent, cheerful and good-natured.', '{"age": "middle_aged", "style": "characters", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A jovial and mature middle-aged male voice with a general American accent, cheerful and good-natured."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Whimsical Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JJ', 'English_WhimsicalGirl', 'system_voice_library', 'library', 'minimax', 'Whimsical Girl', 'A whimsical yet wary young adult female voice with a general American accent, combining playfulness with caution.', '{"age": "young_adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A whimsical yet wary young adult female voice with a general American accent, combining playfulness with caution."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Charming Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JK', 'English_CharmingQueen', 'system_voice_library', 'library', 'minimax', 'Charming Queen', 'A bewitching and charming adult queen with an English accent, captivating all who listen.', '{"age": "adult", "style": "characters", "accent": "England", "gender": "female", "language": "en", "description": "A bewitching and charming adult queen with an English accent, captivating all who listen."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind-Hearted Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JM', 'English_Kind-heartedGirl', 'system_voice_library', 'library', 'minimax', 'Kind-Hearted Girl', 'A kind-hearted and calm young adult female with a general American accent, speaking with gentle warmth.', '{"age": "young_adult", "style": "characters", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A kind-hearted and calm young adult female with a general American accent, speaking with gentle warmth."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Neighbor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JN', 'English_FriendlyNeighbor', 'system_voice_library', 'library', 'minimax', 'Friendly Neighbor', 'An energetic and friendly young adult female neighbor with a general American accent, cheerful and welcoming.', '{"age": "young_adult", "style": "advertisement", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An energetic and friendly young adult female neighbor with a general American accent, cheerful and welcoming."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR75P2G8RC8S90JR9MM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sweet Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JP', 'English_Sweet_Female_4', 'system_voice_library', 'library', 'minimax', 'Sweet Girl', 'A sweet and lively adult female voice with a general American accent, exuding charm and vivacity.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A sweet and lively adult female voice with a general American accent, exuding charm and vivacity."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0JW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Magnetic Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JQ', 'English_Magnetic_Male_2', 'system_voice_library', 'library', 'minimax', 'Magnetic Man', 'A magnetic adult male voice with a British accent, ideal for authoritative and engaging news reports.', '{"age": "adult", "style": "advertisement", "accent": "EN-British", "gender": "male", "language": "en", "description": "A magnetic adult male voice with a British accent, ideal for authoritative and engaging news reports."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0JX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Lively Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBY24D5AJ787S5Q21JR', 'English_Lively_Male_11', 'system_voice_library', 'library', 'minimax', 'Lively Man', 'A lively adult male voice with a general American accent, perfect for energetic and dynamic news reporting.', '{"age": "adult", "style": "advertisement", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A lively adult male voice with a general American accent, perfect for energetic and dynamic news reporting."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0JY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Women
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2ME7', 'English_Friendly_Female_3', 'system_voice_library', 'library', 'minimax', 'Friendly Women', 'A friendly adult female voice with a general American accent, suitable for warm and inviting broadcast content.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A friendly adult female voice with a general American accent, suitable for warm and inviting broadcast content."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0JZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Steady Women
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2ME8', 'English_Steady_Female_1', 'system_voice_library', 'library', 'minimax', 'Steady Women', 'A steady and reliable adult female voice with a general American accent, perfect for clear and consistent broadcasting.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A steady and reliable adult female voice with a general American accent, perfect for clear and consistent broadcasting."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- News Presenter
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2ME9', 'English_Lively_Male_10', 'system_voice_library', 'library', 'minimax', 'News Presenter', 'A professional adult male news presenter with a clear British accent, designed for formal news reporting.', '{"age": "adult", "style": "advertisement", "accent": "EN-British", "gender": "male", "language": "en", "description": "A professional adult male news presenter with a clear British accent, designed for formal news reporting."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Nature Show Host
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEA', 'English_Magnetic_Male_12', 'system_voice_library', 'library', 'minimax', 'Nature Show Host', 'A lively adult male host for a nature show, with an enthusiastic British accent that brings the outdoors to life.', '{"age": "adult", "style": "audiobook", "accent": "EN-British", "gender": "male", "language": "en", "description": "A lively adult male host for a nature show, with an enthusiastic British accent that brings the outdoors to life."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Female Actor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEB', 'English_Steady_Female_5', 'system_voice_library', 'library', 'minimax', 'Female Actor', 'A lively adult female actor with a versatile British accent, capable of a wide range of performances.', '{"age": "adult", "style": "informative", "accent": "EN-British", "gender": "female", "language": "en", "description": "A lively adult female actor with a versatile British accent, capable of a wide range of performances."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Insightful Speaker
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEC', 'English_Insightful_Speaker', 'system_voice_library', 'library', 'minimax', 'Insightful Speaker', 'An Adult Male English voice with a general American accent, characterized by an Explanatory style.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An Adult Male English voice with a general American accent, characterized by an Explanatory style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Patient Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MED', 'English_patient_man_v1', 'system_voice_library', 'library', 'minimax', 'Patient Man', 'An Adult Male English voice with a British accent, characterized by a Patient style.', '{"age": "adult", "style": "audiobook", "accent": "EN-British", "gender": "male", "language": "en", "description": "An Adult Male English voice with a British accent, characterized by a Patient style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Persuasive Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEE', 'English_Persuasive_Man', 'system_voice_library', 'library', 'minimax', 'Persuasive Man', 'An Adult Male English voice with a general American accent, characterized by a Persuasive style.', '{"age": "adult", "style": "advertisement", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An Adult Male English voice with a general American accent, characterized by a Persuasive style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Explanatory Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEF', 'English_Explanatory_Man', 'system_voice_library', 'library', 'minimax', 'Explanatory Man', 'An Adult Male English voice with a general American accent, characterized by an Explanatory style.', '{"age": "adult", "style": "advertisement", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An Adult Male English voice with a general American accent, characterized by an Explanatory style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Intellect Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEG', 'English_intellect_female_1', 'system_voice_library', 'library', 'minimax', 'Intellect Woman', 'An Adult Female English voice with a general American accent, featuring a Podcast style suitable for intellectual content.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An Adult Female English voice with a general American accent, featuring a Podcast style suitable for intellectual content."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Energetic man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEH', 'English_energetic_male_1', 'system_voice_library', 'library', 'minimax', 'Energetic man', 'An Adult Male English voice with a general American accent, characterized by a Leadership style.', '{"age": "adult", "style": "advertisement", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An Adult Male English voice with a general American accent, characterized by a Leadership style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0K9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Witty woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEJ', 'English_witty_female_1', 'system_voice_library', 'library', 'minimax', 'Witty woman', 'An Adult Female English voice with a general American accent, characterized by a Witty style.', '{"age": "adult", "style": "social_media", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An Adult Female English voice with a general American accent, characterized by a Witty style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Lucky Robot
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEK', 'English_Lucky_Robot', 'system_voice_library', 'library', 'minimax', 'Lucky Robot', 'A Male English voice with a general American accent, characterized by a robotic style.', '{"age": "adult", "style": "characters", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A Male English voice with a general American accent, characterized by a robotic style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cute Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEM', 'English_Cute_Girl', 'system_voice_library', 'library', 'minimax', 'Cute Girl', 'A Young Adult Female English voice with a Spanish accent, characterized by a Cute style.', '{"age": "young_adult", "style": "characters", "accent": "EN-Spanish", "gender": "female", "language": "en", "description": "A Young Adult Female English voice with a Spanish accent, characterized by a Cute style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sharp Commentator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEN', 'English_Sharp_Commentator', 'system_voice_library', 'library', 'minimax', 'Sharp Commentator', 'An Adult Female English voice with a general American accent, characterized by a Lively commentary style.', '{"age": "adult", "style": "informative", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An Adult Female English voice with a general American accent, characterized by a Lively commentary style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Honest Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEP', 'English_Honest_Man', 'system_voice_library', 'library', 'minimax', 'Honest Man', 'An Adult Male English voice with an African accent, characterized by a Sincere style.', '{"age": "adult", "style": "informative", "accent": "EN-African", "gender": "male", "language": "en", "description": "An Adult Male English voice with an African accent, characterized by a Sincere style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Angry Pirate
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEQ', 'angry_pirate_1', 'system_voice_library', 'library', 'minimax', 'Angry Pirate', 'An Adult Male English voice with a general American accent, characterized by a Raspy, pirate-like style.', '{"age": "adult", "style": "characters", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An Adult Male English voice with a general American accent, characterized by a Raspy, pirate-like style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Giant
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MER', 'massive_kind_troll', 'system_voice_library', 'library', 'minimax', 'Friendly Giant', 'An Adult Male English voice with a general American accent, characterized by a deep and Steady, giant-like style.', '{"age": "adult", "style": "characters", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An Adult Male English voice with a general American accent, characterized by a deep and Steady, giant-like style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Movie Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MES', 'movie_trailer_deep', 'system_voice_library', 'library', 'minimax', 'Movie Narrator', 'An Adult Male English voice with a general American accent, featuring a Deep, cinematic style suitable for movie trailers.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "An Adult Male English voice with a general American accent, featuring a Deep, cinematic style suitable for movie trailers."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Peaceful Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MET', 'peace_and_ease', 'system_voice_library', 'library', 'minimax', 'Peaceful Lady', 'An Adult Female English voice with a general American accent, characterized by a Peaceful and calm style.', '{"age": "adult", "style": "audiobook", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An Adult Female English voice with a general American accent, characterized by a Peaceful and calm style."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- WiseGrandma
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEV', 'moss_audio_6dc281eb-713c-11f0-a447-9613c873494c', 'system_voice_library', 'library', 'minimax', 'WiseGrandma', 'A sweet old granny, mumbling slightly, sharing life lessons with you with great warmth.', '{"age": "senior", "style": "conversational", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A sweet old granny, mumbling slightly, sharing life lessons with you with great warmth."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- EngagingGirl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEW', 'moss_audio_c12a59b9-7115-11f0-a447-9613c873494c', 'system_voice_library', 'library', 'minimax', 'EngagingGirl', 'An engaging and expressive vocal tone, typical of a young woman.', '{"age": "young_adult", "style": "social_media", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An engaging and expressive vocal tone, typical of a young woman."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Southern Dude
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEX', 'moss_audio_076697ad-7144-11f0-a447-9613c873494c', 'system_voice_library', 'library', 'minimax', 'Southern Dude', 'A young guy, full of confidence, speaking with a heavy Southern drawl.', '{"age": "adult", "style": "social_media", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A young guy, full of confidence, speaking with a heavy Southern drawl."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- KnowledgePill
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEY', 'moss_audio_737a299c-734a-11f0-918f-4e0486034804', 'system_voice_library', 'library', 'minimax', 'KnowledgePill', 'A vibrant young male voice, with the kind of clear, trustworthy delivery ideal for science communication.', '{"age": "young_adult", "style": "social_media", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A vibrant young male voice, with the kind of clear, trustworthy delivery ideal for science communication."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- CandidGirl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MEZ', 'moss_audio_19dbb103-7350-11f0-ad20-f2bc95e89150', 'system_voice_library', 'library', 'minimax', 'CandidGirl', 'A sassy girl with a tone that blends sarcasm and surprise.', '{"age": "young_adult", "style": "social_media", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A sassy girl with a tone that blends sarcasm and surprise."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- ChatterZoe
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MF0', 'moss_audio_7c7e7ae2-7356-11f0-9540-7ef9b4b62566', 'system_voice_library', 'library', 'minimax', 'ChatterZoe', 'A magnetic young woman''s voice with a hint of urgency.', '{"age": "young_adult", "style": "conversational", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A magnetic young woman''s voice with a hint of urgency."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- ContrarianKonrad
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTBZ8F67J9MPKW3S2MF1', 'moss_audio_570551b1-735c-11f0-b236-0adeeecad052', 'system_voice_library', 'library', 'minimax', 'ContrarianKonrad', 'A self-assured man with a German accent. He comes across as cocky.', '{"age": "adult", "style": "social_media", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A self-assured man with a German accent. He comes across as cocky."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR8TKG34321T7KYY0KS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- ChillBestie
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6QV', 'moss_audio_ad5baf92-735f-11f0-8263-fe5a2fe98ec8', 'system_voice_library', 'library', 'minimax', 'ChillBestie', 'A young girl with a sweet voice, who sounds like she''s thinking aloud as she talks to a friend.', '{"age": "young_adult", "style": "conversational", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A young girl with a sweet voice, who sounds like she''s thinking aloud as she talks to a friend."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B7Y.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- BoringHusband
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6QW', 'moss_audio_cedfd4d2-736d-11f0-99be-fe40dd2a5fe8', 'system_voice_library', 'library', 'minimax', 'BoringHusband', 'The voice of a bored husband attempting to sound casual as he makes conversation.', '{"age": "middle_aged", "style": "conversational", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "The voice of a bored husband attempting to sound casual as he makes conversation."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B7Z.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- ApproachableDan
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6QX', 'moss_audio_a0d611da-737c-11f0-ad20-f2bc95e89150', 'system_voice_library', 'library', 'minimax', 'ApproachableDan', 'A middle-aged man with a warm and welcoming voice, delivering an introduction', '{"age": "middle_aged", "style": "conversational", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A middle-aged man with a warm and welcoming voice, delivering an introduction"}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B80.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- UnderstatedCamden
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6QY', 'moss_audio_4f4172f4-737b-11f0-9540-7ef9b4b62566', 'system_voice_library', 'library', 'minimax', 'UnderstatedCamden', 'A middle-aged man speaking about his hobbies in a quiet, unassuming way', '{"age": "middle_aged", "style": "conversational", "accent": "EN-US (General)", "gender": "male", "language": "en", "description": "A middle-aged man speaking about his hobbies in a quiet, unassuming way"}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B81.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- BubblyLexi
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6QZ', 'moss_audio_62ca20b0-7380-11f0-99be-fe40dd2a5fe8', 'system_voice_library', 'library', 'minimax', 'BubblyLexi', 'An energetic young woman who is slightly pretentious.', '{"age": "young_adult", "style": "conversational", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "An energetic young woman who is slightly pretentious."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B82.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Relatable Riley
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R0', 'conversational_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Relatable Riley', 'A youthful and conversational female voice, natural and authentic. Perfect for vlogs, social media content, and casual storytelling', '{"age": "young_adult", "style": "conversational", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A youthful and conversational female voice, natural and authentic. Perfect for vlogs, social media content, and casual storytelling"}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B83.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Paige
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R1', 'conversational_female_2_v1', 'system_voice_library', 'library', 'minimax', 'Friendly Paige', 'A friendly and supportive young adult female voice, perfect for conversational content, lifestyle vlogs, or offering advice like a caring older sister.', '{"age": "young_adult", "style": "conversational", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A friendly and supportive young adult female voice, perfect for conversational content, lifestyle vlogs, or offering advice like a caring older sister."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B84.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Upbeat Ashley
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R2', 'socialmedia_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Upbeat Ashley', 'A youthful and energetic American female voice, characterized by a fast-paced, confident delivery.', '{"age": "young_adult", "style": "social_media", "accent": "EN-US (General)", "gender": "female", "language": "en", "description": "A youthful and energetic American female voice, characterized by a fast-paced, confident delivery."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B85.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kindergarten Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R3', 'BritishChild_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Kindergarten Boy', 'A bright and innocent young boy’s voice in British English.', '{"age": "youth", "style": "characters", "accent": "EN-British", "gender": "male", "language": "en", "description": "A bright and innocent young boy\u2019s voice in British English."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B86.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bubbly Kid
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R4', 'BritishChild_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Bubbly Kid', 'A gentle and sweet young girl’s voice in British English.', '{"age": "youth", "style": "characters", "accent": "EN-British", "gender": "female", "language": "en", "description": "A gentle and sweet young girl\u2019s voice in British English."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B87.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Executive
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R5', 'Chinese (Mandarin)_Reliable_Executive', 'system_voice_library', 'library', 'minimax', 'Reliable Executive', 'A steady and reliable middle-aged male executive voice in Standard Mandarin, conveying trustworthiness.', '{"age": "middle_aged", "style": "characters", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A steady and reliable middle-aged male executive voice in Standard Mandarin, conveying trustworthiness."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B88.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- News Anchor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R6', 'Chinese (Mandarin)_News_Anchor', 'system_voice_library', 'library', 'minimax', 'News Anchor', 'A professional, broadcaster-like middle-aged female news anchor in Standard Mandarin.', '{"age": "middle_aged", "style": "broadcast", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A professional, broadcaster-like middle-aged female news anchor in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B89.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Unrestrained Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R7', 'Chinese (Mandarin)_Unrestrained_Young_Man', 'system_voice_library', 'library', 'minimax', 'Unrestrained Young Man', 'An unrestrained and free-spirited adult male voice in Standard Mandarin.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "An unrestrained and free-spirited adult male voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B8A.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Mature Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R8', 'Chinese (Mandarin)_Mature_Woman', 'system_voice_library', 'library', 'minimax', 'Mature Woman', 'A charming and mature adult female voice in Standard Mandarin.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A charming and mature adult female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B8B.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Arrogant Miss
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6R9', 'Arrogant_Miss', 'system_voice_library', 'library', 'minimax', 'Arrogant Miss', 'An arrogant adult female voice in Standard Mandarin, projecting confidence and superiority.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "An arrogant adult female voice in Standard Mandarin, projecting confidence and superiority."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B8C.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind-hearted Antie
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6RA', 'Chinese (Mandarin)_Kind-hearted_Antie', 'system_voice_library', 'library', 'minimax', 'Kind-hearted Antie', 'A gentle and kind-hearted middle-aged "antie" voice in Standard Mandarin, warm and caring.', '{"age": "middle_aged", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A gentle and kind-hearted middle-aged \"antie\" voice in Standard Mandarin, warm and caring."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B8D.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Robot Armor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6RB', 'Robot_Armor', 'system_voice_library', 'library', 'minimax', 'Robot Armor', 'An electronic, robotic adult male voice, suitable for sci-fi or futuristic content in Standard Mandarin.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "An electronic, robotic adult male voice, suitable for sci-fi or futuristic content in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B8E.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Refreshing Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6RC', 'hunyin_6', 'system_voice_library', 'library', 'minimax', 'Refreshing Young Man', 'A cheerful and refreshing adult male voice in Standard Mandarin, bright and positive.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A cheerful and refreshing adult male voice in Standard Mandarin, bright and positive."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B8F.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- HK Flight Attendant
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6RD', 'Chinese (Mandarin)_HK_Flight_Attendant', 'system_voice_library', 'library', 'minimax', 'HK Flight Attendant', 'A polite middle-aged female flight attendant with a Southern Chinese accent, clear and courteous.', '{"age": "middle_aged", "style": "social_media", "accent": "CN-Southern", "gender": "female", "language": "chinese (mandarin)", "description": "A polite middle-aged female flight attendant with a Southern Chinese accent, clear and courteous."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B8G.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Humorous Elder
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6RE', 'Chinese (Mandarin)_Humorous_Elder', 'system_voice_library', 'library', 'minimax', 'Humorous Elder', 'A refreshing and humorous senior male voice with a Northern Chinese accent, full of character.', '{"age": "senior", "style": "characters", "accent": "CN-Northern", "gender": "male", "language": "chinese (mandarin)", "description": "A refreshing and humorous senior male voice with a Northern Chinese accent, full of character."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JR9F070KX847BTN8B8H.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentleman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6RF', 'Chinese (Mandarin)_Gentleman', 'system_voice_library', 'library', 'minimax', 'Gentleman', 'A magnetic and charismatic adult male gentleman in Standard Mandarin.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A magnetic and charismatic adult male gentleman in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Warm Bestie
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6RG', 'Chinese (Mandarin)_Warm_Bestie', 'system_voice_library', 'library', 'minimax', 'Warm Bestie', 'A warm and crisp adult female "bestie" voice in Standard Mandarin, friendly and clear.', '{"age": "adult", "style": "informative", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A warm and crisp adult female \"bestie\" voice in Standard Mandarin, friendly and clear."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Stubborn Friend
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC0ZQWXC7WJVRE9Y6RH', 'Chinese (Mandarin)_Stubborn_Friend', 'system_voice_library', 'library', 'minimax', 'Stubborn Friend', 'An uninhibited and stubborn adult male friend''s voice in Standard Mandarin.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "An uninhibited and stubborn adult male friend''s voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sweet Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZG', 'Chinese (Mandarin)_Sweet_Lady', 'system_voice_library', 'library', 'minimax', 'Sweet Lady', 'A tender and sweet adult female voice in Standard Mandarin.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A tender and sweet adult female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Southern Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZH', 'Chinese (Mandarin)_Southern_Young_Man', 'system_voice_library', 'library', 'minimax', 'Southern Young Man', 'An earnest adult male voice with a Southern Chinese accent.', '{"age": "adult", "style": "audiobook", "accent": "CN-Southern", "gender": "male", "language": "chinese (mandarin)", "description": "An earnest adult male voice with a Southern Chinese accent."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Women
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZJ', 'Chinese (Mandarin)_Wise_Women', 'system_voice_library', 'library', 'minimax', 'Wise Women', 'A lyrical and wise middle-aged female voice in Standard Mandarin.', '{"age": "middle_aged", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A lyrical and wise middle-aged female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZK', 'Chinese (Mandarin)_Gentle_Youth', 'system_voice_library', 'library', 'minimax', 'Gentle Youth', 'A gentle adult male youth voice in Standard Mandarin.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A gentle adult male youth voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Warm Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZM', 'Chinese (Mandarin)_Warm_Girl', 'system_voice_library', 'library', 'minimax', 'Warm Girl', 'A soft and warm young adult female voice in Standard Mandarin.', '{"age": "young_adult", "style": "broadcast", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A soft and warm young adult female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Male Announcer
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZN', 'Chinese (Mandarin)_Male_Announcer', 'system_voice_library', 'library', 'minimax', 'Male Announcer', 'A magnetic middle-aged male announcer voice in Standard Mandarin, clear and authoritative.', '{"age": "middle_aged", "style": "broadcast", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A magnetic middle-aged male announcer voice in Standard Mandarin, clear and authoritative."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind-hearted Elder
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZP', 'Chinese (Mandarin)_Kind-hearted_Elder', 'system_voice_library', 'library', 'minimax', 'Kind-hearted Elder', 'A kind and gentle senior female voice in Standard Mandarin.', '{"age": "senior", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A kind and gentle senior female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cute Spirit
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZQ', 'Chinese (Mandarin)_Cute_Spirit', 'system_voice_library', 'library', 'minimax', 'Cute Spirit', 'An adorable and cute female spirit voice, youthful and sweet, in Standard Mandarin.', '{"age": "youth", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "An adorable and cute female spirit voice, youthful and sweet, in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRAHNEG0G9W8AAD1NFT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Radio Host
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZR', 'Chinese (Mandarin)_Radio_Host', 'system_voice_library', 'library', 'minimax', 'Radio Host', 'A poetic adult male radio host in Standard Mandarin, with a smooth and engaging delivery.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A poetic adult male radio host in Standard Mandarin, with a smooth and engaging delivery."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Lyrical Voice
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZS', 'Chinese (Mandarin)_Lyrical_Voice', 'system_voice_library', 'library', 'minimax', 'Lyrical Voice', 'A mellow and lyrical adult male voice in Standard Mandarin, smooth and expressive.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A mellow and lyrical adult male voice in Standard Mandarin, smooth and expressive."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Straightforward Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZT', 'Chinese (Mandarin)_Straightforward_Boy', 'system_voice_library', 'library', 'minimax', 'Straightforward Boy', 'A thoughtful and straightforward young adult male voice in Standard Mandarin.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A thoughtful and straightforward young adult male voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sincere Adult
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC13XCFEH6KZFV20FZV', 'Chinese (Mandarin)_Sincere_Adult', 'system_voice_library', 'library', 'minimax', 'Sincere Adult', 'A sincere and encouraging adult male voice in Standard Mandarin.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A sincere and encouraging adult male voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Senior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA1', 'Chinese (Mandarin)_Gentle_Senior', 'system_voice_library', 'library', 'minimax', 'Gentle Senior', 'A gentle and cozy adult female senior voice in Standard Mandarin.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A gentle and cozy adult female senior voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Crisp Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA2', 'Chinese (Mandarin)_Crisp_Girl', 'system_voice_library', 'library', 'minimax', 'Crisp Girl', 'A warm and crisp young adult female voice in Standard Mandarin.', '{"age": "young_adult", "style": "broadcast", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A warm and crisp young adult female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Pure-hearted Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA3', 'Chinese (Mandarin)_Pure-hearted_Boy', 'system_voice_library', 'library', 'minimax', 'Pure-hearted Boy', 'A committed and pure-hearted young adult male voice in Standard Mandarin.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "chinese (mandarin)", "description": "A committed and pure-hearted young adult male voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Soft Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA4', 'Chinese (Mandarin)_Soft_Girl', 'system_voice_library', 'library', 'minimax', 'Soft Girl', 'A welcoming and soft adult female voice with a Southern Chinese accent.', '{"age": "adult", "style": "social_media", "accent": "CN-Southern", "gender": "female", "language": "chinese (mandarin)", "description": "A welcoming and soft adult female voice with a Southern Chinese accent."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Intellectual Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA5', 'Chinese (Mandarin)_IntellectualGirl', 'system_voice_library', 'library', 'minimax', 'Intellectual Girl', 'An intellectual adult female voice in Standard Mandarin, clear and knowledgeable.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "An intellectual adult female voice in Standard Mandarin, clear and knowledgeable."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Warm-hearted Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA6', 'Chinese (Mandarin)_Warm_HeartedGirl', 'system_voice_library', 'library', 'minimax', 'Warm-hearted Girl', 'A warm-hearted and caring adult female voice in Standard Mandarin.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A warm-hearted and caring adult female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZABZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Laid-back Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA7', 'Chinese (Mandarin)_Laid_BackGirl', 'system_voice_library', 'library', 'minimax', 'Laid-back Girl', 'A relaxed and laid-back adult female voice in Standard Mandarin.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A relaxed and laid-back adult female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Explorative Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA8', 'Chinese (Mandarin)_ExplorativeGirl', 'system_voice_library', 'library', 'minimax', 'Explorative Girl', 'An explorative and curious adult female voice in Standard Mandarin.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "An explorative and curious adult female voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Warm-hearted Aunt
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAA9', 'Chinese (Mandarin)_Warm-HeartedAunt', 'system_voice_library', 'library', 'minimax', 'Warm-hearted Aunt', 'A kind and warm-hearted middle-aged auntie voice in Standard Mandarin.', '{"age": "middle_aged", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A kind and warm-hearted middle-aged auntie voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bashful Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAA', 'Chinese (Mandarin)_BashfulGirl', 'system_voice_library', 'library', 'minimax', 'Bashful Girl', 'A bashful and shy female youth voice in Standard Mandarin.', '{"age": "youth", "style": "characters", "accent": "Standard", "gender": "female", "language": "chinese (mandarin)", "description": "A bashful and shy female youth voice in Standard Mandarin."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAB', 'Arabic_CalmWoman', 'system_voice_library', 'library', 'minimax', 'Calm Woman', 'A calm adult female Arabic voice, ideal for audiobooks and serene narration.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "ar", "description": "A calm adult female Arabic voice, ideal for audiobooks and serene narration."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Guy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAC', 'Arabic_FriendlyGuy', 'system_voice_library', 'library', 'minimax', 'Friendly Guy', 'A natural and friendly adult male Arabic voice.', '{"age": "adult", "style": "natural", "accent": "Standard", "gender": "male", "language": "ar", "description": "A natural and friendly adult male Arabic voice."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Professional Female Host
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAD', 'Cantonese_ProfessionalHost（F)', 'system_voice_library', 'library', 'minimax', 'Professional Female Host', 'A neutral and professional adult female host in Cantonese.', '{"age": "adult", "style": "neutral", "accent": "Standard", "gender": "female", "language": "cantonese", "description": "A neutral and professional adult female host in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAE', 'Cantonese_GentleLady', 'system_voice_library', 'library', 'minimax', 'Gentle Lady', 'A calm and gentle adult female voice in Cantonese.', '{"age": "adult", "style": "calm", "accent": "Standard", "gender": "female", "language": "cantonese", "description": "A calm and gentle adult female voice in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Professional Male Host
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAF', 'Cantonese_ProfessionalHost（M)', 'system_voice_library', 'library', 'minimax', 'Professional Male Host', 'A neutral and professional adult male host in Cantonese.', '{"age": "adult", "style": "neutral", "accent": "Standard", "gender": "male", "language": "cantonese", "description": "A neutral and professional adult male host in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Playful Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAG', 'Cantonese_PlayfulMan', 'system_voice_library', 'library', 'minimax', 'Playful Man', 'A soulful and playful adult male voice in Cantonese.', '{"age": "adult", "style": "soulful", "accent": "Standard", "gender": "male", "language": "cantonese", "description": "A soulful and playful adult male voice in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZAC9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cute Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAH', 'Cantonese_CuteGirl', 'system_voice_library', 'library', 'minimax', 'Cute Girl', 'A soothing and cute young adult female voice in Cantonese.', '{"age": "young_adult", "style": "soothing", "accent": "Standard", "gender": "female", "language": "cantonese", "description": "A soothing and cute young adult female voice in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZACA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAJ', 'Cantonese_KindWoman', 'system_voice_library', 'library', 'minimax', 'Kind Woman', 'A friendly and kind adult female voice in Cantonese.', '{"age": "adult", "style": "friendly", "accent": "Standard", "gender": "female", "language": "cantonese", "description": "A friendly and kind adult female voice in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZACB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAK', 'Cantonese_Narrator', 'system_voice_library', 'library', 'minimax', 'Narrator', 'A classic middle-aged male narrator voice in Cantonese.', '{"age": "middle_aged", "style": "narrator", "accent": "Standard", "gender": "male", "language": "cantonese", "description": "A classic middle-aged male narrator voice in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZACC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Professor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAM', 'Cantonese_WiselProfessor', 'system_voice_library', 'library', 'minimax', 'Wise Professor', 'A gentle and wise adult male professor''s voice in Cantonese.', '{"age": "adult", "style": "gentle", "accent": "Standard", "gender": "male", "language": "cantonese", "description": "A gentle and wise adult male professor''s voice in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZACD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Indifferent Staff
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAN', 'Cantonese_IndifferentStaff', 'system_voice_library', 'library', 'minimax', 'Indifferent Staff', 'A convincing yet indifferent adult male staff voice in Cantonese.', '{"age": "adult", "style": "convincing", "accent": "Standard", "gender": "male", "language": "cantonese", "description": "A convincing yet indifferent adult male staff voice in Cantonese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZACE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind-hearted girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAP', 'Dutch_kindhearted_girl', 'system_voice_library', 'library', 'minimax', 'Kind-hearted girl', 'A warm and kind-hearted young adult female voice in Dutch.', '{"age": "young_adult", "style": "warm", "accent": "Standard", "gender": "female", "language": "nl", "description": "A warm and kind-hearted young adult female voice in Dutch."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZACF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bossy leader
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC21SK2WX0JGPZVVAAQ', 'Dutch_bossy_leader', 'system_voice_library', 'library', 'minimax', 'Bossy leader', 'A serious and bossy adult male leader''s voice in Dutch.', '{"age": "adult", "style": "serious", "accent": "Standard", "gender": "male", "language": "nl", "description": "A serious and bossy adult male leader''s voice in Dutch."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRB1109G8BHYAFJZACG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Level-Headed Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMJ', 'French_Male_Speech_New', 'system_voice_library', 'library', 'minimax', 'Level-Headed Man', 'A level-headed and composed adult male voice in French.', '{"age": "adult", "style": "level-headed", "accent": "Standard", "gender": "male", "language": "fr", "description": "A level-headed and composed adult male voice in French."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Patient Female Presenter
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMK', 'French_Female_News Anchor', 'system_voice_library', 'library', 'minimax', 'Patient Female Presenter', 'A patient adult female presenter in French, calm and clear.', '{"age": "adult", "style": "patient", "accent": "Standard", "gender": "female", "language": "fr", "description": "A patient adult female presenter in French, calm and clear."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Casual Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMM', 'French_CasualMan', 'system_voice_library', 'library', 'minimax', 'Casual Man', 'A casual and relaxed middle-aged male voice in French.', '{"age": "middle_aged", "style": "casual", "accent": "Standard", "gender": "male", "language": "fr", "description": "A casual and relaxed middle-aged male voice in French."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Movie Lead Female
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMN', 'French_MovieLeadFemale', 'system_voice_library', 'library', 'minimax', 'Movie Lead Female', 'A cinematic young adult female lead voice in French, perfect for film.', '{"age": "young_adult", "style": "film", "accent": "Standard", "gender": "female", "language": "fr", "description": "A cinematic young adult female lead voice in French, perfect for film."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Female Anchor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMP', 'French_FemaleAnchor', 'system_voice_library', 'library', 'minimax', 'Female Anchor', 'A professional adult female anchor voice in French, authoritative and clear.', '{"age": "adult", "style": "anchor", "accent": "Standard", "gender": "female", "language": "fr", "description": "A professional adult female anchor voice in French, authoritative and clear."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Male Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMQ', 'French_MaleNarrator', 'system_voice_library', 'library', 'minimax', 'Male Narrator', 'A classic adult male narrator voice in French, ideal for storytelling.', '{"age": "adult", "style": "narrator", "accent": "Standard", "gender": "male", "language": "fr", "description": "A classic adult male narrator voice in French, ideal for storytelling."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Fluent Female Broadcaster
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMR', 'French_Female Journalist', 'system_voice_library', 'library', 'minimax', 'Fluent Female Broadcaster', 'A fluent and articulate adult female broadcaster in French.', '{"age": "adult", "style": "fluent", "accent": "Standard", "gender": "female", "language": "fr", "description": "A fluent and articulate adult female broadcaster in French."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Persuasive Female Speaker
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMS', 'French_Female_Speech_New', 'system_voice_library', 'library', 'minimax', 'Persuasive Female Speaker', 'A persuasive adult female speaker in French, confident and convincing.', '{"age": "adult", "style": "persuasive", "accent": "Standard", "gender": "female", "language": "fr", "description": "A persuasive adult female speaker in French, confident and convincing."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMT', 'German_FriendlyMan', 'system_voice_library', 'library', 'minimax', 'Friendly Man', 'A sincere and friendly middle-aged male voice in German.', '{"age": "middle_aged", "style": "sincere", "accent": "Standard", "gender": "male", "language": "de", "description": "A sincere and friendly middle-aged male voice in German."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sweet Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMV', 'German_SweetLady', 'system_voice_library', 'library', 'minimax', 'Sweet Lady', 'An animated and sweet adult female voice in German.', '{"age": "adult", "style": "animated", "accent": "Standard", "gender": "female", "language": "de", "description": "An animated and sweet adult female voice in German."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Playful Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMW', 'German_PlayfulMan', 'system_voice_library', 'library', 'minimax', 'Playful Man', 'A lively and spirited adult male voice in German, full of energy.', '{"age": "adult", "style": "lively_and_spirited", "accent": "Standard", "gender": "male", "language": "de", "description": "A lively and spirited adult male voice in German, full of energy."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1RZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sweet Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMX', 'Indonesian_SweetGirl', 'system_voice_library', 'library', 'minimax', 'Sweet Girl', 'A cute and sweet young adult female voice in Indonesian.', '{"age": "young_adult", "style": "cute_and_sweet", "accent": "Standard", "gender": "female", "language": "id", "description": "A cute and sweet young adult female voice in Indonesian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1S0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reserved Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMY', 'Indonesian_ReservedYoungMan', 'system_voice_library', 'library', 'minimax', 'Reserved Young Man', 'A cold and reserved young adult male voice in Indonesian.', '{"age": "young_adult", "style": "cold_and_reserved", "accent": "Standard", "gender": "male", "language": "id", "description": "A cold and reserved young adult male voice in Indonesian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1S1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Charming Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFMZ', 'Indonesian_CharmingGirl', 'system_voice_library', 'library', 'minimax', 'Charming Girl', 'An alluring and charming adult female voice in Indonesian.', '{"age": "adult", "style": "alluring", "accent": "Standard", "gender": "female", "language": "id", "description": "An alluring and charming adult female voice in Indonesian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRCNR2XCV6BKDPFF1S2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFN0', 'Indonesian_CalmWoman', 'system_voice_library', 'library', 'minimax', 'Calm Woman', 'A serene and calm young adult female voice in Indonesian.', '{"age": "young_adult", "style": "serene", "accent": "Standard", "gender": "female", "language": "id", "description": "A serene and calm young adult female voice in Indonesian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7GR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFN1', 'Indonesian_ConfidentWoman', 'system_voice_library', 'library', 'minimax', 'Confident Woman', 'An assertive and confident young adult female voice in Indonesian.', '{"age": "young_adult", "style": "assertive", "accent": "Standard", "gender": "female", "language": "id", "description": "An assertive and confident young adult female voice in Indonesian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7GS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Caring Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFN2', 'Indonesian_CaringMan', 'system_voice_library', 'library', 'minimax', 'Caring Man', 'A compassionate and caring young adult male voice in Indonesian.', '{"age": "young_adult", "style": "compassionate", "accent": "Standard", "gender": "male", "language": "id", "description": "A compassionate and caring young adult male voice in Indonesian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7GT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bossy Leader
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFN3', 'Indonesian_BossyLeader', 'system_voice_library', 'library', 'minimax', 'Bossy Leader', 'A calm, authoritative, and bossy adult male leader''s voice in Indonesian.', '{"age": "adult", "style": "calm_and_authoritative", "accent": "Standard", "gender": "male", "language": "id", "description": "A calm, authoritative, and bossy adult male leader''s voice in Indonesian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7GV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Determined Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC34JNC3943CGYFGFN4', 'Indonesian_DeterminedBoy', 'system_voice_library', 'library', 'minimax', 'Determined Boy', 'A mature and resolute young adult male voice in Indonesian, conveying determination.', '{"age": "young_adult", "style": "mature_and_resolute", "accent": "Standard", "gender": "male", "language": "id", "description": "A mature and resolute young adult male voice in Indonesian, conveying determination."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7GW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0M', 'Indonesian_GentleGirl', 'system_voice_library', 'library', 'minimax', 'Gentle Girl', 'A soft-spoken and gentle young adult female voice in Indonesian.', '{"age": "young_adult", "style": "soft-spoken", "accent": "Standard", "gender": "female", "language": "id", "description": "A soft-spoken and gentle young adult female voice in Indonesian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7GX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Brave Heroine
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0N', 'Italian_BraveHeroine', 'system_voice_library', 'library', 'minimax', 'Brave Heroine', 'A calm and brave middle-aged female heroine''s voice in Italian.', '{"age": "middle_aged", "style": "calm", "accent": "Standard", "gender": "female", "language": "it", "description": "A calm and brave middle-aged female heroine''s voice in Italian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7GY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0P', 'Italian_Narrator', 'system_voice_library', 'library', 'minimax', 'Narrator', 'A classic middle-aged male narrator voice in Italian.', '{"age": "middle_aged", "style": "narrator", "accent": "Standard", "gender": "male", "language": "it", "description": "A classic middle-aged male narrator voice in Italian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7GZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wandering Sorcerer
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0Q', 'Italian_WanderingSorcerer', 'system_voice_library', 'library', 'minimax', 'Wandering Sorcerer', 'A ruthless adult female wandering sorcerer''s voice in Italian.', '{"age": "adult", "style": "ruthless", "accent": "Standard", "gender": "female", "language": "it", "description": "A ruthless adult female wandering sorcerer''s voice in Italian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7H0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Diligent Leader
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0R', 'Italian_DiligentLeader', 'system_voice_library', 'library', 'minimax', 'Diligent Leader', 'A calm and diligent adult female leader''s voice in Italian.', '{"age": "adult", "style": "calm", "accent": "Standard", "gender": "female", "language": "it", "description": "A calm and diligent adult female leader''s voice in Italian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7H1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0S', 'Italian_ReliableMan', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A confident and reliable adult male voice in Italian.', '{"age": "adult", "style": "confident", "accent": "Standard", "gender": "male", "language": "it", "description": "A confident and reliable adult male voice in Italian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7H2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Athletic Student
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0T', 'Italian_AthleticStudent', 'system_voice_library', 'library', 'minimax', 'Athletic Student', 'A charming adult male athletic student''s voice in Italian.', '{"age": "adult", "style": "charming", "accent": "Standard", "gender": "male", "language": "it", "description": "A charming adult male athletic student''s voice in Italian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7H3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Arrogant Princess
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0V', 'Italian_ArrogantPrincess', 'system_voice_library', 'library', 'minimax', 'Arrogant Princess', 'A passionate and arrogant young adult princess''s voice in Italian.', '{"age": "young_adult", "style": "passionate", "accent": "Standard", "gender": "female", "language": "it", "description": "A passionate and arrogant young adult princess''s voice in Italian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7H4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Whisper Belle
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0W', 'Japanese_Whisper_Belle', 'system_voice_library', 'library', 'minimax', 'Whisper Belle', 'A breathy, adult female whisper voice in Japanese, perfect for ASMR.', '{"age": "adult", "style": "breathy,asmr", "accent": "Standard", "gender": "female", "language": "ja", "description": "A breathy, adult female whisper voice in Japanese, perfect for ASMR."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7H5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Intellectual Senior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0X', 'Japanese_IntellectualSenior', 'system_voice_library', 'library', 'minimax', 'Intellectual Senior', 'A mature and intellectual young adult male voice in Japanese, sounding older than his age.', '{"age": "young_adult", "style": "mature", "accent": "Standard", "gender": "male", "language": "ja", "description": "A mature and intellectual young adult male voice in Japanese, sounding older than his age."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRD5YAPD84R9HQNR7H6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Decisive Princess
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0Y', 'Japanese_DecisivePrincess', 'system_voice_library', 'library', 'minimax', 'Decisive Princess', 'A firm and decisive adult princess''s voice in Japanese.', '{"age": "adult", "style": "firm", "accent": "Standard", "gender": "female", "language": "ja", "description": "A firm and decisive adult princess''s voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687K.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Loyal Knight
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y0Z', 'Japanese_LoyalKnight', 'system_voice_library', 'library', 'minimax', 'Loyal Knight', 'A youthful and loyal adult male knight''s voice in Japanese.', '{"age": "adult", "style": "youthful", "accent": "Standard", "gender": "male", "language": "ja", "description": "A youthful and loyal adult male knight''s voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687M.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Dominant Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y10', 'Japanese_DominantMan', 'system_voice_library', 'library', 'minimax', 'Dominant Man', 'A mature and dominant middle-aged male voice in Japanese.', '{"age": "middle_aged", "style": "mature", "accent": "Standard", "gender": "male", "language": "ja", "description": "A mature and dominant middle-aged male voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687N.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Serious Commander
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y11', 'Japanese_SeriousCommander', 'system_voice_library', 'library', 'minimax', 'Serious Commander', 'A serious and reliable adult male commander''s voice in Japanese.', '{"age": "adult", "style": "reliable", "accent": "Standard", "gender": "male", "language": "ja", "description": "A serious and reliable adult male commander''s voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687P.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cold Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y12', 'Japanese_ColdQueen', 'system_voice_library', 'library', 'minimax', 'Cold Queen', 'A distant and cold adult queen''s voice in Japanese.', '{"age": "adult", "style": "distant", "accent": "Standard", "gender": "female", "language": "ja", "description": "A distant and cold adult queen''s voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687Q.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Dependable Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC48DFNMZA70WC06Y13', 'Japanese_DependableWoman', 'system_voice_library', 'library', 'minimax', 'Dependable Woman', 'A steady and dependable adult female voice in Japanese.', '{"age": "adult", "style": "steady", "accent": "Standard", "gender": "female", "language": "ja", "description": "A steady and dependable adult female voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687R.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Butler
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5P', 'Japanese_GentleButler', 'system_voice_library', 'library', 'minimax', 'Gentle Butler', 'A charming and gentle adult male butler''s voice in Japanese.', '{"age": "adult", "style": "charming", "accent": "Standard", "gender": "male", "language": "ja", "description": "A charming and gentle adult male butler''s voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687S.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5Q', 'Japanese_KindLady', 'system_voice_library', 'library', 'minimax', 'Kind Lady', 'A charming and kind adult female voice in Japanese.', '{"age": "adult", "style": "charming", "accent": "Standard", "gender": "female", "language": "ja", "description": "A charming and kind adult female voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687T.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5R', 'Japanese_CalmLady', 'system_voice_library', 'library', 'minimax', 'Calm Lady', 'A calm and charming adult female voice in Japanese.', '{"age": "adult", "style": "charming", "accent": "Standard", "gender": "female", "language": "ja", "description": "A calm and charming adult female voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687V.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Optimistic Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5S', 'Japanese_OptimisticYouth', 'system_voice_library', 'library', 'minimax', 'Optimistic Youth', 'A cheerful and optimistic adult male youth''s voice in Japanese.', '{"age": "adult", "style": "cheerful", "accent": "Standard", "gender": "male", "language": "ja", "description": "A cheerful and optimistic adult male youth''s voice in Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687W.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Generous Izakaya Owner
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5T', 'Japanese_GenerousIzakayaOwner', 'system_voice_library', 'library', 'minimax', 'Generous Izakaya Owner', 'A playful and generous middle-aged male izakaya owner''s voice in Standard Japanese.', '{"age": "middle_aged", "style": "playful", "accent": "Standard", "gender": "male", "language": "ja", "description": "A playful and generous middle-aged male izakaya owner''s voice in Standard Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687X.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sporty Student
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5V', 'Japanese_SportyStudent', 'system_voice_library', 'library', 'minimax', 'Sporty Student', 'An inviting and sporty adult male student''s voice in Standard Japanese.', '{"age": "adult", "style": "inviting", "accent": "Standard", "gender": "male", "language": "ja", "description": "An inviting and sporty adult male student''s voice in Standard Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687Y.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Innocent Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5W', 'Japanese_InnocentBoy', 'system_voice_library', 'library', 'minimax', 'Innocent Boy', 'An inviting and innocent adult male voice in Standard Japanese.', '{"age": "adult", "style": "inviting", "accent": "Standard", "gender": "male", "language": "ja", "description": "An inviting and innocent adult male voice in Standard Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0687Z.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Graceful Maiden
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5X', 'Japanese_GracefulMaiden', 'system_voice_library', 'library', 'minimax', 'Graceful Maiden', 'A sweet and graceful adult maiden''s voice in Standard Japanese.', '{"age": "adult", "style": "sweet", "accent": "Standard", "gender": "female", "language": "ja", "description": "A sweet and graceful adult maiden''s voice in Standard Japanese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06880.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Powerful Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5Y', 'Korean_PowerfulGirl', 'system_voice_library', 'library', 'minimax', 'Powerful Girl', 'A powerful adult female voice with a rural Korean accent.', '{"age": "adult", "style": "rural", "accent": "Standard", "gender": "female", "language": "ko", "description": "A powerful adult female voice with a rural Korean accent."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06881.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bossy Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG5Z', 'Korean_BossyMan', 'system_voice_library', 'library', 'minimax', 'Bossy Man', 'An innocent and ethereal adult female voice in Standard Korean.', '{"age": "adult", "style": "innocent_and_ethereal", "accent": "Standard", "gender": "female", "language": "ko", "description": "An innocent and ethereal adult female voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06882.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sweet Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG60', 'Korean_SweetGirl', 'system_voice_library', 'library', 'minimax', 'Sweet Girl', 'A soothing and gentle middle-aged female voice in Standard Korean, sweet and calming.', '{"age": "middle_aged", "style": "soothing_and_gentle", "accent": "Standard", "gender": "female", "language": "ko", "description": "A soothing and gentle middle-aged female voice in Standard Korean, sweet and calming."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06883.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cheerful Boyfriend
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG61', 'Korean_CheerfulBoyfriend', 'system_voice_library', 'library', 'minimax', 'Cheerful Boyfriend', 'A sharp and intense middle-aged male voice in Standard Korean.', '{"age": "middle_aged", "style": "sharp_and_intense", "accent": "Standard", "gender": "male", "language": "ko", "description": "A sharp and intense middle-aged male voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06884.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Enchanting Sister
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG62', 'Korean_EnchantingSister', 'system_voice_library', 'library', 'minimax', 'Enchanting Sister', 'A desirable and charming young adult "enchanting sister" voice in Standard Korean.', '{"age": "young_adult", "style": "desirable_and_charming", "accent": "Standard", "gender": "female", "language": "ko", "description": "A desirable and charming young adult \"enchanting sister\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06885.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Shy Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG63', 'Korean_ShyGirl', 'system_voice_library', 'library', 'minimax', 'Shy Girl', 'A timid and introverted young adult female voice in Standard Korean.', '{"age": "young_adult", "style": "timid_and_introverted", "accent": "Standard", "gender": "female", "language": "ko", "description": "A timid and introverted young adult female voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06886.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Sister
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG64', 'Korean_ReliableSister', 'system_voice_library', 'library', 'minimax', 'Reliable Sister', 'A powerful and authoritative middle-aged "reliable sister" voice in Standard Korean.', '{"age": "middle_aged", "style": "powerful_and_authoritative", "accent": "Standard", "gender": "female", "language": "ko", "description": "A powerful and authoritative middle-aged \"reliable sister\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06887.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Strict Boss
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG65', 'Korean_StrictBoss', 'system_voice_library', 'library', 'minimax', 'Strict Boss', 'A stern middle-aged male boss''s voice in Standard Korean.', '{"age": "middle_aged", "style": "stern", "accent": "Standard", "gender": "male", "language": "ko", "description": "A stern middle-aged male boss''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06888.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sassy Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG66', 'Korean_SassyGirl', 'system_voice_library', 'library', 'minimax', 'Sassy Girl', 'A Sassy female youth voice in Standard Korean.', '{"age": "youth", "style": "sassy", "accent": "Standard", "gender": "female", "language": "ko", "description": "A Sassy female youth voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB06889.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Childhood Friend Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG67', 'Korean_ChildhoodFriendGirl', 'system_voice_library', 'library', 'minimax', 'Childhood Friend Girl', 'A polite and reserved young adult female "childhood friend" voice in Standard Korean.', '{"age": "young_adult", "style": "polite_and_reserved", "accent": "Standard", "gender": "female", "language": "ko", "description": "A polite and reserved young adult female \"childhood friend\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0688A.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Playboy Charmer
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG68', 'Korean_PlayboyCharmer', 'system_voice_library', 'library', 'minimax', 'Playboy Charmer', 'A seductive young adult male "playboy charmer" voice in Standard Korean.', '{"age": "young_adult", "style": "seductive", "accent": "Standard", "gender": "male", "language": "ko", "description": "A seductive young adult male \"playboy charmer\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0688B.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Elegant Princess
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG69', 'Korean_ElegantPrincess', 'system_voice_library', 'library', 'minimax', 'Elegant Princess', 'A graceful and refined adult princess voice in Standard Korean.', '{"age": "adult", "style": "graceful_and_refined", "accent": "Standard", "gender": "female", "language": "ko", "description": "A graceful and refined adult princess voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0688C.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Brave Female Warrior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG6A', 'Korean_BraveFemaleWarrior', 'system_voice_library', 'library', 'minimax', 'Brave Female Warrior', 'A resolute young adult brave female warrior''s voice in Standard Korean.', '{"age": "young_adult", "style": "resolute", "accent": "Standard", "gender": "female", "language": "ko", "description": "A resolute young adult brave female warrior''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0688D.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Brave Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG6B', 'Korean_BraveYouth', 'system_voice_library', 'library', 'minimax', 'Brave Youth', 'A powerful young adult brave male youth''s voice in Standard Korean.', '{"age": "young_adult", "style": "powerful", "accent": "Standard", "gender": "male", "language": "ko", "description": "A powerful young adult brave male youth''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0688E.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG6C', 'Korean_CalmLady', 'system_voice_library', 'library', 'minimax', 'Calm Lady', 'A resilient and determined young adult female voice in Standard Korean.', '{"age": "young_adult", "style": "resilient_and_determined", "accent": "Standard", "gender": "female", "language": "ko", "description": "A resilient and determined young adult female voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0688F.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Enthusiastic Teen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC5A5SFC2WM2SQ2WG6D', 'Korean_EnthusiasticTeen', 'system_voice_library', 'library', 'minimax', 'Enthusiastic Teen', 'A passionate and lively young adult male teen''s voice in Standard Korean.', '{"age": "young_adult", "style": "passionate_and_lively", "accent": "Standard", "gender": "male", "language": "ko", "description": "A passionate and lively young adult male teen''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JREZ1E0DMXJQZB0688G.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Soothing Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZP', 'Korean_SoothingLady', 'system_voice_library', 'library', 'minimax', 'Soothing Lady', 'An alluring and soothing middle-aged female voice in Standard Korean.', '{"age": "middle_aged", "style": "alluring", "accent": "Standard", "gender": "female", "language": "ko", "description": "An alluring and soothing middle-aged female voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Intellectual Senior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZQ', 'Korean_IntellectualSenior', 'system_voice_library', 'library', 'minimax', 'Intellectual Senior', 'A magnetic and intellectual young adult male voice with a senior quality in Standard Korean.', '{"age": "young_adult", "style": "magnetic", "accent": "Standard", "gender": "male", "language": "ko", "description": "A magnetic and intellectual young adult male voice with a senior quality in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Lonely Warrior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZR', 'Korean_LonelyWarrior', 'system_voice_library', 'library', 'minimax', 'Lonely Warrior', 'A youthful and daring adult male "lonely warrior" voice in Standard Korean.', '{"age": "adult", "style": "youthful_and_daring", "accent": "Standard", "gender": "male", "language": "ko", "description": "A youthful and daring adult male \"lonely warrior\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Mature Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZS', 'Korean_MatureLady', 'system_voice_library', 'library', 'minimax', 'Mature Lady', 'A refined and elegant mature middle-aged lady''s voice in Standard Korean.', '{"age": "middle_aged", "style": "refined_and_elegant", "accent": "Standard", "gender": "female", "language": "ko", "description": "A refined and elegant mature middle-aged lady''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Innocent Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZT', 'Korean_InnocentBoy', 'system_voice_library', 'library', 'minimax', 'Innocent Boy', 'A naive and pure young adult male "innocent boy" voice in Standard Korean.', '{"age": "young_adult", "style": "naive_and_pure", "accent": "Standard", "gender": "male", "language": "ko", "description": "A naive and pure young adult male \"innocent boy\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Charming Sister
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZV', 'Korean_CharmingSister', 'system_voice_library', 'library', 'minimax', 'Charming Sister', 'A seductive middle-aged "charming sister" voice in Standard Korean.', '{"age": "middle_aged", "style": "seductive", "accent": "Standard", "gender": "female", "language": "ko", "description": "A seductive middle-aged \"charming sister\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Athletic Student
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZW', 'Korean_AthleticStudent', 'system_voice_library', 'library', 'minimax', 'Athletic Student', 'An energetic young adult male athletic student''s voice in Standard Korean.', '{"age": "young_adult", "style": "energetic", "accent": "Standard", "gender": "male", "language": "ko", "description": "An energetic young adult male athletic student''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Brave Adventurer
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZX', 'Korean_BraveAdventurer', 'system_voice_library', 'library', 'minimax', 'Brave Adventurer', 'A playful and adventurous adult female brave adventurer''s voice in Standard Korean.', '{"age": "adult", "style": "playful_and_adventurous", "accent": "Standard", "gender": "female", "language": "ko", "description": "A playful and adventurous adult female brave adventurer''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Gentleman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZY', 'Korean_CalmGentleman', 'system_voice_library', 'library', 'minimax', 'Calm Gentleman', 'A composed and calm middle-aged gentleman''s voice in Standard Korean.', '{"age": "middle_aged", "style": "composed", "accent": "Standard", "gender": "male", "language": "ko", "description": "A composed and calm middle-aged gentleman''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Elf
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYXZZ', 'Korean_WiseElf', 'system_voice_library', 'library', 'minimax', 'Wise Elf', 'A sweet and ethereal young adult female "wise elf" voice in Standard Korean.', '{"age": "young_adult", "style": "sweet_and_ethereal", "accent": "Standard", "gender": "female", "language": "ko", "description": "A sweet and ethereal young adult female \"wise elf\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cheerful Cool Junior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY00', 'Korean_CheerfulCoolJunior', 'system_voice_library', 'library', 'minimax', 'Cheerful Cool Junior', 'An energetic and spirited adult male "cheerful cool junior" voice in Standard Korean.', '{"age": "adult", "style": "energetic_and_spirited", "accent": "Standard", "gender": "male", "language": "ko", "description": "An energetic and spirited adult male \"cheerful cool junior\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Decisive Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY01', 'Korean_DecisiveQueen', 'system_voice_library', 'library', 'minimax', 'Decisive Queen', 'A sweet yet resolute young adult decisive queen''s voice in Standard Korean.', '{"age": "young_adult", "style": "sweet_and_resolute", "accent": "Standard", "gender": "female", "language": "ko", "description": "A sweet yet resolute young adult decisive queen''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cold Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY02', 'Korean_ColdYoungMan', 'system_voice_library', 'library', 'minimax', 'Cold Young Man', 'A cold and composed adult male voice in Standard Korean.', '{"age": "adult", "style": "cold_and_composed", "accent": "Standard", "gender": "male", "language": "ko", "description": "A cold and composed adult male voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Mysterious Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY03', 'Korean_MysteriousGirl', 'system_voice_library', 'library', 'minimax', 'Mysterious Girl', 'An energetic and lively female youth voice for a mysterious character in Standard Korean.', '{"age": "youth", "style": "energetic_and_lively", "accent": "Standard", "gender": "female", "language": "ko", "description": "An energetic and lively female youth voice for a mysterious character in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRF3PNACAE2YV8GXYBZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Quirky Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY04', 'Korean_QuirkyGirl', 'system_voice_library', 'library', 'minimax', 'Quirky Girl', 'An adorable and quirky female youth voice in Standard Korean.', '{"age": "youth", "style": "adorable_and_quirky", "accent": "Standard", "gender": "female", "language": "ko", "description": "An adorable and quirky female youth voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5R3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Considerate Senior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY05', 'Korean_ConsiderateSenior', 'system_voice_library', 'library', 'minimax', 'Considerate Senior', 'A gentle and mature young adult male "considerate senior" voice in Standard Korean.', '{"age": "young_adult", "style": "gentle_and_mature", "accent": "Standard", "gender": "male", "language": "ko", "description": "A gentle and mature young adult male \"considerate senior\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5R4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cheerful Little Sister
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY06', 'Korean_CheerfulLittleSister', 'system_voice_library', 'library', 'minimax', 'Cheerful Little Sister', 'An energetic and lively adult female "cheerful little sister" voice in Standard Korean.', '{"age": "adult", "style": "energetic_and_lively", "accent": "Standard", "gender": "female", "language": "ko", "description": "An energetic and lively adult female \"cheerful little sister\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5R5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Dominant Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY07', 'Korean_DominantMan', 'system_voice_library', 'library', 'minimax', 'Dominant Man', 'A mature and authoritative dominant adult male voice in Standard Korean.', '{"age": "adult", "style": "mature_and_authoritative", "accent": "Standard", "gender": "male", "language": "ko", "description": "A mature and authoritative dominant adult male voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5R6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Airheaded Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY08', 'Korean_AirheadedGirl', 'system_voice_library', 'library', 'minimax', 'Airheaded Girl', 'A cool and composed adult female voice, suitable for an "airheaded" character in Standard Korean.', '{"age": "adult", "style": "cool_and_composed", "accent": "Standard", "gender": "female", "language": "ko", "description": "A cool and composed adult female voice, suitable for an \"airheaded\" character in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5R7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY09', 'Korean_ReliableYouth', 'system_voice_library', 'library', 'minimax', 'Reliable Youth', 'A gentle and considerate young adult reliable male youth''s voice in Standard Korean.', '{"age": "young_adult", "style": "gentle_and_considerate", "accent": "Standard", "gender": "male", "language": "ko", "description": "A gentle and considerate young adult reliable male youth''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5R8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Big Sister
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY0A', 'Korean_FriendlyBigSister', 'system_voice_library', 'library', 'minimax', 'Friendly Big Sister', 'A charismatic and alluring middle-aged "friendly big sister" voice in Standard Korean.', '{"age": "middle_aged", "style": "charismatic_and_alluring", "accent": "Standard", "gender": "female", "language": "ko", "description": "A charismatic and alluring middle-aged \"friendly big sister\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5R9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Boss
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY0B', 'Korean_GentleBoss', 'system_voice_library', 'library', 'minimax', 'Gentle Boss', 'A regal and refined middle-aged male "gentle boss" voice in Standard Korean.', '{"age": "middle_aged", "style": "regal_and_refined", "accent": "Standard", "gender": "male", "language": "ko", "description": "A regal and refined middle-aged male \"gentle boss\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5RA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cold Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC6V5G6S9WZZTJNYY0C', 'Korean_ColdGirl', 'system_voice_library', 'library', 'minimax', 'Cold Girl', 'An aloof and cold adult female voice in Standard Korean.', '{"age": "adult", "style": "aloof", "accent": "Standard", "gender": "female", "language": "ko", "description": "An aloof and cold adult female voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5RB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Haughty Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ388', 'Korean_HaughtyLady', 'system_voice_library', 'library', 'minimax', 'Haughty Lady', 'A cold and distant young adult haughty lady''s voice in Standard Korean.', '{"age": "young_adult", "style": "cold_and_distant", "accent": "Standard", "gender": "female", "language": "ko", "description": "A cold and distant young adult haughty lady''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5RC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Charming Elder Sister
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ389', 'Korean_CharmingElderSister', 'system_voice_library', 'library', 'minimax', 'Charming Elder Sister', 'A playful and mischievous middle-aged "charming elder sister" voice in Standard Korean.', '{"age": "middle_aged", "style": "playful_and_mischievous", "accent": "Standard", "gender": "female", "language": "ko", "description": "A playful and mischievous middle-aged \"charming elder sister\" voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5RD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Intellectual Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38A', 'Korean_IntellectualMan', 'system_voice_library', 'library', 'minimax', 'Intellectual Man', 'A combative middle-aged intellectual male voice in Standard Korean.', '{"age": "middle_aged", "style": "combative", "accent": "Standard", "gender": "male", "language": "ko", "description": "A combative middle-aged intellectual male voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5RE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Caring Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38B', 'Korean_CaringWoman', 'system_voice_library', 'library', 'minimax', 'Caring Woman', 'A lively and vibrant young adult caring woman''s voice in Standard Korean.', '{"age": "young_adult", "style": "lively_and_vibrant", "accent": "Standard", "gender": "female", "language": "ko", "description": "A lively and vibrant young adult caring woman''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5RF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Teacher
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38C', 'Korean_WiseTeacher', 'system_voice_library', 'library', 'minimax', 'Wise Teacher', 'A sagacious and wise middle-aged male teacher''s voice in Standard Korean.', '{"age": "middle_aged", "style": "sagacious", "accent": "Standard", "gender": "male", "language": "ko", "description": "A sagacious and wise middle-aged male teacher''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5RG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Boss
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38D', 'Korean_ConfidentBoss', 'system_voice_library', 'library', 'minimax', 'Confident Boss', 'A deep and commanding middle-aged confident boss''s voice in Standard Korean.', '{"age": "middle_aged", "style": "deep_and_commanding", "accent": "Standard", "gender": "male", "language": "ko", "description": "A deep and commanding middle-aged confident boss''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRGD0NSPPRV7B90S5RH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Athletic Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38E', 'Korean_AthleticGirl', 'system_voice_library', 'library', 'minimax', 'Athletic Girl', 'A robust and athletic female youth''s voice in Standard Korean.', '{"age": "youth", "style": "robust_and_athletic", "accent": "Standard", "gender": "female", "language": "ko", "description": "A robust and athletic female youth''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Possessive Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38F', 'Korean_PossessiveMan', 'system_voice_library', 'library', 'minimax', 'Possessive Man', 'A powerful and authoritative middle-aged possessive man''s voice in Standard Korean.', '{"age": "middle_aged", "style": "powerful_and_authoritative", "accent": "Standard", "gender": "male", "language": "ko", "description": "A powerful and authoritative middle-aged possessive man''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38G', 'Korean_GentleWoman', 'system_voice_library', 'library', 'minimax', 'Gentle Woman', 'A strong-willed yet gentle young adult female voice in Standard Korean.', '{"age": "young_adult", "style": "strong-willed", "accent": "Standard", "gender": "female", "language": "ko", "description": "A strong-willed yet gentle young adult female voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cocky Guy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38H', 'Korean_CockyGuy', 'system_voice_library', 'library', 'minimax', 'Cocky Guy', 'A playful and mischievous young adult cocky guy''s voice in Standard Korean.', '{"age": "young_adult", "style": "playful_and_mischievous", "accent": "Standard", "gender": "male", "language": "ko", "description": "A playful and mischievous young adult cocky guy''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Thoughtful Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38J', 'Korean_ThoughtfulWoman', 'system_voice_library', 'library', 'minimax', 'Thoughtful Woman', 'A mature and contemplative young adult thoughtful woman''s voice in Standard Korean.', '{"age": "young_adult", "style": "mature_and_contemplative", "accent": "Standard", "gender": "female", "language": "ko", "description": "A mature and contemplative young adult thoughtful woman''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Optimistic Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38K', 'Korean_OptimisticYouth', 'system_voice_library', 'library', 'minimax', 'Optimistic Youth', 'A cheerful and optimistic young adult male youth''s voice in Standard Korean.', '{"age": "young_adult", "style": "cheerful", "accent": "Standard", "gender": "male", "language": "ko", "description": "A cheerful and optimistic young adult male youth''s voice in Standard Korean."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Anxious Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38M', 'Portuguese_AnxiousMan', 'system_voice_library', 'library', 'minimax', 'Anxious Man', 'An enthusiastic middle-aged male voice in Portuguese, conveying a sense of anxiety.', '{"age": "middle_aged", "style": "enthusiastic", "accent": "Standard", "gender": "male", "language": "pt", "description": "An enthusiastic middle-aged male voice in Portuguese, conveying a sense of anxiety."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Mature Researcher
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38N', 'Portuguese_Matureresearcher', 'system_voice_library', 'library', 'minimax', 'Mature Researcher', 'A comforting and mature middle-aged male researcher''s voice in Portuguese.', '{"age": "middle_aged", "style": "comforting", "accent": "Standard", "gender": "male", "language": "pt", "description": "A comforting and mature middle-aged male researcher''s voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Optimistic youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38P', 'Portuguese_Optimisticyouth', 'system_voice_library', 'library', 'minimax', 'Optimistic youth', 'A high-energy and optimistic young adult male voice in Portuguese.', '{"age": "young_adult", "style": "high_energy", "accent": "Standard", "gender": "male", "language": "pt", "description": "A high-energy and optimistic young adult male voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cute Elf
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC70XM9R7BNTR1ZZ38Q', 'Portuguese_CuteElf', 'system_voice_library', 'library', 'minimax', 'Cute Elf', 'A lively and cute young adult female elf''s voice in Portuguese.', '{"age": "young_adult", "style": "lively", "accent": "Standard", "gender": "female", "language": "pt", "description": "A lively and cute young adult female elf''s voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Energetic Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGE', 'Portuguese_EnergeticGirl', 'system_voice_library', 'library', 'minimax', 'Energetic Girl', 'A cheerful and energetic young adult female voice in Portuguese.', '{"age": "young_adult", "style": "cheerful", "accent": "Standard", "gender": "female", "language": "pt", "description": "A cheerful and energetic young adult female voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Funny Guy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGF', 'Portuguese_FunnyGuy', 'system_voice_library', 'library', 'minimax', 'Funny Guy', 'A mischievous young adult "funny guy" voice in Portuguese.', '{"age": "young_adult", "style": "mischievous", "accent": "Standard", "gender": "male", "language": "pt", "description": "A mischievous young adult \"funny guy\" voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Nutty Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGG', 'Portuguese_Nuttylady', 'system_voice_library', 'library', 'minimax', 'Nutty Lady', 'A wacky middle-aged "nutty lady" voice in Portuguese.', '{"age": "middle_aged", "style": "wacky", "accent": "Standard", "gender": "female", "language": "pt", "description": "A wacky middle-aged \"nutty lady\" voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Deep-toned Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGH', 'Portuguese_Deep-tonedMan', 'system_voice_library', 'library', 'minimax', 'Deep-toned Man', 'A charismatic, deep-toned middle-aged male voice in Portuguese.', '{"age": "middle_aged", "style": "charismatic", "accent": "Standard", "gender": "male", "language": "pt", "description": "A charismatic, deep-toned middle-aged male voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SQZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sentimental Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGJ', 'Portuguese_SentimentalLady', 'system_voice_library', 'library', 'minimax', 'Sentimental Lady', 'An elegant and sentimental young adult female voice in Portuguese.', '{"age": "young_adult", "style": "elegant", "accent": "Standard", "gender": "female", "language": "pt", "description": "An elegant and sentimental young adult female voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bossy Leader
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGK', 'Portuguese_BossyLeader', 'system_voice_library', 'library', 'minimax', 'Bossy Leader', 'A calm and formal adult male bossy leader''s voice in Portuguese.', '{"age": "adult", "style": "calm_and_formal", "accent": "Standard", "gender": "male", "language": "pt", "description": "A calm and formal adult male bossy leader''s voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGM', 'Portuguese_Wiselady', 'system_voice_library', 'library', 'minimax', 'Wise lady', 'A smooth and wise middle-aged lady''s voice in Portuguese.', '{"age": "middle_aged", "style": "smooth", "accent": "Standard", "gender": "female", "language": "pt", "description": "A smooth and wise middle-aged lady''s voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Strong-willed Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGN', 'Portuguese_Strong-WilledBoy', 'system_voice_library', 'library', 'minimax', 'Strong-willed Boy', 'A mature and strong-willed young adult male voice in Portuguese.', '{"age": "young_adult", "style": "mature", "accent": "Standard", "gender": "male", "language": "pt", "description": "A mature and strong-willed young adult male voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Deep-voiced Gentleman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGP', 'Portuguese_Deep-VoicedGentleman', 'system_voice_library', 'library', 'minimax', 'Deep-voiced Gentleman', 'A deep-voiced adult gentleman in Portuguese.', '{"age": "adult", "style": "deep-voiced", "accent": "Standard", "gender": "male", "language": "pt", "description": "A deep-voiced adult gentleman in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Upset Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGQ', 'Portuguese_UpsetGirl', 'system_voice_library', 'library', 'minimax', 'Upset Girl', 'A sad young adult female voice in Portuguese, conveying upset emotions.', '{"age": "young_adult", "style": "sad", "accent": "Standard", "gender": "female", "language": "pt", "description": "A sad young adult female voice in Portuguese, conveying upset emotions."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Passionate Warrior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGR', 'Portuguese_PassionateWarrior', 'system_voice_library', 'library', 'minimax', 'Passionate Warrior', 'An energetic and passionate young adult male warrior''s voice in Portuguese.', '{"age": "young_adult", "style": "energetic", "accent": "Standard", "gender": "male", "language": "pt", "description": "An energetic and passionate young adult male warrior''s voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Anime Character
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGS', 'Portuguese_AnimeCharacter', 'system_voice_library', 'library', 'minimax', 'Anime Character', 'An animated middle-aged female voice in Portuguese, suitable for anime characters.', '{"age": "middle_aged", "style": "animated", "accent": "Standard", "gender": "female", "language": "pt", "description": "An animated middle-aged female voice in Portuguese, suitable for anime characters."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGT', 'Portuguese_ConfidentWoman', 'system_voice_library', 'library', 'minimax', 'Confident Woman', 'A clear and firm young adult confident woman''s voice in Portuguese.', '{"age": "young_adult", "style": "clear_and_firm", "accent": "Standard", "gender": "female", "language": "pt", "description": "A clear and firm young adult confident woman''s voice in Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Angry Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGV', 'Portuguese_AngryMan', 'system_voice_library', 'library', 'minimax', 'Angry Man', 'A serious young adult male voice in Portuguese, conveying anger.', '{"age": "young_adult", "style": "serious", "accent": "Standard", "gender": "male", "language": "pt", "description": "A serious young adult male voice in Portuguese, conveying anger."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SR9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Captivating Storyteller
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGW', 'Portuguese_CaptivatingStoryteller', 'system_voice_library', 'library', 'minimax', 'Captivating Storyteller', 'A captivating middle-aged male narrator''s voice in Portuguese, ideal for storytelling.', '{"age": "middle_aged", "style": "narrator", "accent": "Standard", "gender": "male", "language": "pt", "description": "A captivating middle-aged male narrator''s voice in Portuguese, ideal for storytelling."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SRA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Godfather
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGX', 'Portuguese_Godfather', 'system_voice_library', 'library', 'minimax', 'Godfather', 'A serious middle-aged male godfather voice in Standard Portuguese, conveying authority.', '{"age": "middle_aged", "style": "serious", "accent": "Standard", "gender": "male", "language": "pt", "description": "A serious middle-aged male godfather voice in Standard Portuguese, conveying authority."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SRB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reserved Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGY', 'Portuguese_ReservedYoungMan', 'system_voice_library', 'library', 'minimax', 'Reserved Young Man', 'A cold and calm reserved young adult male voice in Standard Portuguese.', '{"age": "young_adult", "style": "cold_and_calm", "accent": "Standard", "gender": "male", "language": "pt", "description": "A cold and calm reserved young adult male voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SRC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Smart Young Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEGZ', 'Portuguese_SmartYoungGirl', 'system_voice_library', 'library', 'minimax', 'Smart Young Girl', 'An intelligent young female girl''s voice in Standard Portuguese, sharp and clear.', '{"age": "youth", "style": "inteligente", "accent": "Standard", "gender": "female", "language": "pt", "description": "An intelligent young female girl''s voice in Standard Portuguese, sharp and clear."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SRD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind-hearted Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC8RR6VQK3JAVN6YEH0', 'Portuguese_Kind-heartedGirl', 'system_voice_library', 'library', 'minimax', 'Kind-hearted Girl', 'A calm and kind-hearted young adult female voice in Standard Portuguese.', '{"age": "young_adult", "style": "calm", "accent": "Standard", "gender": "female", "language": "pt", "description": "A calm and kind-hearted young adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRH93PVPBE160CQ2SRE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Pompous lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GGZ', 'Portuguese_Pompouslady', 'system_voice_library', 'library', 'minimax', 'Pompous lady', 'A pompous young adult female cartoon-style voice in Standard Portuguese, full of personality.', '{"age": "young_adult", "style": "cartoon", "accent": "Standard", "gender": "female", "language": "pt", "description": "A pompous young adult female cartoon-style voice in Standard Portuguese, full of personality."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55Q5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Grinch
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH0', 'Portuguese_Grinch', 'system_voice_library', 'library', 'minimax', 'Grinch', 'A cunning adult male Grinch-like voice in Standard Portuguese, mischievous and sly.', '{"age": "adult", "style": "cunning", "accent": "Standard", "gender": "male", "language": "pt", "description": "A cunning adult male Grinch-like voice in Standard Portuguese, mischievous and sly."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55Q6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Debator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH1', 'Portuguese_Debator', 'system_voice_library', 'library', 'minimax', 'Debator', 'A tough middle-aged male debater''s voice in Standard Portuguese, strong and assertive.', '{"age": "middle_aged", "style": "tough", "accent": "Standard", "gender": "male", "language": "pt", "description": "A tough middle-aged male debater''s voice in Standard Portuguese, strong and assertive."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55Q7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sweet Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH2', 'Portuguese_SweetGirl', 'system_voice_library', 'library', 'minimax', 'Sweet Girl', 'An adorable and sweet young adult female voice in Standard Portuguese.', '{"age": "young_adult", "style": "adorable", "accent": "Standard", "gender": "female", "language": "pt", "description": "An adorable and sweet young adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55Q8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Attractive Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH3', 'Portuguese_AttractiveGirl', 'system_voice_library', 'library', 'minimax', 'Attractive Girl', 'An alluring and attractive adult female voice in Standard Portuguese.', '{"age": "adult", "style": "alluring", "accent": "Standard", "gender": "female", "language": "pt", "description": "An alluring and attractive adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55Q9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Thoughtful Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH4', 'Portuguese_ThoughtfulMan', 'system_voice_library', 'library', 'minimax', 'Thoughtful Man', 'A gentle and thoughtful young adult male voice in Standard Portuguese.', '{"age": "young_adult", "style": "gentle", "accent": "Standard", "gender": "male", "language": "pt", "description": "A gentle and thoughtful young adult male voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Playful Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH5', 'Portuguese_PlayfulGirl', 'system_voice_library', 'library', 'minimax', 'Playful Girl', 'A cutesy and playful female youth voice in Standard Portuguese.', '{"age": "youth", "style": "cutesy", "accent": "Standard", "gender": "female", "language": "pt", "description": "A cutesy and playful female youth voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gorgeous Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH6', 'Portuguese_GorgeousLady', 'system_voice_library', 'library', 'minimax', 'Gorgeous Lady', 'A playful and gorgeous adult female voice in Standard Portuguese, exuding confidence.', '{"age": "adult", "style": "playful", "accent": "Standard", "gender": "female", "language": "pt", "description": "A playful and gorgeous adult female voice in Standard Portuguese, exuding confidence."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Lovely Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH7', 'Portuguese_LovelyLady', 'system_voice_library', 'library', 'minimax', 'Lovely Lady', 'A charismatic and lovely adult female voice in Standard Portuguese.', '{"age": "adult", "style": "charismatic", "accent": "Standard", "gender": "female", "language": "pt", "description": "A charismatic and lovely adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Serene Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH8', 'Portuguese_SereneWoman', 'system_voice_library', 'library', 'minimax', 'Serene Woman', 'A calm and serene young adult female voice in Standard Portuguese, peaceful and composed.', '{"age": "young_adult", "style": "calm", "accent": "Standard", "gender": "female", "language": "pt", "description": "A calm and serene young adult female voice in Standard Portuguese, peaceful and composed."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sad Teen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GH9', 'Portuguese_SadTeen', 'system_voice_library', 'library', 'minimax', 'Sad Teen', 'A frustrated and sad male teen''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "frustrated", "accent": "Standard", "gender": "male", "language": "pt", "description": "A frustrated and sad male teen''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Mature Partner
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHA', 'Portuguese_MaturePartner', 'system_voice_library', 'library', 'minimax', 'Mature Partner', 'A mature middle-aged male partner''s voice in Standard Portuguese, dependable and warm.', '{"age": "middle_aged", "style": "mature", "accent": "Standard", "gender": "male", "language": "pt", "description": "A mature middle-aged male partner''s voice in Standard Portuguese, dependable and warm."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Comedian
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHB', 'Portuguese_Comedian', 'system_voice_library', 'library', 'minimax', 'Comedian', 'A humorous young adult male comedian''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "humor", "accent": "Standard", "gender": "male", "language": "pt", "description": "A humorous young adult male comedian''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Naughty Schoolgirl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHC', 'Portuguese_NaughtySchoolgirl', 'system_voice_library', 'library', 'minimax', 'Naughty Schoolgirl', 'An inviting and naughty young adult female schoolgirl''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "inviting", "accent": "Standard", "gender": "female", "language": "pt", "description": "An inviting and naughty young adult female schoolgirl''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHD', 'Portuguese_Narrator', 'system_voice_library', 'library', 'minimax', 'Narrator', 'A middle-aged female narrator''s voice in Standard Portuguese, perfect for storytelling.', '{"age": "middle_aged", "style": "storytelling", "accent": "Standard", "gender": "female", "language": "pt", "description": "A middle-aged female narrator''s voice in Standard Portuguese, perfect for storytelling."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Tough Boss
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHE', 'Portuguese_ToughBoss', 'system_voice_library', 'library', 'minimax', 'Tough Boss', 'A mature and tough middle-aged female boss''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "mature", "accent": "Standard", "gender": "female", "language": "pt", "description": "A mature and tough middle-aged female boss''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRJ1ZAJHWD4Q32F55QM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Fussy hostess
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHF', 'Portuguese_Fussyhostess', 'system_voice_library', 'library', 'minimax', 'Fussy hostess', 'An intense and fussy middle-aged female hostess''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "intense", "accent": "Standard", "gender": "female", "language": "pt", "description": "An intense and fussy middle-aged female hostess''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JP4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Dramatist
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHG', 'Portuguese_Dramatist', 'system_voice_library', 'library', 'minimax', 'Dramatist', 'A quirky middle-aged male dramatist''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "quirky", "accent": "Standard", "gender": "male", "language": "pt", "description": "A quirky middle-aged male dramatist''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JP5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Steady Mentor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHH', 'Portuguese_Steadymentor', 'system_voice_library', 'library', 'minimax', 'Steady Mentor', 'An arrogant yet steady young adult male mentor''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "arrogant", "accent": "Standard", "gender": "male", "language": "pt", "description": "An arrogant yet steady young adult male mentor''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JP6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Jovial Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHJ', 'Portuguese_Jovialman', 'system_voice_library', 'library', 'minimax', 'Jovial Man', 'A jovial and laughing middle-aged male voice in Standard Portuguese.', '{"age": "middle_aged", "style": "laugh", "accent": "Standard", "gender": "male", "language": "pt", "description": "A jovial and laughing middle-aged male voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JP7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Charming Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHK', 'Portuguese_CharmingQueen', 'system_voice_library', 'library', 'minimax', 'Charming Queen', 'A bewitching and charming adult queen''s voice in Standard Portuguese.', '{"age": "adult", "style": "bewitching", "accent": "Standard", "gender": "female", "language": "pt", "description": "A bewitching and charming adult queen''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JP8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Santa Claus
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHM', 'Portuguese_SantaClaus', 'system_voice_library', 'library', 'minimax', 'Santa Claus', 'A joyful middle-aged male Santa Claus voice in Standard Portuguese, full of holiday cheer.', '{"age": "middle_aged", "style": "joyful", "accent": "Standard", "gender": "male", "language": "pt", "description": "A joyful middle-aged male Santa Claus voice in Standard Portuguese, full of holiday cheer."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JP9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Rudolph
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHN', 'Portuguese_Rudolph', 'system_voice_library', 'library', 'minimax', 'Rudolph', 'A naive young adult female voice in the style of Rudolph in Standard Portuguese.', '{"age": "young_adult", "style": "naive", "accent": "Standard", "gender": "female", "language": "pt", "description": "A naive young adult female voice in the style of Rudolph in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Arnold
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHP', 'Portuguese_Arnold', 'system_voice_library', 'library', 'minimax', 'Arnold', 'A steady adult male voice in the style of Arnold in Standard Portuguese, strong and firm.', '{"age": "adult", "style": "steady", "accent": "Standard", "gender": "male", "language": "pt", "description": "A steady adult male voice in the style of Arnold in Standard Portuguese, strong and firm."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Charming Santa
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHQ', 'Portuguese_CharmingSanta', 'system_voice_library', 'library', 'minimax', 'Charming Santa', 'An attractive and charming middle-aged male Santa voice in Standard Portuguese.', '{"age": "middle_aged", "style": "attractive", "accent": "Standard", "gender": "male", "language": "pt", "description": "An attractive and charming middle-aged male Santa voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Ghost
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHR', 'Portuguese_Ghost', 'system_voice_library', 'library', 'minimax', 'Ghost', 'A sensual adult male ghost''s voice in Standard Portuguese, mysterious and alluring.', '{"age": "adult", "style": "sensual", "accent": "Standard", "gender": "male", "language": "pt", "description": "A sensual adult male ghost''s voice in Standard Portuguese, mysterious and alluring."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Humorous Elder
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHS', 'Portuguese_HumorousElder', 'system_voice_library', 'library', 'minimax', 'Humorous Elder', 'A wacky and humorous middle-aged male elder''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "wacky", "accent": "Standard", "gender": "male", "language": "pt", "description": "A wacky and humorous middle-aged male elder''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Leader
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHT', 'Portuguese_CalmLeader', 'system_voice_library', 'library', 'minimax', 'Calm Leader', 'A composed and calm middle-aged male leader''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "composed", "accent": "Standard", "gender": "male", "language": "pt", "description": "A composed and calm middle-aged male leader''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Teacher
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTC91MKW5CF0SA0V7GHV', 'Portuguese_GentleTeacher', 'system_voice_library', 'library', 'minimax', 'Gentle Teacher', 'A mild and gentle adult male teacher''s voice in Standard Portuguese.', '{"age": "adult", "style": "mild", "accent": "Standard", "gender": "male", "language": "pt", "description": "A mild and gentle adult male teacher''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Energetic Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFE9', 'Portuguese_EnergeticBoy', 'system_voice_library', 'library', 'minimax', 'Energetic Boy', 'A cheerful and energetic young adult male voice in Standard Portuguese.', '{"age": "young_adult", "style": "cheerful", "accent": "Standard", "gender": "male", "language": "pt", "description": "A cheerful and energetic young adult male voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEA', 'Portuguese_ReliableMan', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A steady and reliable adult male voice in Standard Portuguese.', '{"age": "adult", "style": "steady", "accent": "Standard", "gender": "male", "language": "pt", "description": "A steady and reliable adult male voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Serene Elder
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEB', 'Portuguese_SereneElder', 'system_voice_library', 'library', 'minimax', 'Serene Elder', 'A reflective and serene middle-aged male elder''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "reflective", "accent": "Standard", "gender": "male", "language": "pt", "description": "A reflective and serene middle-aged male elder''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Grim Reaper
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEC', 'Portuguese_GrimReaper', 'system_voice_library', 'library', 'minimax', 'Grim Reaper', 'A sinister adult male Grim Reaper''s voice in Standard Portuguese, dark and ominous.', '{"age": "adult", "style": "sinister", "accent": "Standard", "gender": "male", "language": "pt", "description": "A sinister adult male Grim Reaper''s voice in Standard Portuguese, dark and ominous."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Assertive Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFED', 'Portuguese_AssertiveQueen', 'system_voice_library', 'library', 'minimax', 'Assertive Queen', 'A firm and assertive young adult queen''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "firm", "accent": "Standard", "gender": "female", "language": "pt", "description": "A firm and assertive young adult queen''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRKN78YZ93BDGHE7JPN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Whimsical Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEE', 'Portuguese_WhimsicalGirl', 'system_voice_library', 'library', 'minimax', 'Whimsical Girl', 'A lovely and whimsical young adult female voice in Standard Portuguese.', '{"age": "young_adult", "style": "lovely", "accent": "Standard", "gender": "female", "language": "pt", "description": "A lovely and whimsical young adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QD4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Stressed Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEF', 'Portuguese_StressedLady', 'system_voice_library', 'library', 'minimax', 'Stressed Lady', 'An unsure and stressed middle-aged lady''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "unsure", "accent": "Standard", "gender": "female", "language": "pt", "description": "An unsure and stressed middle-aged lady''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QD5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Neighbor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEG', 'Portuguese_FriendlyNeighbor', 'system_voice_library', 'library', 'minimax', 'Friendly Neighbor', 'An energetic and friendly young adult female neighbor''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "energetic", "accent": "Standard", "gender": "female", "language": "pt", "description": "An energetic and friendly young adult female neighbor''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QD6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Caring Girlfriend
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEH', 'Portuguese_CaringGirlfriend', 'system_voice_library', 'library', 'minimax', 'Caring Girlfriend', 'A dreamy middle-aged female caring girlfriend''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "dreamy", "accent": "Standard", "gender": "female", "language": "pt", "description": "A dreamy middle-aged female caring girlfriend''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QD7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Powerful Soldier
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEJ', 'Portuguese_PowerfulSoldier', 'system_voice_library', 'library', 'minimax', 'Powerful Soldier', 'A youthful and bold young adult male powerful soldier''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "youthful_and_bold", "accent": "Standard", "gender": "male", "language": "pt", "description": "A youthful and bold young adult male powerful soldier''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QD8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Fascinating Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEK', 'Portuguese_FascinatingBoy', 'system_voice_library', 'library', 'minimax', 'Fascinating Boy', 'An approachable and fascinating young adult male voice in Standard Portuguese.', '{"age": "young_adult", "style": "approachable", "accent": "Standard", "gender": "male", "language": "pt", "description": "An approachable and fascinating young adult male voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QD9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Romantic Husband
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEM', 'Portuguese_RomanticHusband', 'system_voice_library', 'library', 'minimax', 'Romantic Husband', 'An emotional middle-aged male romantic husband''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "emotional", "accent": "Standard", "gender": "male", "language": "pt", "description": "An emotional middle-aged male romantic husband''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Strict Boss
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEN', 'Portuguese_StrictBoss', 'system_voice_library', 'library', 'minimax', 'Strict Boss', 'A robotic and strict young adult female boss''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "robotic", "accent": "Standard", "gender": "female", "language": "pt", "description": "A robotic and strict young adult female boss''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Inspiring Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEP', 'Portuguese_InspiringLady', 'system_voice_library', 'library', 'minimax', 'Inspiring Lady', 'A commanding and inspiring young adult female voice in Standard Portuguese.', '{"age": "young_adult", "style": "commanding", "accent": "Standard", "gender": "female", "language": "pt", "description": "A commanding and inspiring young adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Playful Spirit
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFEQ', 'Portuguese_PlayfulSpirit', 'system_voice_library', 'library', 'minimax', 'Playful Spirit', 'An animated and playful young adult female spirit''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "animated", "accent": "Standard", "gender": "female", "language": "pt", "description": "An animated and playful young adult female spirit''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Elegant Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCAY999VG35NQY1DFER', 'Portuguese_ElegantGirl', 'system_voice_library', 'library', 'minimax', 'Elegant Girl', 'A dramatic and elegant young adult female voice in Standard Portuguese.', '{"age": "young_adult", "style": "dramatic", "accent": "Standard", "gender": "female", "language": "pt", "description": "A dramatic and elegant young adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Compelling Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC569S', 'Portuguese_CompellingGirl', 'system_voice_library', 'library', 'minimax', 'Compelling Girl', 'A persuasive and compelling young adult female voice in Standard Portuguese.', '{"age": "young_adult", "style": "persuasive", "accent": "Standard", "gender": "female", "language": "pt", "description": "A persuasive and compelling young adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Powerful Veteran
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC569T', 'Portuguese_PowerfulVeteran', 'system_voice_library', 'library', 'minimax', 'Powerful Veteran', 'A strong and powerful middle-aged male veteran''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "strong", "accent": "Standard", "gender": "male", "language": "pt", "description": "A strong and powerful middle-aged male veteran''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sensible Manager
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC569V', 'Portuguese_SensibleManager', 'system_voice_library', 'library', 'minimax', 'Sensible Manager', 'A charismatic and sensible middle-aged male manager''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "charismatic", "accent": "Standard", "gender": "male", "language": "pt", "description": "A charismatic and sensible middle-aged male manager''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDH.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Thoughtful Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC569W', 'Portuguese_ThoughtfulLady', 'system_voice_library', 'library', 'minimax', 'Thoughtful Lady', 'A worried and thoughtful middle-aged lady''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "worried", "accent": "Standard", "gender": "female", "language": "pt", "description": "A worried and thoughtful middle-aged lady''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDJ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Theatrical Actor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC569X', 'Portuguese_TheatricalActor', 'system_voice_library', 'library', 'minimax', 'Theatrical Actor', 'An animated middle-aged male theatrical actor''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "animated", "accent": "Standard", "gender": "male", "language": "pt", "description": "An animated middle-aged male theatrical actor''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDK.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Fragile Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC569Y', 'Portuguese_FragileBoy', 'system_voice_library', 'library', 'minimax', 'Fragile Boy', 'A gentle and fragile young adult male voice in Standard Portuguese.', '{"age": "young_adult", "style": "gentle", "accent": "Standard", "gender": "male", "language": "pt", "description": "A gentle and fragile young adult male voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDM.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Chatty Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC569Z', 'Portuguese_ChattyGirl', 'system_voice_library', 'library', 'minimax', 'Chatty Girl', 'A conversational and chatty young adult female voice in Standard Portuguese.', '{"age": "young_adult", "style": "conversational", "accent": "Standard", "gender": "female", "language": "pt", "description": "A conversational and chatty young adult female voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDN.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Conscientious Instructor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A0', 'Portuguese_Conscientiousinstructor', 'system_voice_library', 'library', 'minimax', 'Conscientious Instructor', 'A youthful and conscientious young adult female instructor''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "youthful", "accent": "Standard", "gender": "female", "language": "pt", "description": "A youthful and conscientious young adult female instructor''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Rational Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A1', 'Portuguese_RationalMan', 'system_voice_library', 'library', 'minimax', 'Rational Man', 'A thoughtful and rational adult male voice in Standard Portuguese.', '{"age": "adult", "style": "thoughtful", "accent": "Standard", "gender": "male", "language": "pt", "description": "A thoughtful and rational adult male voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Scholar
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A2', 'Portuguese_WiseScholar', 'system_voice_library', 'library', 'minimax', 'Wise Scholar', 'A conversational young adult male wise scholar''s voice in Standard Portuguese.', '{"age": "young_adult", "style": "conversational", "accent": "Standard", "gender": "male", "language": "pt", "description": "A conversational young adult male wise scholar''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Frank Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A3', 'Portuguese_FrankLady', 'system_voice_library', 'library', 'minimax', 'Frank Lady', 'An agitated and frank middle-aged lady''s voice in Standard Portuguese.', '{"age": "middle_aged", "style": "agitated", "accent": "Standard", "gender": "female", "language": "pt", "description": "An agitated and frank middle-aged lady''s voice in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Determined Manager
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A4', 'Portuguese_DeterminedManager', 'system_voice_library', 'library', 'minimax', 'Determined Manager', 'A middle-aged female manager''s voice with attitude and determination in Standard Portuguese.', '{"age": "middle_aged", "style": "attitude", "accent": "Standard", "gender": "female", "language": "pt", "description": "A middle-aged female manager''s voice with attitude and determination in Standard Portuguese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Charming Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A5', 'Portuguese_CharmingLady', 'system_voice_library', 'library', 'minimax', 'Charming Lady', 'Charming Lady - Charming', '{"age": "adult", "style": "charming", "accent": "Standard", "gender": "female", "language": "pt"}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRMM7YMQCN7PKMG5QDV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Handsome Childhood Friend
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A6', 'Russian_HandsomeChildhoodFriend', 'system_voice_library', 'library', 'minimax', 'Handsome Childhood Friend', 'An aggressive female youth''s voice for a handsome childhood friend character in Standard Russian.', '{"age": "youth", "style": "aggressive", "accent": "Standard", "gender": "female", "language": "ru", "description": "An aggressive female youth''s voice for a handsome childhood friend character in Standard Russian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6E.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bright Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A7', 'Russian_BrightHeroine', 'system_voice_library', 'library', 'minimax', 'Bright Queen', 'An arrogant and bright adult queen''s voice in Standard Russian.', '{"age": "adult", "style": "arrogant", "accent": "Standard", "gender": "female", "language": "ru", "description": "An arrogant and bright adult queen''s voice in Standard Russian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6F.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Ambitious Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A8', 'Russian_AmbitiousWoman', 'system_voice_library', 'library', 'minimax', 'Ambitious Woman', 'A demanding and ambitious adult woman''s voice in Standard Russian.', '{"age": "adult", "style": "demanding", "accent": "Standard", "gender": "female", "language": "ru", "description": "A demanding and ambitious adult woman''s voice in Standard Russian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6G.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56A9', 'Russian_ReliableMan', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A steady and reliable middle-aged man''s voice in Standard Russian.', '{"age": "middle_aged", "style": "steady", "accent": "Standard", "gender": "male", "language": "ru", "description": "A steady and reliable middle-aged man''s voice in Standard Russian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6H.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Crazy Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56AA', 'Russian_CrazyQueen', 'system_voice_library', 'library', 'minimax', 'Crazy Girl', 'An energetic adult female "crazy girl" voice in Standard Russian, wild and unpredictable.', '{"age": "adult", "style": "energetic", "accent": "Standard", "gender": "female", "language": "ru", "description": "An energetic adult female \"crazy girl\" voice in Standard Russian, wild and unpredictable."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6J.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Pessimistic Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCBXFDJ5MYAXDKC56AB', 'Russian_PessimisticGirl', 'system_voice_library', 'library', 'minimax', 'Pessimistic Girl', 'A compassionate adult female "pessimistic girl" voice in Standard Russian.', '{"age": "adult", "style": "compassionate", "accent": "Standard", "gender": "female", "language": "ru", "description": "A compassionate adult female \"pessimistic girl\" voice in Standard Russian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6K.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Attractive Guy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB1R', 'Russian_AttractiveGuy', 'system_voice_library', 'library', 'minimax', 'Attractive Guy', 'A deep-voiced and attractive adult guy''s voice in Standard Russian.', '{"age": "adult", "style": "deep-voiced", "accent": "Standard", "gender": "male", "language": "ru", "description": "A deep-voiced and attractive adult guy''s voice in Standard Russian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6M.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bad-tempered Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB1S', 'Russian_Bad-temperedBoy', 'system_voice_library', 'library', 'minimax', 'Bad-tempered Boy', 'A charming adult male "bad-tempered boy" voice in Standard Russian.', '{"age": "adult", "style": "charming", "accent": "Standard", "gender": "male", "language": "ru", "description": "A charming adult male \"bad-tempered boy\" voice in Standard Russian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6N.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Neighbor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB1T', 'Spanish_FriendlyNeighbor', 'system_voice_library', 'library', 'minimax', 'Friendly Neighbor', 'An energetic young adult female friendly neighbor''s voice in Standard Spanish.', '{"age": "young_adult", "style": "advertisement", "accent": "Standard", "gender": "female", "language": "es", "description": "An energetic young adult female friendly neighbor''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6P.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Fragile Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB1V', 'Spanish_FragileBoy', 'system_voice_library', 'library', 'minimax', 'Fragile Boy', 'A gentle young adult fragile boy''s voice in Standard Spanish.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A gentle young adult fragile boy''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6Q.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Upset Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB1W', 'Spanish_UpsetGirl', 'system_voice_library', 'library', 'minimax', 'Upset Girl', 'A sad young adult upset girl''s voice in Standard Spanish.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "es", "description": "A sad young adult upset girl''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6R.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Soft-spoken Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB1X', 'Spanish_Soft-spokenGirl', 'system_voice_library', 'library', 'minimax', 'Soft-spoken Girl', 'A serene and soft-spoken young adult girl''s voice in Standard Spanish.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "es", "description": "A serene and soft-spoken young adult girl''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6S.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Charming Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB1Y', 'Spanish_CharmingQueen', 'system_voice_library', 'library', 'minimax', 'Charming Queen', 'A bewitching and charming adult queen''s voice in Standard Spanish.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "es", "description": "A bewitching and charming adult queen''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6T.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Nutty Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB1Z', 'Spanish_Nuttylady', 'system_voice_library', 'library', 'minimax', 'Nutty Lady', 'A wacky middle-aged female voice in Standard Spanish.', '{"age": "middle_aged", "style": "characters", "accent": "Standard", "gender": "female", "language": "es", "description": "A wacky middle-aged female voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6V.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Elegant Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB20', 'Spanish_ElegantGirl', 'system_voice_library', 'library', 'minimax', 'Elegant Girl', 'A dramatic and elegant young adult female voice in Standard Spanish.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "es", "description": "A dramatic and elegant young adult female voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6W.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Fascinating Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB21', 'Spanish_FascinatingBoy', 'system_voice_library', 'library', 'minimax', 'Fascinating Boy', 'An approachable and fascinating young adult male voice in Standard Spanish.', '{"age": "young_adult", "style": "advertisement", "accent": "Standard", "gender": "male", "language": "es", "description": "An approachable and fascinating young adult male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6X.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Funny Guy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB22', 'Spanish_FunnyGuy', 'system_voice_library', 'library', 'minimax', 'Funny Guy', 'A mischievous young adult male "funny guy" voice in Standard Spanish.', '{"age": "young_adult", "style": "social_media", "accent": "Standard", "gender": "male", "language": "es", "description": "A mischievous young adult male \"funny guy\" voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6Y.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Playful Spirit
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB23', 'Spanish_PlayfulSpirit', 'system_voice_library', 'library', 'minimax', 'Playful Spirit', 'An animated and playful young adult female spirit''s voice in Standard Spanish.', '{"age": "young_adult", "style": "advertisement", "accent": "Standard", "gender": "female", "language": "es", "description": "An animated and playful young adult female spirit''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRNFV90MD1CYFVNEX6Z.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Theatrical Actor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB24', 'Spanish_TheatricalActor', 'system_voice_library', 'library', 'minimax', 'Theatrical Actor', 'A robust and theatrical middle-aged male actor''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "advertisement", "accent": "Standard", "gender": "male", "language": "es", "description": "A robust and theatrical middle-aged male actor''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G950S.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Serene Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB25', 'Spanish_SereneWoman', 'system_voice_library', 'library', 'minimax', 'Serene Woman', 'A soothing and serene young adult female voice in Standard Spanish.', '{"age": "young_adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "A soothing and serene young adult female voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G950T.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Mature Partner
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB26', 'Spanish_MaturePartner', 'system_voice_library', 'library', 'minimax', 'Mature Partner', 'A warm and mature middle-aged male partner''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "es", "description": "A warm and mature middle-aged male partner''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G950V.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Captivating Storyteller
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB27', 'Spanish_CaptivatingStoryteller', 'system_voice_library', 'library', 'minimax', 'Captivating Storyteller', 'A captivating middle-aged male narrator''s voice in Standard Spanish, perfect for storytelling.', '{"age": "middle_aged", "style": "informative", "accent": "Standard", "gender": "male", "language": "es", "description": "A captivating middle-aged male narrator''s voice in Standard Spanish, perfect for storytelling."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G950W.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB28', 'Spanish_Narrator', 'system_voice_library', 'library', 'minimax', 'Narrator', 'A middle-aged female narrator''s voice in Standard Spanish, ideal for storytelling.', '{"age": "middle_aged", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "A middle-aged female narrator''s voice in Standard Spanish, ideal for storytelling."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G950X.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Scholar
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB29', 'Spanish_WiseScholar', 'system_voice_library', 'library', 'minimax', 'Wise Scholar', 'A conversational young adult male wise scholar''s voice in Standard Spanish.', '{"age": "young_adult", "style": "informative", "accent": "Standard", "gender": "male", "language": "es", "description": "A conversational young adult male wise scholar''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G950Y.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind-hearted Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB2A', 'Spanish_Kind-heartedGirl', 'system_voice_library', 'library', 'minimax', 'Kind-hearted Girl', 'A bright and kind-hearted young adult female voice in Standard Spanish.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "female", "language": "es", "description": "A bright and kind-hearted young adult female voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G950Z.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Determined Manager
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB2B', 'Spanish_DeterminedManager', 'system_voice_library', 'library', 'minimax', 'Determined Manager', 'A businesslike and determined middle-aged female manager''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "A businesslike and determined middle-aged female manager''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G9510.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Bossy Leader
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB2C', 'Spanish_BossyLeader', 'system_voice_library', 'library', 'minimax', 'Bossy Leader', 'A businesslike and bossy adult male leader''s voice in Standard Spanish.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A businesslike and bossy adult male leader''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G9511.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reserved Young Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB2D', 'Spanish_ReservedYoungMan', 'system_voice_library', 'library', 'minimax', 'Reserved Young Man', 'A tranquil and reserved young adult male voice in Standard Spanish.', '{"age": "young_adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "es", "description": "A tranquil and reserved young adult male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G9512.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCCG1TDRR06AC87BB2E', 'Spanish_ConfidentWoman', 'system_voice_library', 'library', 'minimax', 'Confident Woman', 'A clear and firm young adult confident woman''s voice in Standard Spanish.', '{"age": "young_adult", "style": "informative", "accent": "Standard", "gender": "female", "language": "es", "description": "A clear and firm young adult confident woman''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRPYTFHFNEH0E9G9513.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Thoughtful Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWQ', 'Spanish_ThoughtfulMan', 'system_voice_library', 'library', 'minimax', 'Thoughtful Man', 'A sober and thoughtful young adult male voice in Standard Spanish.', '{"age": "young_adult", "style": "informative", "accent": "Standard", "gender": "male", "language": "es", "description": "A sober and thoughtful young adult male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X01.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Strong-willed Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWR', 'Spanish_Strong-WilledBoy', 'system_voice_library', 'library', 'minimax', 'Strong-willed Boy', 'A mature and strong-willed adult male voice in Standard Spanish.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A mature and strong-willed adult male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X02.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sophisticated Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWS', 'Spanish_SophisticatedLady', 'system_voice_library', 'library', 'minimax', 'Sophisticated Lady', 'A refined and sophisticated adult lady''s voice in Standard Spanish.', '{"age": "adult", "style": "informative", "accent": "Standard", "gender": "female", "language": "es", "description": "A refined and sophisticated adult lady''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X03.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Rational Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWT', 'Spanish_RationalMan', 'system_voice_library', 'library', 'minimax', 'Rational Man', 'A thoughtful and rational adult male voice in Standard Spanish.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "es", "description": "A thoughtful and rational adult male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X04.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Anime Character
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWV', 'Spanish_AnimeCharacter', 'system_voice_library', 'library', 'minimax', 'Anime Character', 'An animated middle-aged female voice in Standard Spanish, suitable for anime characters.', '{"age": "middle_aged", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "An animated middle-aged female voice in Standard Spanish, suitable for anime characters."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X05.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Deep-toned Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWW', 'Spanish_Deep-tonedMan', 'system_voice_library', 'library', 'minimax', 'Deep-toned Man', 'A charismatic, deep-toned middle-aged male voice in Standard Spanish.', '{"age": "middle_aged", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A charismatic, deep-toned middle-aged male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X06.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Fussy hostess
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWX', 'Spanish_Fussyhostess', 'system_voice_library', 'library', 'minimax', 'Fussy hostess', 'An intense and fussy middle-aged female hostess''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "advertisement", "accent": "Standard", "gender": "female", "language": "es", "description": "An intense and fussy middle-aged female hostess''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X07.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sincere Teen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWY', 'Spanish_SincereTeen', 'system_voice_library', 'library', 'minimax', 'Sincere Teen', 'A heartfelt and sincere male teen''s voice in Standard Spanish.', '{"age": "young_adult", "style": "social_media", "accent": "Standard", "gender": "male", "language": "es", "description": "A heartfelt and sincere male teen''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X08.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Frank Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAWZ', 'Spanish_FrankLady', 'system_voice_library', 'library', 'minimax', 'Frank Lady', 'An agitated and frank adult lady''s voice in Standard Spanish.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "female", "language": "es", "description": "An agitated and frank adult lady''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X09.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Comedian
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAX0', 'Spanish_Comedian', 'system_voice_library', 'library', 'minimax', 'Comedian', 'A humorous young adult male comedian''s voice in Standard Spanish.', '{"age": "young_adult", "style": "advertisement", "accent": "Standard", "gender": "male", "language": "es", "description": "A humorous young adult male comedian''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0A.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Debator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAX1', 'Spanish_Debator', 'system_voice_library', 'library', 'minimax', 'Debator', 'A tough middle-aged male debater''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A tough middle-aged male debater''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0B.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Tough Boss
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAX2', 'Spanish_ToughBoss', 'system_voice_library', 'library', 'minimax', 'Tough Boss', 'A mature and tough middle-aged female boss''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "A mature and tough middle-aged female boss''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0C.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAX3', 'Spanish_Wiselady', 'system_voice_library', 'library', 'minimax', 'Wise Lady', 'A neutral and wise middle-aged lady''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "A neutral and wise middle-aged lady''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0D.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Steady Mentor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAX4', 'Spanish_Steadymentor', 'system_voice_library', 'library', 'minimax', 'Steady Mentor', 'An arrogant yet steady young adult male mentor''s voice in Standard Spanish.', '{"age": "young_adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "es", "description": "An arrogant yet steady young adult male mentor''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0E.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Jovial Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAX5', 'Spanish_Jovialman', 'system_voice_library', 'library', 'minimax', 'Jovial Man', 'A gravelly and jovial senior male voice in Standard Spanish.', '{"age": "senior", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A gravelly and jovial senior male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0F.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Santa Claus
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAX6', 'Spanish_SantaClaus', 'system_voice_library', 'library', 'minimax', 'Santa Claus', 'A joyful senior male Santa Claus voice in Standard Spanish.', '{"age": "senior", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A joyful senior male Santa Claus voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0G.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Rudolph
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCDHKP1CT8ZR84WKAX7', 'Spanish_Rudolph', 'system_voice_library', 'library', 'minimax', 'Rudolph', 'A naive young adult male voice in the style of Rudolph in Standard Spanish.', '{"age": "young_adult", "style": "informative", "accent": "Standard", "gender": "male", "language": "es", "description": "A naive young adult male voice in the style of Rudolph in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0H.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Intonate Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQB', 'Spanish_Intonategirl', 'system_voice_library', 'library', 'minimax', 'Intonate Girl', 'A versatile young adult female voice in Standard Spanish.', '{"age": "young_adult", "style": "advertisement", "accent": "Standard", "gender": "female", "language": "es", "description": "A versatile young adult female voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0J.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Arnold
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQC', 'Spanish_Arnold', 'system_voice_library', 'library', 'minimax', 'Arnold', 'A steady adult male voice in the style of Arnold in Standard Spanish.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "es", "description": "A steady adult male voice in the style of Arnold in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0K.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Ghost
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQD', 'Spanish_Ghost', 'system_voice_library', 'library', 'minimax', 'Ghost', 'A raspy adult male ghost''s voice in Standard Spanish.', '{"age": "adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A raspy adult male ghost''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0M.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Humorous Elder
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQE', 'Spanish_HumorousElder', 'system_voice_library', 'library', 'minimax', 'Humorous Elder', 'An eccentric and humorous senior male elder''s voice in Standard Spanish.', '{"age": "senior", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "An eccentric and humorous senior male elder''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0N.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Energetic Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQF', 'Spanish_EnergeticBoy', 'system_voice_library', 'library', 'minimax', 'Energetic Boy', 'A cheerful and energetic young adult male voice in Standard Spanish.', '{"age": "young_adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "es", "description": "A cheerful and energetic young adult male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0P.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Whimsical Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQG', 'Spanish_WhimsicalGirl', 'system_voice_library', 'library', 'minimax', 'Whimsical Girl', 'A witty and whimsical young adult female voice in Standard Spanish.', '{"age": "young_adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "A witty and whimsical young adult female voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0Q.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Strict Boss
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQH', 'Spanish_StrictBoss', 'system_voice_library', 'library', 'minimax', 'Strict Boss', 'A commanding and strict young adult female boss''s voice in Standard Spanish.', '{"age": "young_adult", "style": "advertisement", "accent": "Standard", "gender": "female", "language": "es", "description": "A commanding and strict young adult female boss''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0R.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQJ', 'Spanish_ReliableMan', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A steady and reliable adult male voice in Standard Spanish.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "es", "description": "A steady and reliable adult male voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0S.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Serene Elder
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQK', 'Spanish_SereneElder', 'system_voice_library', 'library', 'minimax', 'Serene Elder', 'A reflective and serene senior male elder''s voice in Standard Spanish.', '{"age": "senior", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "A reflective and serene senior male elder''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0T.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Angry Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQM', 'Spanish_AngryMan', 'system_voice_library', 'library', 'minimax', 'Angry Man', 'An intense young adult male voice in Standard Spanish, conveying anger.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "An intense young adult male voice in Standard Spanish, conveying anger."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0V.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Assertive Queen
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQN', 'Spanish_AssertiveQueen', 'system_voice_library', 'library', 'minimax', 'Assertive Queen', 'A firm and assertive young adult queen''s voice in Standard Spanish.', '{"age": "young_adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "A firm and assertive young adult queen''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0W.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Caring Girlfriend
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQP', 'Spanish_CaringGirlfriend', 'system_voice_library', 'library', 'minimax', 'Caring Girlfriend', 'A dreamy adult female caring girlfriend''s voice in Standard Spanish.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "es", "description": "A dreamy adult female caring girlfriend''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRQG8PA1938SKQ63X0X.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Powerful Soldier
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQQ', 'Spanish_PowerfulSoldier', 'system_voice_library', 'library', 'minimax', 'Powerful Soldier', 'A youthful and bold young adult male powerful soldier''s voice in Standard Spanish.', '{"age": "young_adult", "style": "informative", "accent": "Standard", "gender": "male", "language": "es", "description": "A youthful and bold young adult male powerful soldier''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNYX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Passionate Warrior
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQR', 'Spanish_PassionateWarrior', 'system_voice_library', 'library', 'minimax', 'Passionate Warrior', 'An energetic and passionate young adult male warrior''s voice in Standard Spanish.', '{"age": "young_adult", "style": "characters", "accent": "Standard", "gender": "male", "language": "es", "description": "An energetic and passionate young adult male warrior''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNYY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Chatty Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQS', 'Spanish_ChattyGirl', 'system_voice_library', 'library', 'minimax', 'Chatty Girl', 'A conversational and chatty young adult female voice in Standard Spanish.', '{"age": "young_adult", "style": "social_media", "accent": "Standard", "gender": "female", "language": "es", "description": "A conversational and chatty young adult female voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNYZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Romantic Husband
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQT', 'Spanish_RomanticHusband', 'system_voice_library', 'library', 'minimax', 'Romantic Husband', 'An emotional middle-aged male romantic husband''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "informative", "accent": "Standard", "gender": "male", "language": "es", "description": "An emotional middle-aged male romantic husband''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Compelling Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQV', 'Spanish_CompellingGirl', 'system_voice_library', 'library', 'minimax', 'Compelling Girl', 'A persuasive and compelling young adult female voice in Standard Spanish.', '{"age": "young_adult", "style": "informative", "accent": "Standard", "gender": "female", "language": "es", "description": "A persuasive and compelling young adult female voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Powerful Veteran
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQW', 'Spanish_PowerfulVeteran', 'system_voice_library', 'library', 'minimax', 'Powerful Veteran', 'A strong and powerful middle-aged male veteran''s voice in Standard Spanish.', '{"age": "middle_aged", "style": "informative", "accent": "Standard", "gender": "male", "language": "es", "description": "A strong and powerful middle-aged male veteran''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sensible Manager
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQX', 'Spanish_SensibleManager', 'system_voice_library', 'library', 'minimax', 'Sensible Manager', 'A charismatic and sensible adult male manager''s voice in Standard Spanish.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "male", "language": "es", "description": "A charismatic and sensible adult male manager''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Thoughtful Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCED5FTQZ1NQ0HWYTQY', 'Spanish_ThoughtfulLady', 'system_voice_library', 'library', 'minimax', 'Thoughtful Lady', 'A worried and thoughtful adult lady''s voice in Standard Spanish.', '{"age": "adult", "style": "informative", "accent": "Standard", "gender": "female", "language": "es", "description": "A worried and thoughtful adult lady''s voice in Standard Spanish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J95', 'Turkish_CalmWoman', 'system_voice_library', 'library', 'minimax', 'Calm Woman', 'A calm adult female Turkish voice, ideal for audiobooks.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "tr", "description": "A calm adult female Turkish voice, ideal for audiobooks."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Trustworthy man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J96', 'Turkish_Trustworthyman', 'system_voice_library', 'library', 'minimax', 'Trustworthy man', 'A resonant and trustworthy adult male Turkish voice.', '{"age": "adult", "style": "resonate", "accent": "Standard", "gender": "male", "language": "tr", "description": "A resonant and trustworthy adult male Turkish voice."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J97', 'Ukrainian_CalmWoman', 'system_voice_library', 'library', 'minimax', 'Calm Woman', 'A calm adult female Ukrainian voice, ideal for audiobooks.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "ukrainian", "description": "A calm adult female Ukrainian voice, ideal for audiobooks."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Scholar
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J98', 'Ukrainian_WiseScholar', 'system_voice_library', 'library', 'minimax', 'Wise Scholar', 'A conversational young adult male wise scholar''s voice in Ukrainian.', '{"age": "young_adult", "style": "conversational", "accent": "Standard", "gender": "male", "language": "ukrainian", "description": "A conversational young adult male wise scholar''s voice in Ukrainian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Serene Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J99', 'Vietnamese_Serene_Man', 'system_voice_library', 'library', 'minimax', 'Serene Man', 'A serene adult male Vietnamese voice, perfect for podcasts.', '{"age": "adult", "style": "podcast", "gender": "male", "language": "vi", "description": "A serene adult male Vietnamese voice, perfect for podcasts."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZ9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9A', 'Vietnamese_female_4_v1', 'system_voice_library', 'library', 'minimax', 'Confident Woman', 'A confident adult female Vietnamese voice, suitable for broadcast.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "female", "language": "vi", "description": "A confident adult female Vietnamese voice, suitable for broadcast."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9B', 'Vietnamese_male_1_v2', 'system_voice_library', 'library', 'minimax', 'Friendly Man', 'A tranquil and friendly adult male Vietnamese voice.', '{"age": "adult", "style": "tranquil", "accent": "Standard", "gender": "male", "language": "vi", "description": "A tranquil and friendly adult male Vietnamese voice."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRR0V7QKYCQCG4TPNZB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Kind-hearted girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9C', 'Vietnamese_kindhearted_girl', 'system_voice_library', 'library', 'minimax', 'Kind-hearted girl', 'A warm and kind-hearted young adult female voice in Vietnamese.', '{"age": "young_adult", "style": "warim", "accent": "Standard", "gender": "female", "language": "vi", "description": "A warm and kind-hearted young adult female voice in Vietnamese."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SP.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Optimistic girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9D', 'Thai_Optimistic_girl', 'system_voice_library', 'library', 'minimax', 'Optimistic girl', 'A lively and optimistic young adult female voice in Thai.', '{"age": "young_adult", "style": "lively", "gender": "female", "language": "th", "description": "A lively and optimistic young adult female voice in Thai."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SQ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Serene Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9E', 'Thai_male_1_sample8', 'system_voice_library', 'library', 'minimax', 'Serene Man', 'A magnetic and serene adult male voice in Thai.', '{"age": "adult", "style": "magnetic", "accent": "Standard", "gender": "male", "language": "th", "description": "A magnetic and serene adult male voice in Thai."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SR.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Tender Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9F', 'Thai_Tender_Woman', 'system_voice_library', 'library', 'minimax', 'Tender Woman', 'A gentle and tender adult female voice in Thai.', '{"age": "adult", "style": "gentle", "gender": "female", "language": "th", "description": "A gentle and tender adult female voice in Thai."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SS.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9G', 'Thai_male_2_sample2', 'system_voice_library', 'library', 'minimax', 'Friendly Man', 'A lively and friendly adult male voice in Thai.', '{"age": "adult", "style": "lively", "accent": "Standard", "gender": "male", "language": "th", "description": "A lively and friendly adult male voice in Thai."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9ST.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9H', 'Thai_female_1_sample1', 'system_voice_library', 'library', 'minimax', 'Confident Woman', 'A neutral and confident adult female voice in Thai.', '{"age": "adult", "style": "neutral", "accent": "Standard", "gender": "female", "language": "th", "description": "A neutral and confident adult female voice in Thai."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Energetic Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9J', 'Thai_female_2_sample2', 'system_voice_library', 'library', 'minimax', 'Energetic Woman', 'An energetic adult female voice in Thai.', '{"age": "adult", "style": "energetic", "accent": "Standard", "gender": "female", "language": "th", "description": "An energetic adult female voice in Thai."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Male Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9K', 'Polish_male_1_sample4', 'system_voice_library', 'library', 'minimax', 'Male Narrator', 'A mature adult male narrator''s voice in Polish.', '{"age": "adult", "style": "mature", "accent": "Standard", "gender": "male", "language": "pl", "description": "A mature adult male narrator''s voice in Polish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Male Anchor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9M', 'Polish_male_2_sample3', 'system_voice_library', 'library', 'minimax', 'Male Anchor', 'An adult male broadcast anchor''s voice in Polish.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "male", "language": "pl", "description": "An adult male broadcast anchor''s voice in Polish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9N', 'Polish_female_1_sample1', 'system_voice_library', 'library', 'minimax', 'Calm Woman', 'A calm adult female voice in Polish.', '{"age": "adult", "style": "calm", "accent": "Standard", "gender": "female", "language": "pl", "description": "A calm adult female voice in Polish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9SZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Casual Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9P', 'Polish_female_2_sample3', 'system_voice_library', 'library', 'minimax', 'Casual Woman', 'A neutral and casual adult female voice in Polish.', '{"age": "adult", "style": "neutral", "accent": "Standard", "gender": "female", "language": "pl", "description": "A neutral and casual adult female voice in Polish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9T0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9Q', 'Romanian_male_1_sample2', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A neutral and reliable adult male voice in Romanian.', '{"age": "adult", "style": "neutral", "accent": "Standard", "gender": "male", "language": "romanian", "description": "A neutral and reliable adult male voice in Romanian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9T1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Energetic Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9R', 'Romanian_male_2_sample1', 'system_voice_library', 'library', 'minimax', 'Energetic Youth', 'An energetic adult male youth''s voice in Romanian.', '{"age": "adult", "style": "energetic", "accent": "Standard", "gender": "male", "language": "romanian", "description": "An energetic adult male youth''s voice in Romanian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9T2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Optimistic Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCF4CC7ZMM4YPDF4J9S', 'Romanian_female_1_sample4', 'system_voice_library', 'library', 'minimax', 'Optimistic Youth', 'A cheerful and optimistic adult female youth''s voice in Romanian.', '{"age": "adult", "style": "cheerful", "accent": "Standard", "gender": "female", "language": "romanian", "description": "A cheerful and optimistic adult female youth''s voice in Romanian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRSS7CXKMWH4ZMJF9T3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXRY', 'Romanian_female_2_sample1', 'system_voice_library', 'library', 'minimax', 'Gentle Woman', 'A gentle adult female voice in Romanian.', '{"age": "adult", "style": "gentle", "accent": "Standard", "gender": "female", "language": "romanian", "description": "A gentle adult female voice in Romanian."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BPX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXRZ', 'Greek_female_1_sample1', 'system_voice_library', 'library', 'minimax', 'Gentle Lady', 'A gentle adult lady''s voice in Greek.', '{"age": "adult", "style": "gentle", "accent": "Standard", "gender": "female", "language": "greek", "description": "A gentle adult lady''s voice in Greek."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BPY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Thoughtful Mentor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS0', 'greek_male_1a_v1', 'system_voice_library', 'library', 'minimax', 'Thoughtful Mentor', 'An intellectual and thoughtful adult male mentor''s voice in Greek.', '{"age": "adult", "style": "intellectual", "accent": "Standard", "gender": "male", "language": "greek", "description": "An intellectual and thoughtful adult male mentor''s voice in Greek."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BPZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Girl Next Door
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS1', 'Greek_female_2_sample3', 'system_voice_library', 'library', 'minimax', 'Girl Next Door', 'A cheerful young adult "girl next door" voice in Greek.', '{"age": "young_adult", "style": "cheerful", "accent": "Standard", "gender": "female", "language": "greek", "description": "A cheerful young adult \"girl next door\" voice in Greek."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Assured Presenter
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS2', 'czech_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Assured Presenter', 'A serious and assured young adult male presenter''s voice in Czech.', '{"age": "young_adult", "style": "serious", "accent": "Standard", "gender": "male", "language": "czech", "description": "A serious and assured young adult male presenter''s voice in Czech."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Steadfast Narrator
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS3', 'czech_female_5_v7', 'system_voice_library', 'library', 'minimax', 'Steadfast Narrator', 'A steadfast adult female broadcast narrator''s voice in Czech.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "female", "language": "czech", "description": "A steadfast adult female broadcast narrator''s voice in Czech."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ2.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Elegant Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS4', 'czech_female_2_v2', 'system_voice_library', 'library', 'minimax', 'Elegant Lady', 'A graceful and elegant adult lady''s voice in Czech.', '{"age": "adult", "style": "graceful", "accent": "Standard", "gender": "female", "language": "czech", "description": "A graceful and elegant adult lady''s voice in Czech."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ3.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Upbeat Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS5', 'finnish_male_3_v1', 'system_voice_library', 'library', 'minimax', 'Upbeat Man', 'An energetic and upbeat young adult female voice in Finnish.', '{"age": "young_adult", "style": "energetic", "accent": "Standard", "gender": "female", "language": "finnish", "description": "An energetic and upbeat young adult female voice in Finnish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ4.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Assertive Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS6', 'finnish_female_4_v1', 'system_voice_library', 'library', 'minimax', 'Assertive Woman', 'A determined and assertive adult female voice in Finnish.', '{"age": "adult", "style": "determined", "accent": "Standard", "gender": "female", "language": "finnish", "description": "A determined and assertive adult female voice in Finnish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ5.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Boy
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS7', 'finnish_male_1_v2', 'system_voice_library', 'library', 'minimax', 'Friendly Boy', 'A deep and friendly young adult male voice in Finnish.', '{"age": "young_adult", "style": "deep", "accent": "Standard", "gender": "male", "language": "finnish", "description": "A deep and friendly young adult male voice in Finnish."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ6.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Trustworthy Advisor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS8', 'hindi_male_1_v2', 'system_voice_library', 'library', 'minimax', 'Trustworthy Advisor', 'A magnetic and trustworthy adult male advisor''s voice in Hindi.', '{"age": "adult", "style": "magnetic", "accent": "Standard", "gender": "male", "language": "hi", "description": "A magnetic and trustworthy adult male advisor''s voice in Hindi."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ7.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Tranquil Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXS9', 'hindi_female_2_v1', 'system_voice_library', 'library', 'minimax', 'Tranquil Woman', 'A gentle and tranquil adult female voice in Hindi.', '{"age": "adult", "style": "gentle", "accent": "Standard", "gender": "female", "language": "hi", "description": "A gentle and tranquil adult female voice in Hindi."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ8.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- News Anchor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSA', 'hindi_female_1_v2', 'system_voice_library', 'library', 'minimax', 'News Anchor', 'A calm adult female news anchor''s voice in Hindi.', '{"age": "adult", "style": "calm", "accent": "Standard", "gender": "female", "language": "hi", "description": "A calm adult female news anchor''s voice in Hindi."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQ9.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Upbeat Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSB', 'Bulgarian_male_2_v1', 'system_voice_library', 'library', 'minimax', 'Upbeat Man', 'A Male Bulgarian voice with a standard accent, characterized as upbeat and energetic.', '{"age": "adult", "style": "informative", "accent": "Standard", "gender": "male", "language": "bulgarian", "description": "A Male Bulgarian voice with a standard accent, characterized as upbeat and energetic."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQA.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Graceful Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSC', 'Bulgarian_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Graceful Lady', 'A Female Bulgarian voice with a standard accent, characterized as graceful and elegant.', '{"age": "adult", "style": "conversational", "accent": "Standard", "gender": "female", "language": "bulgarian", "description": "A Female Bulgarian voice with a standard accent, characterized as graceful and elegant."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQB.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Energetic Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSD', 'Danish_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Energetic Youth', 'A Male Danish voice with a standard accent, characterized as youthful and full of energy.', '{"age": "adult", "style": "social_media", "accent": "Standard", "gender": "male", "language": "danish", "description": "A Male Danish voice with a standard accent, characterized as youthful and full of energy."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQC.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Wise Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSE', 'Danish_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Wise Woman', 'A Female Danish voice with a standard accent, characterized as wise and knowledgeable.', '{"age": "adult", "style": "social_media", "accent": "Standard", "gender": "female", "language": "danish", "description": "A Female Danish voice with a standard accent, characterized as wise and knowledgeable."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQD.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSF', 'Hebrew_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A Male Hebrew voice with a standard accent, characterized as reliable and steady.', '{"age": "adult", "style": "advertisement", "accent": "Standard", "gender": "male", "language": "hebrew", "description": "A Male Hebrew voice with a standard accent, characterized as reliable and steady."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQE.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Sage Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSG', 'Hebrew_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Sage Woman', 'A Female Hebrew voice with a standard accent, characterized as sage-like and calm.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "female", "language": "hebrew", "description": "A Female Hebrew voice with a standard accent, characterized as sage-like and calm."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQF.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Seasoned Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSH', 'Malay_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Seasoned Man', 'A Male Malay voice with a standard accent, characterized as seasoned and experienced.', '{"age": "adult", "style": "conversational", "accent": "Standard", "gender": "male", "language": "ms", "description": "A Male Malay voice with a standard accent, characterized as seasoned and experienced."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRTYBD6FY2ZYGR43BQG.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Passionate Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSJ', 'Malay_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Passionate Lady', 'A Female Malay voice with a standard accent, characterized as passionate and expressive.', '{"age": "adult", "style": "social_media", "accent": "Standard", "gender": "female", "language": "ms", "description": "A Female Malay voice with a standard accent, characterized as passionate and expressive."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2P.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Easygoing Neighbor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSK', 'Malay_female_2_v1', 'system_voice_library', 'library', 'minimax', 'Easygoing Neighbor', 'A Female Malay voice with a a standard accent, characterized as relaxed and welcoming', '{"age": "adult", "style": "social_media", "accent": "Standard", "gender": "female", "language": "ms", "description": "A Female Malay voice with a a standard accent, characterized as relaxed and welcoming"}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2Q.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Steady Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCGT2M0QC2Y0FRYVXSM', 'Persian_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Steady Man', 'A Male Persian voice with a standard accent, characterized as steady and firm.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "male", "language": "persian", "description": "A Male Persian voice with a standard accent, characterized as steady and firm."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2R.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Anchorwoman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7X7', 'Persian_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Anchorwoman', 'A Female Persian voice with a standard accent, characterized as professional and clear, suitable for news anchoring.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "female", "language": "persian", "description": "A Female Persian voice with a standard accent, characterized as professional and clear, suitable for news anchoring."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2S.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Amiable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7X8', 'Slovak_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Amiable Man', 'A Male Slovak voice with a standard accent, characterized as amiable and friendly.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "male", "language": "slovak", "description": "A Male Slovak voice with a standard accent, characterized as amiable and friendly."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2T.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7X9', 'Slovak_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Friendly Woman', 'A Female Slovak voice with a standard accent, characterized as friendly and approachable.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "female", "language": "slovak", "description": "A Female Slovak voice with a standard accent, characterized as friendly and approachable."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2V.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XA', 'Swedish_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Confident Man', 'A Male Swedish voice with a standard accent, characterized as confident and assertive.', '{"age": "adult", "style": "advertisement", "accent": "Standard", "gender": "male", "language": "swedish", "description": "A Male Swedish voice with a standard accent, characterized as confident and assertive."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2W.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Friendly Neighbor
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XB', 'Swedish_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Friendly Neighbor', 'A Female Swedish voice with a standard accent, characterized as friendly, warm, and neighborly.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "female", "language": "swedish", "description": "A Female Swedish voice with a standard accent, characterized as friendly, warm, and neighborly."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2X.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Distinguished Gentleman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XC', 'Croatian_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Distinguished Gentleman', 'A Male Croatian voice with a standard accent, characterized as distinguished and elegant.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "male", "language": "croatian", "description": "A Male Croatian voice with a standard accent, characterized as distinguished and elegant."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2Y.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cheerful Young Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XD', 'Croatian_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Cheerful Young Lady', 'A Female Croatian voice with a standard accent, characterized as cheerful and lively.', '{"age": "adult", "style": "social_media", "accent": "Standard", "gender": "female", "language": "croatian", "description": "A Female Croatian voice with a standard accent, characterized as cheerful and lively."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S2Z.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Cheerful Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XE', 'Filipino_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Cheerful Man', 'A Male Filipino voice with a standard accent, characterized as cheerful and pleasant.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "male", "language": "filipino", "description": "A Male Filipino voice with a standard accent, characterized as cheerful and pleasant."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S30.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Gentle Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XF', 'Filipino_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Gentle Woman', 'A Female Filipino voice with a standard accent, characterized as gentle and kind.', '{"age": "adult", "style": "advertisement", "accent": "Standard", "gender": "female", "language": "filipino", "description": "A Female Filipino voice with a standard accent, characterized as gentle and kind."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S31.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Steady Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XG', 'Hungarian_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Steady Man', 'A Male Hungarian voice with a standard accent, characterized as steady and reliable.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "male", "language": "hungarian", "description": "A Male Hungarian voice with a standard accent, characterized as steady and reliable."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S32.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Calm Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XH', 'Hungarian_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Calm Woman', 'A Female Hungarian voice with a standard accent, characterized as calm and peaceful.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "female", "language": "hungarian", "description": "A Female Hungarian voice with a standard accent, characterized as calm and peaceful."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S33.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XJ', 'Norwegian_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A Male Norwegian voice with a standard accent, characterized as reliable and trustworthy.', '{"age": "adult", "style": "conversational", "accent": "Standard", "gender": "male", "language": "norwegian", "description": "A Male Norwegian voice with a standard accent, characterized as reliable and trustworthy."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S34.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Upbeat Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XK', 'Norwegian_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Upbeat Girl', 'A Female Norwegian voice with a standard accent, characterized as upbeat and energetic.', '{"age": "adult", "style": "social_media", "accent": "Standard", "gender": "female", "language": "norwegian", "description": "A Female Norwegian voice with a standard accent, characterized as upbeat and energetic."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S35.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Male Host
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XM', 'Slovenian_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Male Host', 'A Male Slovenian voice with a standard accent, characterized as professional and engaging, suitable for hosting.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "male", "language": "slovenian", "description": "A Male Slovenian voice with a standard accent, characterized as professional and engaging, suitable for hosting."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S36.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Elegant Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XN', 'Slovenian_female_1_v2', 'system_voice_library', 'library', 'minimax', 'Elegant Lady', 'A Female Slovenian voice with a standard accent, characterized as elegant and sophisticated.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "slovenian", "description": "A Female Slovenian voice with a standard accent, characterized as elegant and sophisticated."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRVS63VCKVRBW061S37.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Reliable Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XP', 'Catalan_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Reliable Man', 'A Male Catalan voice with a standard accent, characterized as reliable and sound.', '{"age": "adult", "style": "infomative", "accent": "Standard", "gender": "male", "language": "catalan", "description": "A Male Catalan voice with a standard accent, characterized as reliable and sound."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRWZMZH21THAHZSQ1WT.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Graceful Lady
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XQ', 'Catalan_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Graceful Lady', 'A Female Catalan voice with a standard accent, characterized as graceful and gentle.', '{"age": "adult", "style": "conversational", "accent": "Standard", "gender": "female", "language": "catalan", "description": "A Female Catalan voice with a standard accent, characterized as graceful and gentle."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRWZMZH21THAHZSQ1WV.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Young Gentleman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XR', 'Nynorsk_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Young Gentleman', 'A Male Nynorsk voice with a standard accent, characterized as young and courteous.', '{"age": "adult", "style": "conversational", "accent": "Standard", "gender": "male", "language": "nynorsk", "description": "A Male Nynorsk voice with a standard accent, characterized as young and courteous."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRWZMZH21THAHZSQ1WW.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Shy Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XS', 'Nynorsk_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Shy Girl', 'A Female Nynorsk voice with a standard accent, characterized as shy and soft-spoken.', '{"age": "adult", "style": "conversational", "accent": "Standard", "gender": "female", "language": "nynorsk", "description": "A Female Nynorsk voice with a standard accent, characterized as shy and soft-spoken."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRWZMZH21THAHZSQ1WX.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Confident Man
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCHKNV0CQN3W0ERZ7XT', 'Tamil_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Confident Man', 'A Male Tamil voice with a standard accent, characterized as confident and strong.', '{"age": "adult", "style": "social_media", "accent": "Standard", "gender": "male", "language": "tamil", "description": "A Male Tamil voice with a standard accent, characterized as confident and strong."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRWZMZH21THAHZSQ1WY.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Mature Woman
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCJE42PWE5RR1DCN82K', 'Tamil_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Mature Woman', 'A Female Tamil voice with a standard accent, characterized as mature and poised.', '{"age": "adult", "style": "audiobook", "accent": "Standard", "gender": "female", "language": "tamil", "description": "A Female Tamil voice with a standard accent, characterized as mature and poised."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRWZMZH21THAHZSQ1WZ.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Steady Youth
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCJE42PWE5RR1DCN82M', 'Afrikaans_male_1_v1', 'system_voice_library', 'library', 'minimax', 'Steady Youth', 'A Male Afrikaans voice with a standard accent, characterized as young and steady.', '{"age": "adult", "style": "broadcast", "accent": "Standard", "gender": "male", "language": "afrikaans", "description": "A Male Afrikaans voice with a standard accent, characterized as young and steady."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRWZMZH21THAHZSQ1X0.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Outgoing Girl
INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('voice_01KD4WZTCJE42PWE5RR1DCN82N', 'Afrikaans_female_1_v1', 'system_voice_library', 'library', 'minimax', 'Outgoing Girl', 'A Female Afrikaans voice with a standard accent, characterized as outgoing and lively.', '{"age": "adult", "style": "social_media", "accent": "Standard", "gender": "female", "language": "afrikaans", "description": "A Female Afrikaans voice with a standard accent, characterized as outgoing and lively."}'::jsonb, '${S3_PUBLIC_BASE_URL}/${S3_BUCKET_NAME}/voice_samples/voice_01KD4Z1JRWZMZH21THAHZSQ1X1.wav', NULL, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();

-- Migration complete
"""
Add Library Voice Script

一步完成：创建数据库记录 + 上传音频到 S3 + 设置 sample_url

支持两种模式：
1. 单文件模式：添加单个音频文件
2. 批量模式：从目录批量添加音频文件

Usage:
    cd main/live-agent-api
    
    # 单文件添加
    uv run python scripts/add_library_voice.py \
        --audio ~/path/to/English_NewVoice_English.mp3 \
        --name "New Voice" \
        --desc "A new voice description" \
        --language en \
        --gender female \
        --age adult
    
    # 批量添加（从目录，自动解析文件名）
    uv run python scripts/add_library_voice.py \
        --audio-dir ~/path/to/audio_files \
        --dry-run
    
    # 批量添加（正式执行）
    uv run python scripts/add_library_voice.py \
        --audio-dir ~/path/to/audio_files

文件命名规则：{reference_id}_{language}.mp3
例如：English_NewVoice_English.mp3 -> reference_id="English_NewVoice", language="English"
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

import aioboto3
import ulid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from loguru import logger


# Known language patterns for parsing filenames
KNOWN_LANGUAGES = [
    "Chinese Mandarin", "English", "Arabic", "Japanese", "Korean",
    "French", "German", "Italian", "Spanish", "Portuguese",
    "Russian", "Thai", "Vietnamese", "Indonesian", "Cantonese",
    "Dutch", "Polish", "Turkish", "Greek", "Hebrew", "Hindi",
    "Hungarian", "Czech", "Danish", "Finnish", "Bulgarian",
    "Croatian", "Romanian", "Slovak", "Slovenian", "Swedish",
    "Norwegian", "Ukrainian", "Filipino", "Afrikaans", "Catalan",
    "Serbian", "Malay", "Bengali", "Tamil", "Persian",
]

# Language code mapping
LANGUAGE_TO_CODE = {
    "chinese mandarin": "zh",
    "english": "en",
    "arabic": "ar",
    "japanese": "ja",
    "korean": "ko",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "spanish": "es",
    "portuguese": "pt",
    "russian": "ru",
    "thai": "th",
    "vietnamese": "vi",
    "indonesian": "id",
    "cantonese": "yue",
    "dutch": "nl",
    "polish": "pl",
    "turkish": "tr",
    "greek": "el",
    "hebrew": "he",
    "hindi": "hi",
    "hungarian": "hu",
    "czech": "cs",
    "danish": "da",
    "finnish": "fi",
    "bulgarian": "bg",
    "croatian": "hr",
    "romanian": "ro",
    "slovak": "sk",
    "slovenian": "sl",
    "swedish": "sv",
    "norwegian": "no",
    "ukrainian": "uk",
    "filipino": "fil",
    "afrikaans": "af",
    "catalan": "ca",
    "serbian": "sr",
    "malay": "ms",
    "bengali": "bn",
    "tamil": "ta",
    "persian": "fa",
}


def generate_voice_id() -> str:
    """Generate a unique voice_id using ULID"""
    return f"voice_{ulid.new().str}"


def parse_filename(filename: str) -> Optional[Tuple[str, str]]:
    """
    Parse filename to extract reference_id and language.
    
    Format: {reference_id}_{language}.mp3
    
    Returns:
        Tuple of (reference_id, language) or None if parsing fails
    """
    name = Path(filename).stem
    
    # Try to match known languages at the end
    for lang in KNOWN_LANGUAGES:
        if name.endswith(f"_{lang}"):
            ref_id = name[: -(len(lang) + 1)]
            return (ref_id, lang)
    
    # Fallback: split by last underscore
    last_underscore = name.rfind("_")
    if last_underscore > 0:
        ref_id = name[:last_underscore]
        lang = name[last_underscore + 1:]
        return (ref_id, lang)
    
    return None


def normalize_reference_id(ref_id: str) -> str:
    """Normalize reference_id for database consistency"""
    # Handle Chinese Mandarin -> Chinese (Mandarin)
    if ref_id.startswith("Chinese Mandarin_"):
        ref_id = ref_id.replace("Chinese Mandarin_", "Chinese (Mandarin)_", 1)
    
    # Handle Cantonese professional host naming
    if ref_id == "Cantonese_ProfessionalHostF":
        ref_id = "Cantonese_ProfessionalHost（F)"
    elif ref_id == "Cantonese_ProfessionalHostM":
        ref_id = "Cantonese_ProfessionalHost（M)"
    
    return ref_id


def get_language_code(language: str) -> str:
    """Convert language name to ISO code"""
    return LANGUAGE_TO_CODE.get(language.lower(), language.lower()[:2])


async def upload_to_s3(
    s3_client,
    local_path: Path,
    bucket_name: str,
    s3_key: str,
) -> bool:
    """Upload a file to S3"""
    try:
        await s3_client.upload_file(
            str(local_path),
            bucket_name,
            s3_key,
            ExtraArgs={
                "ContentType": "audio/mpeg",
                "ACL": "public-read",
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to upload {local_path} to s3://{bucket_name}/{s3_key}: {e}")
        return False


async def check_reference_id_exists(
    session: AsyncSession,
    reference_id: str,
) -> bool:
    """Check if a voice with given reference_id already exists"""
    try:
        result = await session.execute(
            text("SELECT 1 FROM voices WHERE reference_id = :ref_id LIMIT 1"),
            {"ref_id": reference_id}
        )
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Failed to check reference_id existence: {e}")
        return False


async def insert_voice(
    session: AsyncSession,
    voice_id: str,
    reference_id: str,
    name: str,
    desc: str,
    tags: dict,
    sample_url: str,
) -> bool:
    """Insert a new voice record into database"""
    try:
        await session.execute(
            text("""
                INSERT INTO voices (
                    voice_id, reference_id, owner_id, category, provider,
                    name, "desc", tags, sample_url, sample_text, created_at, updated_at
                ) VALUES (
                    :voice_id, :reference_id, 'system_voice_library', 'library', 'minimax',
                    :name, :desc, :tags::jsonb, :sample_url, NULL, NOW(), NOW()
                )
            """),
            {
                "voice_id": voice_id,
                "reference_id": reference_id,
                "name": name,
                "desc": desc,
                "tags": json.dumps(tags),
                "sample_url": sample_url,
            }
        )
        await session.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to insert voice {voice_id}: {e}")
        await session.rollback()
        return False


async def add_single_voice(
    session: AsyncSession,
    s3_client,
    audio_path: Path,
    bucket_name: str,
    remote_base_url: str,
    s3_prefix: str,
    name: str,
    desc: str,
    language: str,
    gender: str,
    age: str = "adult",
    style: str = "general",
    reference_id: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    """
    Add a single voice: create DB record + upload audio + set sample_url
    """
    # Generate IDs
    voice_id = generate_voice_id()
    if not reference_id:
        # Use filename (without extension) as reference_id
        reference_id = audio_path.stem
    
    reference_id = normalize_reference_id(reference_id)
    
    # Check if already exists
    if await check_reference_id_exists(session, reference_id):
        logger.warning(f"Voice with reference_id={reference_id} already exists, skipping")
        return False
    
    # Build tags
    language_code = get_language_code(language)
    tags = {
        "gender": gender,
        "age": age,
        "language": language_code,
        "style": style,
        "description": desc,
    }
    
    # Build S3 key and URL
    s3_key = f"{s3_prefix}/{voice_id}.mp3"
    sample_url = f"{remote_base_url}/{bucket_name}/{s3_key}"
    
    if dry_run:
        logger.info(f"[DRY RUN] Would add voice:")
        logger.info(f"  voice_id: {voice_id}")
        logger.info(f"  reference_id: {reference_id}")
        logger.info(f"  name: {name}")
        logger.info(f"  language: {language} ({language_code})")
        logger.info(f"  gender: {gender}")
        logger.info(f"  s3_key: {s3_key}")
        logger.info(f"  sample_url: {sample_url}")
        return True
    
    # Upload to S3
    logger.info(f"Uploading {audio_path.name} -> s3://{bucket_name}/{s3_key}")
    uploaded = await upload_to_s3(s3_client, audio_path, bucket_name, s3_key)
    if not uploaded:
        return False
    
    # Insert to database
    logger.info(f"Inserting voice record: {voice_id} ({name})")
    inserted = await insert_voice(
        session, voice_id, reference_id, name, desc, tags, sample_url
    )
    if not inserted:
        return False
    
    logger.info(f"✅ Added voice: {voice_id} -> {sample_url}")
    return True


async def add_voices_from_directory(
    session_factory,
    s3_client,
    audio_dir: Path,
    bucket_name: str,
    remote_base_url: str,
    s3_prefix: str,
    dry_run: bool = False,
) -> Tuple[int, int, int]:
    """
    Add voices from a directory of audio files.
    
    Returns:
        Tuple of (success_count, skipped_count, failed_count)
    """
    audio_files = list(audio_dir.glob("*.mp3"))
    logger.info(f"Found {len(audio_files)} MP3 files")
    
    success = 0
    skipped = 0
    failed = 0
    
    for audio_path in audio_files:
        # Parse filename
        parsed = parse_filename(audio_path.name)
        if not parsed:
            logger.warning(f"Cannot parse filename: {audio_path.name}, skipping")
            skipped += 1
            continue
        
        ref_id, language = parsed
        ref_id = normalize_reference_id(ref_id)
        
        # Generate name from reference_id
        name = ref_id.replace("_", " ")
        if name.startswith("Chinese (Mandarin) "):
            name = name.replace("Chinese (Mandarin) ", "")
        
        desc = f"A {language} voice"
        
        async with session_factory() as session:
            # Check if exists
            if await check_reference_id_exists(session, ref_id):
                logger.info(f"[SKIP] {audio_path.name} (reference_id={ref_id} exists)")
                skipped += 1
                continue
            
            result = await add_single_voice(
                session=session,
                s3_client=s3_client,
                audio_path=audio_path,
                bucket_name=bucket_name,
                remote_base_url=remote_base_url,
                s3_prefix=s3_prefix,
                name=name,
                desc=desc,
                language=language,
                gender="unknown",  # Will need manual update or metadata file
                age="adult",
                reference_id=ref_id,
                dry_run=dry_run,
            )
            
            if result:
                success += 1
            else:
                failed += 1
    
    return success, skipped, failed


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Add library voice(s): create DB record + upload audio + set sample_url"
    )
    
    # Mode selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--audio",
        dest="audio_file",
        help="Single audio file to add"
    )
    group.add_argument(
        "--audio-dir",
        dest="audio_dir",
        help="Directory of audio files to add (batch mode)"
    )
    
    # Single file mode options
    parser.add_argument("--name", help="Voice display name (single file mode)")
    parser.add_argument("--desc", help="Voice description (single file mode)")
    parser.add_argument("--language", default="en", help="Language code or name")
    parser.add_argument("--gender", choices=["male", "female", "unknown"], default="unknown")
    parser.add_argument("--age", default="adult", 
                       choices=["youth", "young_adult", "adult", "middle_aged", "senior"])
    parser.add_argument("--reference-id", help="Custom reference_id (default: filename)")
    
    # Common options
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    parser.add_argument("--db", dest="database_url", help="Database URL")
    parser.add_argument("--s3-endpoint", dest="s3_endpoint", help="S3 endpoint URL")
    parser.add_argument("--remote-base-url", dest="remote_base_url", help="Public base URL for sample_url")
    parser.add_argument("--bucket", dest="bucket_name", help="S3 bucket name")
    parser.add_argument("--s3-prefix", dest="s3_prefix", default="voice_samples", help="S3 prefix")
    
    args = parser.parse_args()
    
    # Load config
    database_url = args.database_url or os.getenv("DATABASE_URL")
    s3_endpoint = args.s3_endpoint or os.getenv("S3_ENDPOINT_URL")
    bucket_name = args.bucket_name or os.getenv("S3_BUCKET_NAME")
    remote_base_url = args.remote_base_url or os.getenv("S3_PUBLIC_BASE_URL")
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    
    # Validate
    if not database_url:
        logger.error("DATABASE_URL is required")
        sys.exit(1)
    
    if not args.dry_run:
        if not all([bucket_name, remote_base_url, aws_access_key, aws_secret_key]):
            logger.error("Missing S3 config. Set S3_BUCKET_NAME, S3_PUBLIC_BASE_URL, "
                        "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            sys.exit(1)
    
    logger.info("Configuration:")
    logger.info(f"  Database: {'...' + database_url[-30:] if len(database_url) > 30 else database_url}")
    logger.info(f"  S3 endpoint: {s3_endpoint}")
    logger.info(f"  Bucket: {bucket_name}")
    logger.info(f"  Remote base URL: {remote_base_url}")
    logger.info(f"  Dry run: {args.dry_run}")
    
    # Initialize database
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Initialize S3
    s3_session = aioboto3.Session()
    
    try:
        async with s3_session.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            endpoint_url=s3_endpoint
        ) as s3_client:
            
            if args.audio_file:
                # Single file mode
                audio_path = Path(args.audio_file).expanduser()
                if not audio_path.exists():
                    logger.error(f"Audio file not found: {audio_path}")
                    sys.exit(1)
                
                if not args.name:
                    logger.error("--name is required for single file mode")
                    sys.exit(1)
                
                async with async_session() as session:
                    result = await add_single_voice(
                        session=session,
                        s3_client=s3_client,
                        audio_path=audio_path,
                        bucket_name=bucket_name,
                        remote_base_url=remote_base_url,
                        s3_prefix=args.s3_prefix,
                        name=args.name,
                        desc=args.desc or f"A {args.language} voice",
                        language=args.language,
                        gender=args.gender,
                        age=args.age,
                        reference_id=args.reference_id,
                        dry_run=args.dry_run,
                    )
                
                if result:
                    logger.info("✅ Voice added successfully")
                else:
                    logger.error("❌ Failed to add voice")
                    sys.exit(1)
            
            else:
                # Batch mode
                audio_dir = Path(args.audio_dir).expanduser()
                if not audio_dir.exists():
                    logger.error(f"Audio directory not found: {audio_dir}")
                    sys.exit(1)
                
                success, skipped, failed = await add_voices_from_directory(
                    session_factory=async_session,
                    s3_client=s3_client,
                    audio_dir=audio_dir,
                    bucket_name=bucket_name,
                    remote_base_url=remote_base_url,
                    s3_prefix=args.s3_prefix,
                    dry_run=args.dry_run,
                )
                
                logger.info("=" * 50)
                logger.info("Summary:")
                logger.info(f"  Success: {success}")
                logger.info(f"  Skipped (exists): {skipped}")
                logger.info(f"  Failed: {failed}")
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())


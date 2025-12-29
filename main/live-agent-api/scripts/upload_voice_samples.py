"""
Voice Sample Upload Script

Upload audio sample files to S3 and update database sample_url.

The audio files are named as: {reference_id}_{language}.mp3
Examples:
    - angry_pirate_1_English.mp3 -> reference_id="angry_pirate_1", language="English"
    - Arabic_CalmWoman_Arabic.mp3 -> reference_id="Arabic_CalmWoman", language="Arabic"

Usage:
    cd main/live-agent-api
    
    # Dry run (no actual upload or database update)
    uv run python scripts/upload_voice_samples.py \
        ~/Desktop/2.6_output_audio_20251218_153501 \
        --dry-run
    
    # Upload to S3 and update database
    uv run python scripts/upload_voice_samples.py \
        ~/Desktop/2.6_output_audio_20251218_153501
    
    # Use custom remote base URL (for production)
    uv run python scripts/upload_voice_samples.py \
        ~/Desktop/2.6_output_audio_20251218_153501 \
        --remote-base-url "https://s3.example.com"
"""

import asyncio
import os
import sys
import re
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env file from main/ directory (parent of live-agent-api)
# Script is at: main/live-agent-api/scripts/upload_voice_samples.py
# .env is at: main/.env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

import aioboto3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from loguru import logger


def parse_filename(filename: str) -> Optional[Tuple[str, str]]:
    """
    Parse filename to extract reference_id and language.
    
    The filename format is: {reference_id}_{language}.mp3
    The reference_id can contain underscores, so we find the last underscore
    before the language part.
    
    Examples:
        angry_pirate_1_English.mp3 -> ("angry_pirate_1", "English")
        Arabic_CalmWoman_Arabic.mp3 -> ("Arabic_CalmWoman", "Arabic")
        Chinese Mandarin_BashfulGirl_Chinese Mandarin.mp3 -> ("Chinese Mandarin_BashfulGirl", "Chinese Mandarin")
    
    Returns:
        Tuple of (reference_id, language) or None if parsing fails
    """
    # Remove extension
    name = Path(filename).stem
    
    # Split by last underscore to get reference_id and language
    # But language can contain spaces, so we need to be careful
    
    # Known language patterns (from examining the files)
    known_languages = [
        "Chinese Mandarin",
        "English",
        "Arabic",
        "Japanese",
        "Korean",
        "French",
        "German",
        "Italian",
        "Spanish",
        "Portuguese",
        "Russian",
        "Thai",
        "Vietnamese",
        "Indonesian",
        "Cantonese",
        "Dutch",
        "Polish",
        "Turkish",
        "Greek",
        "Hebrew",
        "Hindi",
        "Hungarian",
        "Czech",
        "Danish",
        "Finnish",
        "Bulgarian",
        "Croatian",
        "Romanian",
        "Slovak",
        "Slovenian",
        "Swedish",
        "Norwegian",
        "Ukrainian",
        "Filipino",
        "Afrikaans",
        "Catalan",
        "Serbian",
        "Malay",
        "Bengali",
    ]
    
    # Try to match known languages at the end
    for lang in known_languages:
        if name.endswith(f"_{lang}"):
            ref_id = name[: -(len(lang) + 1)]  # Remove _language part
            return (ref_id, lang)
    
    # Fallback: split by last underscore
    last_underscore = name.rfind("_")
    if last_underscore > 0:
        ref_id = name[:last_underscore]
        lang = name[last_underscore + 1:]
        return (ref_id, lang)
    
    return None


def normalize_reference_id(ref_id: str) -> str:
    """
    Convert filename reference_id format to database reference_id format.
    
    Mappings:
        - "Chinese Mandarin_xxx" -> "Chinese (Mandarin)_xxx"
        - "Cantonese_ProfessionalHostF" -> "Cantonese_ProfessionalHost（F)"
        - "Cantonese_ProfessionalHostM" -> "Cantonese_ProfessionalHost（M)"
    
    Args:
        ref_id: Reference ID from filename
        
    Returns:
        Normalized reference_id for database lookup
    """
    # Handle Chinese Mandarin -> Chinese (Mandarin)
    if ref_id.startswith("Chinese Mandarin_"):
        ref_id = ref_id.replace("Chinese Mandarin_", "Chinese (Mandarin)_", 1)
    
    # Handle Cantonese professional host naming (add Chinese parentheses)
    if ref_id == "Cantonese_ProfessionalHostF":
        ref_id = "Cantonese_ProfessionalHost（F)"
    elif ref_id == "Cantonese_ProfessionalHostM":
        ref_id = "Cantonese_ProfessionalHost（M)"
    
    return ref_id


async def upload_to_s3(
    s3_client,
    local_path: Path,
    bucket_name: str,
    s3_key: str,
) -> bool:
    """
    Upload a file to S3.
    
    Args:
        s3_client: Boto3 S3 client
        local_path: Local file path
        bucket_name: S3 bucket name
        s3_key: S3 object key
        
    Returns:
        True if upload succeeded, False otherwise
    """
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


async def get_voice_by_reference_id(
    session: AsyncSession,
    reference_id: str,
) -> Optional[Tuple[str, str]]:
    """
    Get voice_id by reference_id.
    
    Returns:
        Tuple of (voice_id, old_sample_url) or None if not found
    """
    try:
        result = await session.execute(
            text("""
                SELECT voice_id, sample_url FROM voices 
                WHERE reference_id = :reference_id
                LIMIT 1
            """),
            {"reference_id": reference_id}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return (row[0], row[1])
        
    except Exception as e:
        logger.error(f"Failed to query voice for reference_id={reference_id}: {e}")
        return None


async def update_sample_url(
    session: AsyncSession,
    voice_id: str,
    new_sample_url: str,
) -> bool:
    """
    Update sample_url in database for voice with given voice_id.
    
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        await session.execute(
            text("""
                UPDATE voices 
                SET sample_url = :new_url, updated_at = NOW()
                WHERE voice_id = :voice_id
            """),
            {"new_url": new_sample_url, "voice_id": voice_id}
        )
        await session.commit()
        return True
        
    except Exception as e:
        logger.error(f"Failed to update sample_url for voice_id={voice_id}: {e}")
        await session.rollback()
        return False


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Upload voice samples to S3 and update database sample_url"
    )
    parser.add_argument(
        "audio_dir",
        help="Directory containing audio sample files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without actually uploading or updating"
    )
    parser.add_argument(
        "--db",
        dest="database_url",
        default=None,
        help="Database URL (default: from .env DATABASE_URL)"
    )
    parser.add_argument(
        "--s3-endpoint",
        dest="s3_endpoint",
        default=None,
        help="S3 endpoint URL (default: from .env S3_ENDPOINT_URL)"
    )
    parser.add_argument(
        "--bucket",
        dest="bucket_name",
        default=None,
        help="S3 bucket name (default: from .env S3_BUCKET_NAME)"
    )
    parser.add_argument(
        "--remote-base-url",
        dest="remote_base_url",
        default=None,
        help="Remote base URL for sample_url in database (default: from .env S3_PUBLIC_BASE_URL). "
             "This is the URL that will be stored in the database."
    )
    parser.add_argument(
        "--s3-prefix",
        dest="s3_prefix",
        default="voice_samples",
        help="S3 prefix/folder for uploaded files (default: voice_samples)"
    )
    
    args = parser.parse_args()
    
    # Load config from args or env vars
    database_url = args.database_url or os.getenv("DATABASE_URL")
    s3_endpoint = args.s3_endpoint or os.getenv("S3_ENDPOINT_URL")
    bucket_name = args.bucket_name or os.getenv("S3_BUCKET_NAME")
    remote_base_url = args.remote_base_url or os.getenv("S3_PUBLIC_BASE_URL")
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    
    # Log config
    logger.info("Configuration:")
    logger.info(f"  Audio directory: {args.audio_dir}")
    logger.info(f"  S3 endpoint: {s3_endpoint}")
    logger.info(f"  Bucket: {bucket_name}")
    logger.info(f"  S3 prefix: {args.s3_prefix}")
    logger.info(f"  Remote base URL: {remote_base_url}")
    logger.info(f"  Dry run: {args.dry_run}")
    
    # Validate
    audio_dir = Path(args.audio_dir).expanduser()
    if not audio_dir.exists():
        logger.error(f"Audio directory not found: {audio_dir}")
        sys.exit(1)
    
    # Database is always required (for looking up voice_id by reference_id)
    if not database_url:
        logger.error("DATABASE_URL is required. Set it in .env or via --db argument")
        sys.exit(1)
    
    if not args.dry_run:
        if not all([bucket_name, remote_base_url, aws_access_key, aws_secret_key]):
            logger.error("Missing required config. Set S3_BUCKET_NAME, "
                        "S3_PUBLIC_BASE_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY in .env or via args")
            sys.exit(1)
    
    # Scan audio files
    audio_files = list(audio_dir.glob("*.mp3"))
    logger.info(f"Found {len(audio_files)} MP3 files")
    
    # Parse filenames
    parsed_files = []
    parse_errors = []
    for f in audio_files:
        result = parse_filename(f.name)
        if result:
            ref_id, lang = result
            parsed_files.append((f, ref_id, lang))
        else:
            parse_errors.append(f.name)
    
    if parse_errors:
        logger.warning(f"Failed to parse {len(parse_errors)} filenames:")
        for name in parse_errors[:10]:
            logger.warning(f"  - {name}")
        if len(parse_errors) > 10:
            logger.warning(f"  ... and {len(parse_errors) - 10} more")
    
    logger.info(f"Successfully parsed {len(parsed_files)} files")
    
    # Initialize database connection (needed for both dry-run and actual run)
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # First pass: lookup voice_id for each reference_id
    logger.info("Looking up voice_id for each reference_id in database...")
    files_with_voice_id = []
    not_found_refs = []
    
    async with async_session() as db_session:
        for path, ref_id, lang in parsed_files:
            # Normalize reference_id for database lookup
            db_ref_id = normalize_reference_id(ref_id)
            voice_info = await get_voice_by_reference_id(db_session, db_ref_id)
            if voice_info:
                voice_id, old_sample_url = voice_info
                files_with_voice_id.append((path, ref_id, db_ref_id, lang, voice_id, old_sample_url))
            else:
                not_found_refs.append((path.name, ref_id, db_ref_id))
    
    if not_found_refs:
        logger.warning(f"Voice not found in database for {len(not_found_refs)} files:")
        for name, ref_id, db_ref_id in not_found_refs[:10]:
            logger.warning(f"  - {name} (file_ref: {ref_id} -> db_ref: {db_ref_id})")
        if len(not_found_refs) > 10:
            logger.warning(f"  ... and {len(not_found_refs) - 10} more")
    
    logger.info(f"Found {len(files_with_voice_id)} voices in database")
    
    if args.dry_run:
        logger.info("=== DRY RUN MODE ===")
        for i, (path, ref_id, db_ref_id, lang, voice_id, old_url) in enumerate(files_with_voice_id[:20], 1):
            s3_key = f"{args.s3_prefix}/{voice_id}.mp3"
            sample_url = f"{remote_base_url}/{bucket_name}/{s3_key}"
            print(f"\n{i}. {path.name}")
            print(f"   file_ref_id: {ref_id}")
            print(f"   db_ref_id: {db_ref_id}")
            print(f"   voice_id: {voice_id}")
            print(f"   language: {lang}")
            print(f"   s3_key: {s3_key}")
            print(f"   old_sample_url: {old_url}")
            print(f"   new_sample_url: {sample_url}")
        
        if len(files_with_voice_id) > 20:
            print(f"\n... and {len(files_with_voice_id) - 20} more files")
        
        logger.info(f"Would upload {len(files_with_voice_id)} files and update database")
        logger.info(f"Skipping {len(not_found_refs)} files (not found in database)")
        await engine.dispose()
        return
    
    # Initialize S3 client
    s3_session = aioboto3.Session()
    
    # Process files
    upload_success = 0
    upload_failed = 0
    db_updated = 0
    db_failed = 0
    
    async with s3_session.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region,
        endpoint_url=s3_endpoint
    ) as s3_client:
        
        for i, (path, ref_id, db_ref_id, lang, voice_id, old_url) in enumerate(files_with_voice_id, 1):
            # Use voice_id for the S3 key (not reference_id)
            s3_key = f"{args.s3_prefix}/{voice_id}.mp3"
            sample_url = f"{remote_base_url}/{bucket_name}/{s3_key}"
            
            # Upload to S3
            logger.info(f"[{i}/{len(files_with_voice_id)}] Uploading {path.name} -> s3://{bucket_name}/{s3_key}")
            
            uploaded = await upload_to_s3(s3_client, path, bucket_name, s3_key)
            
            if uploaded:
                upload_success += 1
                
                # Update database
                async with async_session() as db_session:
                    success = await update_sample_url(db_session, voice_id, sample_url)
                    
                    if success:
                        db_updated += 1
                        logger.info(f"  Updated voice {voice_id}: sample_url = {sample_url}")
                    else:
                        db_failed += 1
                        logger.error(f"  Failed to update database for voice_id={voice_id}")
            else:
                upload_failed += 1
    
    await engine.dispose()
    
    # Summary
    logger.info("=" * 50)
    logger.info("Summary:")
    logger.info(f"  Total audio files: {len(parsed_files)}")
    logger.info(f"  Found in database: {len(files_with_voice_id)}")
    logger.info(f"  Not found in DB: {len(not_found_refs)}")
    logger.info(f"  Upload success: {upload_success}")
    logger.info(f"  Upload failed: {upload_failed}")
    logger.info(f"  Database updated: {db_updated}")
    logger.info(f"  Database errors: {db_failed}")


if __name__ == "__main__":
    asyncio.run(main())


"""
Export Voice Library to SQL Migration

Export current minimax library voices from database to SQL INSERT statements.

Usage:
    cd main/live-agent-api
    uv run python scripts/export_library_voices.py \
      --db "postgresql+asyncpg://postgres:postgres@localhost:5432/live_agent" \
      --output migrations/004_insert_minimax_voices.sql
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from loguru import logger


async def export_library_voices(database_url: str, output_path: str):
    """Export library voices to SQL file"""
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Query all library voices
        result = await session.execute(
            text("""
                SELECT voice_id, reference_id, owner_id, category, provider, 
                       name, "desc", tags, sample_url, sample_text
                FROM voices 
                WHERE category = 'library'
                ORDER BY voice_id
            """)
        )
        voices = result.fetchall()
        
    await engine.dispose()
    
    if not voices:
        logger.warning("No library voices found in database")
        return
    
    logger.info(f"Found {len(voices)} library voices to export")
    
    # Generate SQL file
    sql_lines = [
        "-- Migration: Insert MiniMax Voice Library Data",
        f"-- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"-- Total voices: {len(voices)}",
        "",
        "-- Ensure system user exists",
        "INSERT INTO \"user\" (user_id, username, password)",
        "VALUES ('system_voice_library', 'system_voice_library', 'not_for_login')",
        "ON CONFLICT (user_id) DO NOTHING;",
        "",
        "-- Insert library voices",
    ]
    
    for voice in voices:
        voice_id, reference_id, owner_id, category, provider, name, desc, tags, sample_url, sample_text = voice
        
        # Escape single quotes in strings
        name_escaped = name.replace("'", "''") if name else ""
        desc_escaped = desc.replace("'", "''") if desc else ""
        tags_json = json.dumps(tags) if tags else "{}"
        sample_url_escaped = sample_url.replace("'", "''") if sample_url else ""
        sample_text_escaped = sample_text.replace("'", "''") if sample_text else ""
        
        sql = f"""INSERT INTO voices (voice_id, reference_id, owner_id, category, provider, name, "desc", tags, sample_url, sample_text, created_at, updated_at)
VALUES ('{voice_id}', '{reference_id}', '{owner_id}', '{category}', '{provider}', '{name_escaped}', '{desc_escaped}', '{tags_json}'::jsonb, '{sample_url_escaped}', {f"'{sample_text_escaped}'" if sample_text else 'NULL'}, NOW(), NOW())
ON CONFLICT (voice_id) DO UPDATE SET
    name = EXCLUDED.name,
    "desc" = EXCLUDED."desc",
    tags = EXCLUDED.tags,
    sample_url = EXCLUDED.sample_url,
    updated_at = NOW();"""
        
        sql_lines.append("")
        sql_lines.append(f"-- {name}")
        sql_lines.append(sql)
    
    sql_lines.append("")
    sql_lines.append("-- Migration complete")
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(sql_lines), encoding="utf-8")
    
    logger.info(f"Exported to: {output_path}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Export library voices to SQL migration")
    parser.add_argument(
        "--db",
        dest="database_url",
        default=os.getenv("DATABASE_URL"),
        help="Database URL"
    )
    parser.add_argument(
        "--output", "-o",
        dest="output_path",
        default="migrations/004_insert_minimax_voices.sql",
        help="Output SQL file path"
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        logger.error("DATABASE_URL is required")
        sys.exit(1)
    
    await export_library_voices(args.database_url, args.output_path)


if __name__ == "__main__":
    asyncio.run(main())


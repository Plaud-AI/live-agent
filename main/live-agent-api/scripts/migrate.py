#!/usr/bin/env python3
"""
Database Migration Runner

使用 asyncpg 原生连接执行 SQL 迁移脚本，确保多语句 SQL 和 $$ 块的正确处理。
"""
import asyncio
import os
import logging
import sys
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MigrationRunner")

# 延迟导入，因为这个脚本可能在不同环境下运行
def get_database_url():
    """从环境变量获取数据库 URL"""
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        # 尝试从 .env 文件加载
        env_path = Path(__file__).resolve().parent.parent / '.env'
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        url = line.split('=', 1)[1].strip().strip('"\'')
                        break
    return url


def parse_dsn(sqlalchemy_url: str) -> str:
    """
    将 SQLAlchemy URL 转换为 asyncpg DSN
    postgresql+asyncpg://user:pass@host:port/db -> postgresql://user:pass@host:port/db
    """
    return re.sub(r'^postgresql\+asyncpg://', 'postgresql://', sqlalchemy_url)


async def run_migrations():
    """执行数据库迁移"""
    import asyncpg
    
    migration_dir = Path(__file__).resolve().parent.parent / "migrations"
    database_url = get_database_url()
    
    if not database_url or 'postgresql' not in database_url:
        logger.error("Invalid or missing DATABASE_URL")
        sys.exit(1)
    
    dsn = parse_dsn(database_url)
    # 隐藏密码打印
    safe_dsn = re.sub(r'://[^:]+:[^@]+@', '://***:***@', dsn)
    logger.info(f"Connecting to: {safe_dsn}")
    
    try:
        conn = await asyncpg.connect(dsn)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # 1. 确保迁移记录表存在
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Migration tracking table ready")
        
        # 2. 获取并排序迁移文件
        if not migration_dir.exists():
            logger.warning(f"Migration directory not found: {migration_dir}")
            return
            
        files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql')])
        
        if not files:
            logger.info("No migration files found")
            return
        
        logger.info(f"Found {len(files)} migration file(s)")
        
        # 3. 逐个检查并执行
        applied = 0
        skipped = 0
        
        for filename in files:
            # 检查是否已执行
            row = await conn.fetchrow(
                "SELECT version FROM schema_migrations WHERE version = $1",
                filename
            )
            
            if row:
                logger.info(f"[SKIP] {filename} (already applied)")
                skipped += 1
                continue
            
            # 读取 SQL 文件
            file_path = migration_dir / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            logger.info(f"[APPLY] {filename}...")
            
            try:
                # 在事务中执行迁移
                async with conn.transaction():
                    # asyncpg 的 execute 可以处理多语句 SQL 脚本
                    await conn.execute(sql_content)
                    
                    # 记录已执行的版本
                    await conn.execute(
                        "INSERT INTO schema_migrations (version) VALUES ($1)",
                        filename
                    )
                
                logger.info(f"[SUCCESS] {filename}")
                applied += 1
                
            except Exception as e:
                logger.error(f"[FAILED] {filename}: {e}")
                # 事务会自动回滚
                raise
        
        logger.info(f"Migration complete: {applied} applied, {skipped} skipped")
        
    finally:
        await conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    try:
        asyncio.run(run_migrations())
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Migration failed: {e}")
        sys.exit(1)

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
def load_env_file() -> dict[str, str]:
    """从 .env 文件加载环境变量"""
    env_vars = {}
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars


def get_env_var(name: str, env_file_vars: dict[str, str] | None = None) -> str:
    """获取环境变量，优先从系统环境变量，然后从 .env 文件"""
    value = os.environ.get(name, '')
    if not value and env_file_vars:
        value = env_file_vars.get(name, '')
    return value


def get_database_url():
    """从环境变量获取数据库 URL"""
    env_file_vars = load_env_file()
    return get_env_var('DATABASE_URL', env_file_vars)


def parse_dsn(sqlalchemy_url: str) -> str:
    """
    将 SQLAlchemy URL 转换为 asyncpg DSN
    postgresql+asyncpg://user:pass@host:port/db -> postgresql://user:pass@host:port/db
    """
    return re.sub(r'^postgresql\+asyncpg://', 'postgresql://', sqlalchemy_url)


def substitute_env_vars(sql_content: str, env_file_vars: dict[str, str] | None = None) -> str:
    """
    替换 SQL 中的环境变量占位符 ${VAR_NAME}
    
    支持的变量:
    - ${S3_PUBLIC_BASE_URL}: S3 公网访问基础 URL
    - ${S3_BUCKET_NAME}: S3 存储桶名称
    """
    # 查找所有 ${VAR_NAME} 格式的占位符
    pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
    
    def replace_var(match):
        var_name = match.group(1)
        value = get_env_var(var_name, env_file_vars)
        if not value:
            logger.warning(f"Environment variable {var_name} not set, placeholder will remain")
            return match.group(0)  # 保持原样
        return value
    
    return re.sub(pattern, replace_var, sql_content)


async def detect_schema_baseline(conn) -> dict[str, bool]:
    """
    检测现有数据库的 schema 状态，返回每个迁移是否已"等效执行"。
    
    这允许旧数据库（没有 schema_migrations 表）正确跳过已完成的迁移。
    """
    baseline = {}
    
    # 检测 001: chat_messages.message_time 列是否存在
    result = await conn.fetchval('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'chat_messages' AND column_name = 'message_time'
        )
    ''')
    baseline['001_add_message_time.sql'] = result
    
    # 检测 002: agents.template_id 列是否存在
    result = await conn.fetchval('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'agents' AND column_name = 'template_id'
        )
    ''')
    baseline['002_add_template_id_to_agents.sql'] = result
    
    # 检测 003: voices.category 列是否存在（voice library restructure）
    result = await conn.fetchval('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'voices' AND column_name = 'category'
        )
    ''')
    baseline['003_voice_library_restructure.sql'] = result
    
    # 检测 004: 检查是否有 minimax 类型的 library voice
    # 仅在 003 已执行（category/provider 列存在）时才检测
    if baseline.get('003_voice_library_restructure.sql', False):
        result = await conn.fetchval('''
            SELECT EXISTS (
                SELECT 1 FROM voices 
                WHERE provider = 'minimax' AND category = 'library'
                LIMIT 1
            )
        ''')
        baseline['004_insert_minimax_voices.sql'] = result
    else:
        baseline['004_insert_minimax_voices.sql'] = False
    
    # 检测 005: 检查 clone voices 是否已更新 (有 reference_id 且 voice_id 以 voice_ 开头)
    # 仅在 003 已执行时才检测
    if baseline.get('003_voice_library_restructure.sql', False):
        result = await conn.fetchval('''
            SELECT EXISTS (
                SELECT 1 FROM voices 
                WHERE category = 'clone' AND voice_id LIKE 'voice_%' AND reference_id IS NOT NULL
                LIMIT 1
            )
        ''')
        baseline['005_update_clone_voices_and_agent_refs.sql'] = result
    else:
        baseline['005_update_clone_voices_and_agent_refs.sql'] = False
    
    return baseline


async def run_migrations():
    """执行数据库迁移"""
    import asyncpg
    
    migration_dir = Path(__file__).resolve().parent.parent / "migrations"
    env_file_vars = load_env_file()
    database_url = get_env_var('DATABASE_URL', env_file_vars)
    
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
        is_new_migration_table = await conn.fetchval('''
            SELECT NOT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'schema_migrations'
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Migration tracking table ready")
        
        # 2. 如果是首次创建迁移表，检测已有 schema 并标记基线
        schema_baseline = {}
        if is_new_migration_table:
            logger.info("First-time migration setup detected, checking schema baseline...")
            schema_baseline = await detect_schema_baseline(conn)
            baseline_count = sum(1 for v in schema_baseline.values() if v)
            if baseline_count > 0:
                logger.info(f"Detected {baseline_count} migration(s) already applied to schema")
        
        # 3. 获取并排序迁移文件
        if not migration_dir.exists():
            logger.warning(f"Migration directory not found: {migration_dir}")
            return
            
        files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql')])
        
        if not files:
            logger.info("No migration files found")
            return
        
        logger.info(f"Found {len(files)} migration file(s)")
        
        # 4. 逐个检查并执行
        applied = 0
        skipped = 0
        baselined = 0
        
        for filename in files:
            # 检查是否已在 schema_migrations 表中记录
            row = await conn.fetchrow(
                "SELECT version FROM schema_migrations WHERE version = $1",
                filename
            )
            
            if row:
                logger.info(f"[SKIP] {filename} (already applied)")
                skipped += 1
                continue
            
            # 检查是否通过基线检测判定为已执行
            if schema_baseline.get(filename, False):
                # 直接标记为已执行，不再运行迁移
                await conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES ($1)",
                    filename
                )
                logger.info(f"[BASELINE] {filename} (schema already up-to-date, marked as applied)")
                baselined += 1
                continue
            
            # 读取 SQL 文件
            file_path = migration_dir / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 替换环境变量占位符 (${VAR_NAME})
            sql_content = substitute_env_vars(sql_content, env_file_vars)
            
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
        
        logger.info(f"Migration complete: {applied} applied, {skipped} skipped, {baselined} baselined")
        
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

"""
Redis client and cache utilities for live-agent-api

Shared cache with manager-api and xiaozhi-server
"""

import json
import redis.asyncio as redis
from typing import Any, Optional
from functools import wraps

from config.settings import settings


class RedisClient:
    """Async Redis client singleton"""
    
    _instance: Optional["RedisClient"] = None
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Initialize Redis connection pool"""
        if self._pool is None:
            self._pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                db=settings.REDIS_DB,
                decode_responses=True,
                max_connections=20,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            # Test connection
            await self._client.ping()
            print(f"[Redis] Connected to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client"""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> redis.Redis:
    """Dependency for getting Redis client"""
    return redis_client.client


# ==================== Cache Keys (compatible with manager-api) ====================

class CacheKeys:
    """Cache key generators (compatible with manager-api RedisKeys.java)"""
    
    # Agent config cache (for xiaozhi-server)
    @staticmethod
    def agent_config(agent_id: str) -> str:
        return f"agent:config:{agent_id}"
    
    # Voice/Timbre cache
    @staticmethod
    def timbre_name(timbre_id: str) -> str:
        return f"timbre:name:{timbre_id}"
    
    @staticmethod
    def timbre_details(timbre_id: str) -> str:
        return f"timbre:details:{timbre_id}"
    
    # Model config cache
    @staticmethod
    def model_config(model_id: str) -> str:
        return f"model:data:{model_id}"
    
    @staticmethod
    def model_name(model_id: str) -> str:
        return f"model:name:{model_id}"
    
    # User session cache
    @staticmethod
    def user_session(user_id: str) -> str:
        return f"user:session:{user_id}"
    
    # Agent template cache
    @staticmethod
    def agent_templates(user_id: str) -> str:
        return f"agent:templates:{user_id}"
    
    # Device cache
    @staticmethod
    def device_agents(device_id: str) -> str:
        return f"device:agents:{device_id}"


# ==================== Cache Utilities ====================

class Cache:
    """High-level cache utilities"""
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await redis_client.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"[Redis] Get error for key {key}: {e}")
            return None
    
    @staticmethod
    async def set(
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        try:
            ttl = ttl or settings.REDIS_DEFAULT_TTL
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await redis_client.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"[Redis] Set error for key {key}: {e}")
            return False
    
    @staticmethod
    async def delete(key: str) -> bool:
        """Delete key from cache"""
        try:
            await redis_client.client.delete(key)
            return True
        except Exception as e:
            print(f"[Redis] Delete error for key {key}: {e}")
            return False
    
    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        """Delete keys matching pattern"""
        try:
            keys = []
            async for key in redis_client.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await redis_client.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"[Redis] Delete pattern error for {pattern}: {e}")
            return 0
    
    @staticmethod
    async def exists(key: str) -> bool:
        """Check if key exists"""
        try:
            return await redis_client.client.exists(key) > 0
        except Exception:
            return False
    
    @staticmethod
    async def get_ttl(key: str) -> int:
        """Get remaining TTL of a key"""
        try:
            return await redis_client.client.ttl(key)
        except Exception:
            return -1


def cached(key_func, ttl: int = None):
    """
    Decorator for caching async function results
    
    Usage:
        @cached(lambda agent_id: CacheKeys.agent_config(agent_id), ttl=600)
        async def get_agent_config(agent_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_func(*args, **kwargs)
            
            # Try to get from cache
            cached_value = await Cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await Cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# ==================== Cache Invalidation ====================

# xiaozhi-server 使用的缓存 key 前缀
XIAOZHI_CACHE_PREFIX = "xiaozhi:"
# 缓存失效通知 channel（与 xiaozhi-server 一致）
CACHE_INVALIDATE_CHANNEL = "cache:invalidate"


async def publish_invalidation(cache_type: str, key_pattern: str) -> bool:
    """
    发布缓存失效通知（通过 Redis Pub/Sub）
    
    xiaozhi-server 订阅此 channel，收到消息后会清除 L1 本地缓存
    
    Args:
        cache_type: 缓存类型，如 "agent_config"
        key_pattern: 缓存 key 模式，如 agent_id
        
    Returns:
        是否发布成功
    """
    try:
        message = json.dumps({
            "type": cache_type,
            "key": key_pattern,
        })
        await redis_client.client.publish(CACHE_INVALIDATE_CHANNEL, message)
        print(f"[Cache Invalidation] Published: type={cache_type}, key={key_pattern}")
        return True
    except Exception as e:
        print(f"[Cache Invalidation] Failed to publish: {e}")
        return False


async def invalidate_agent_cache(agent_id: str) -> int:
    """
    使 Agent 配置缓存失效
    
    当 Agent 配置被修改时调用：
    1. 删除 Redis 中的缓存 (L2)
    2. 发布 Pub/Sub 通知，让 xiaozhi-server 清除 L1 本地缓存
    
    Args:
        agent_id: Agent ID
        
    Returns:
        删除的 Redis 缓存 key 数量
    """
    # 1. 删除 Redis 缓存 (L2)
    # xiaozhi-server 的缓存 key 格式: xiaozhi::agent_config:{agent_id}:{timezone}
    pattern = f"{XIAOZHI_CACHE_PREFIX}:agent_config:{agent_id}:*"
    deleted = await Cache.delete_pattern(pattern)
    
    if deleted > 0:
        print(f"[Cache Invalidation] Deleted {deleted} Redis cache keys for agent {agent_id}")
    
    # 2. 发布 Pub/Sub 通知，让 xiaozhi-server 清除 L1 缓存
    await publish_invalidation("agent_config", agent_id)
    
    return deleted


async def invalidate_agent_caches(agent_ids: list[str]) -> int:
    """
    批量使 Agent 配置缓存失效
    
    Args:
        agent_ids: Agent ID 列表
        
    Returns:
        删除的缓存 key 总数
    """
    total_deleted = 0
    for agent_id in agent_ids:
        deleted = await invalidate_agent_cache(agent_id)
        total_deleted += deleted
    
    return total_deleted

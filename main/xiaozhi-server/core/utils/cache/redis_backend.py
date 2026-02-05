"""
Redis 缓存后端

支持与 manager-api 和 live-agent-api 共享缓存
支持 Pub/Sub 进行跨服务缓存失效通知
"""

import json
import time
import redis
import threading
from typing import Any, Optional, Callable
from .config import CacheType


# 缓存失效通知 channel
CACHE_INVALIDATE_CHANNEL = "cache:invalidate"


class RedisCacheBackend:
    """Redis 缓存后端"""
    
    def __init__(
        self,
        host: str = "xiaozhi-esp32-server-redis",
        port: int = 6379,
        password: str = "",
        db: int = 0,
        prefix: str = "xiaozhi:"
    ):
        self.prefix = prefix
        self._client: Optional[redis.Redis] = None
        self._config = {
            "host": host,
            "port": port,
            "password": password or None,
            "db": db,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        }
        self._stats = {"hits": 0, "misses": 0}
        self._connected = False
    
    def connect(self) -> bool:
        """连接 Redis"""
        try:
            self._client = redis.Redis(**self._config)
            self._client.ping()
            self._connected = True
            print(f"[Redis Cache] Connected to {self._config['host']}:{self._config['port']}")
            return True
        except Exception as e:
            print(f"[Redis Cache] Failed to connect: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开 Redis 连接"""
        if self._client:
            self._client.close()
            self._client = None
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self._client is not None
    
    def _make_key(self, cache_type: CacheType, key: str, namespace: str = "") -> str:
        """生成 Redis key"""
        parts = [self.prefix, cache_type.value]
        if namespace:
            parts.append(namespace)
        parts.append(key)
        return ":".join(parts)
    
    def set(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        namespace: str = "",
    ) -> bool:
        """设置缓存值"""
        if not self.is_connected:
            return False
        
        try:
            redis_key = self._make_key(cache_type, key, namespace)
            serialized = json.dumps({
                "value": value,
                "timestamp": time.time(),
            }, ensure_ascii=False, default=str)
            
            if ttl:
                self._client.setex(redis_key, int(ttl), serialized)
            else:
                self._client.set(redis_key, serialized)
            return True
        except Exception as e:
            print(f"[Redis Cache] Set error for {key}: {e}")
            return False
    
    def get(
        self,
        cache_type: CacheType,
        key: str,
        namespace: str = ""
    ) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_connected:
            self._stats["misses"] += 1
            return None
        
        try:
            redis_key = self._make_key(cache_type, key, namespace)
            data = self._client.get(redis_key)
            
            if data:
                parsed = json.loads(data)
                self._stats["hits"] += 1
                return parsed.get("value")
            
            self._stats["misses"] += 1
            return None
        except Exception as e:
            print(f"[Redis Cache] Get error for {key}: {e}")
            self._stats["misses"] += 1
            return None
    
    def delete(
        self,
        cache_type: CacheType,
        key: str,
        namespace: str = ""
    ) -> bool:
        """删除缓存条目"""
        if not self.is_connected:
            return False
        
        try:
            redis_key = self._make_key(cache_type, key, namespace)
            self._client.delete(redis_key)
            return True
        except Exception as e:
            print(f"[Redis Cache] Delete error for {key}: {e}")
            return False
    
    def clear(
        self,
        cache_type: CacheType,
        namespace: str = ""
    ) -> int:
        """清空指定缓存类型"""
        if not self.is_connected:
            return 0
        
        try:
            pattern = self._make_key(cache_type, "*", namespace)
            keys = list(self._client.scan_iter(match=pattern))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            print(f"[Redis Cache] Clear error: {e}")
            return 0
    
    def invalidate_pattern(
        self,
        cache_type: CacheType,
        pattern: str,
        namespace: str = ""
    ) -> int:
        """按模式失效缓存条目"""
        if not self.is_connected:
            return 0
        
        try:
            redis_pattern = self._make_key(cache_type, f"*{pattern}*", namespace)
            keys = list(self._client.scan_iter(match=redis_pattern))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            print(f"[Redis Cache] Invalidate pattern error: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        return {
            "backend": "redis",
            "connected": self.is_connected,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2%}",
        }
    
    # ==================== Pub/Sub 订阅（缓存失效通知） ====================
    
    def subscribe_invalidation(self, callback: Callable[[str, str], None]) -> bool:
        """
        订阅缓存失效通知
        
        Args:
            callback: 回调函数，参数为 (cache_type, key_pattern)
                      例如: callback("agent_config", "agent_xxx")
        
        Returns:
            是否成功启动订阅
        """
        if not self.is_connected:
            return False
        
        def subscriber_thread():
            try:
                # 创建独立的 Redis 连接用于订阅
                sub_client = redis.Redis(**self._config)
                pubsub = sub_client.pubsub()
                pubsub.subscribe(CACHE_INVALIDATE_CHANNEL)
                
                print(f"[Redis Pub/Sub] Subscribed to channel: {CACHE_INVALIDATE_CHANNEL}")
                
                for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            cache_type = data.get("type", "")
                            key_pattern = data.get("key", "")
                            
                            if cache_type and key_pattern:
                                print(f"[Redis Pub/Sub] Received invalidation: type={cache_type}, key={key_pattern}")
                                callback(cache_type, key_pattern)
                        except json.JSONDecodeError:
                            print(f"[Redis Pub/Sub] Invalid message format: {message['data']}")
                        except Exception as e:
                            print(f"[Redis Pub/Sub] Callback error: {e}")
            except Exception as e:
                print(f"[Redis Pub/Sub] Subscriber error: {e}")
        
        # 启动订阅线程（daemon=True 保证主进程退出时自动终止）
        thread = threading.Thread(target=subscriber_thread, daemon=True)
        thread.start()
        return True


# 全局 Redis 缓存后端实例
redis_cache_backend: Optional[RedisCacheBackend] = None


def init_redis_cache(
    host: str = "xiaozhi-esp32-server-redis",
    port: int = 6379,
    password: str = "",
    db: int = 0
) -> bool:
    """初始化 Redis 缓存"""
    global redis_cache_backend
    redis_cache_backend = RedisCacheBackend(
        host=host,
        port=port,
        password=password,
        db=db,
    )
    return redis_cache_backend.connect()


def get_redis_cache() -> Optional[RedisCacheBackend]:
    """获取 Redis 缓存后端"""
    return redis_cache_backend

"""
全局缓存管理器

支持分层缓存架构：
1. L1 本地内存缓存 - 进程内，速度最快 (<0.1ms)，短 TTL (30s)
2. L2 Redis 缓存 - 跨进程共享，与 manager-api、live-agent-api 统一

读取流程: L1 -> L2 -> 数据源
写入流程: 同时写 L1 和 L2
"""

import time
import threading
from typing import Any, Optional, Dict
from collections import OrderedDict
from dataclasses import dataclass
from .strategies import CacheStrategy, CacheEntry
from .config import CacheConfig, CacheType


@dataclass
class L1CacheEntry:
    """L1 本地缓存条目"""
    value: Any
    expire_at: float  # 过期时间戳
    
    def is_expired(self) -> bool:
        return time.time() > self.expire_at


class GlobalCacheManager:
    """全局缓存管理器 - 支持 L1/L2 分层缓存"""

    # L1 本地缓存默认 TTL (秒)
    L1_DEFAULT_TTL = 30
    # L1 缓存最大条目数
    L1_MAX_SIZE = 1000
    # L1 清理间隔 (秒)
    L1_CLEANUP_INTERVAL = 60

    def __init__(self, use_redis: bool = False):
        self._logger = None
        self._use_redis = use_redis
        self._redis_backend = None
        
        # L1 本地内存缓存 (分层缓存的第一层)
        self._l1_cache: Dict[str, L1CacheEntry] = {}
        self._l1_lock = threading.RLock()
        self._l1_last_cleanup = time.time()
        self._l1_stats = {"hits": 0, "misses": 0, "backfills": 0}
        
        # L2 内存缓存（当 Redis 不可用时作为备选）
        self._caches: Dict[str, Dict[str, CacheEntry]] = {}
        self._configs: Dict[str, CacheConfig] = {}
        self._locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()
        self._last_cleanup = time.time()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "cleanups": 0}
    
    def enable_redis(
        self,
        host: str = "xiaozhi-esp32-server-redis",
        port: int = 6379,
        password: str = "",
        db: int = 0
    ) -> bool:
        """启用 Redis 缓存后端 (L2)"""
        try:
            from .redis_backend import RedisCacheBackend
            self._redis_backend = RedisCacheBackend(
                host=host,
                port=port,
                password=password,
                db=db,
            )
            if self._redis_backend.connect():
                self._use_redis = True
                self.logger.info(f"[缓存] L2 Redis 后端已启用: {host}:{port}")
                self.logger.info(f"[缓存] L1 本地缓存已启用: TTL={self.L1_DEFAULT_TTL}s, MaxSize={self.L1_MAX_SIZE}")
                
                # 启用 Pub/Sub 订阅缓存失效通知
                self._start_invalidation_subscriber()
                
                return True
            else:
                self.logger.warning("[缓存] Redis 连接失败，使用纯内存缓存")
                self._use_redis = False
                return False
        except Exception as e:
            self.logger.warning(f"[缓存] Redis 初始化失败: {e}，使用纯内存缓存")
            self._use_redis = False
            return False
    
    def _start_invalidation_subscriber(self):
        """启动缓存失效订阅"""
        if not self._redis_backend:
            return
        
        def on_invalidation(cache_type: str, key_pattern: str):
            """收到缓存失效通知时的回调"""
            # 清除 L1 本地缓存
            if cache_type == "agent_config":
                # key_pattern 是 agent_id，清除该 agent 的所有缓存
                deleted = self._l1_invalidate_pattern(CacheType.AGENT_CONFIG, key_pattern)
                self.logger.info(f"[L1缓存] 收到失效通知，清除 {deleted} 条 agent_config 缓存: {key_pattern}")
            else:
                self.logger.debug(f"[L1缓存] 忽略未知缓存类型的失效通知: {cache_type}")
        
        if self._redis_backend.subscribe_invalidation(on_invalidation):
            self.logger.info("[缓存] 已订阅 Redis Pub/Sub 缓存失效通知")
    
    def disable_redis(self):
        """禁用 Redis 缓存后端"""
        if self._redis_backend:
            self._redis_backend.disconnect()
            self._redis_backend = None
        self._use_redis = False
        self.logger.info("[缓存] Redis 后端已禁用，切换到纯内存缓存")

    @property
    def logger(self):
        """延迟初始化 logger 以避免循环导入"""
        if self._logger is None:
            from config.logger import setup_logging
            self._logger = setup_logging()
        return self._logger

    # ==================== L1 本地缓存操作 ====================
    
    def _l1_key(self, cache_type: CacheType, key: str, namespace: str = "") -> str:
        """生成 L1 缓存键"""
        if namespace:
            return f"{cache_type.value}:{namespace}:{key}"
        return f"{cache_type.value}:{key}"
    
    def _l1_get(self, cache_type: CacheType, key: str, namespace: str = "") -> Optional[Any]:
        """从 L1 本地缓存获取"""
        l1_key = self._l1_key(cache_type, key, namespace)
        
        with self._l1_lock:
            entry = self._l1_cache.get(l1_key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._l1_cache[l1_key]
                return None
            
            return entry.value
    
    def _l1_set(self, cache_type: CacheType, key: str, value: Any, namespace: str = "", ttl: float = None) -> None:
        """写入 L1 本地缓存"""
        l1_key = self._l1_key(cache_type, key, namespace)
        effective_ttl = ttl if ttl is not None else self.L1_DEFAULT_TTL
        
        with self._l1_lock:
            # 检查容量限制
            if len(self._l1_cache) >= self.L1_MAX_SIZE:
                self._l1_cleanup_expired()
                # 如果清理后仍超限，删除最旧的条目
                if len(self._l1_cache) >= self.L1_MAX_SIZE:
                    oldest_key = next(iter(self._l1_cache))
                    del self._l1_cache[oldest_key]
            
            self._l1_cache[l1_key] = L1CacheEntry(
                value=value,
                expire_at=time.time() + effective_ttl
            )
        
        # 定期清理
        self._l1_maybe_cleanup()
    
    def _l1_delete(self, cache_type: CacheType, key: str, namespace: str = "") -> bool:
        """从 L1 本地缓存删除"""
        l1_key = self._l1_key(cache_type, key, namespace)
        
        with self._l1_lock:
            if l1_key in self._l1_cache:
                del self._l1_cache[l1_key]
                return True
            return False
    
    def _l1_cleanup_expired(self) -> int:
        """清理 L1 过期条目（需要在持有锁的情况下调用）"""
        expired_keys = [k for k, v in self._l1_cache.items() if v.is_expired()]
        for k in expired_keys:
            del self._l1_cache[k]
        return len(expired_keys)
    
    def _l1_maybe_cleanup(self):
        """定期清理 L1 缓存"""
        now = time.time()
        if now - self._l1_last_cleanup > self.L1_CLEANUP_INTERVAL:
            self._l1_last_cleanup = now
            with self._l1_lock:
                deleted = self._l1_cleanup_expired()
                if deleted > 0:
                    self.logger.debug(f"[L1缓存] 清理 {deleted} 个过期条目，当前 {len(self._l1_cache)} 条")
    
    def _l1_invalidate_pattern(self, cache_type: CacheType, pattern: str, namespace: str = "") -> int:
        """按模式失效 L1 缓存条目"""
        prefix = f"{cache_type.value}:"
        if namespace:
            prefix = f"{cache_type.value}:{namespace}:"
        
        with self._l1_lock:
            keys_to_delete = [k for k in self._l1_cache.keys() if k.startswith(prefix) and pattern in k]
            for k in keys_to_delete:
                del self._l1_cache[k]
            return len(keys_to_delete)

    # ==================== L2 内存缓存操作（备选） ====================

    def _get_cache_name(self, cache_type: CacheType, namespace: str = "") -> str:
        """生成缓存名称"""
        if namespace:
            return f"{cache_type.value}:{namespace}"
        return cache_type.value

    def _get_or_create_cache(
        self, cache_name: str, config: CacheConfig
    ) -> Dict[str, CacheEntry]:
        """获取或创建缓存空间"""
        with self._global_lock:
            if cache_name not in self._caches:
                self._caches[cache_name] = (
                    OrderedDict()
                    if config.strategy in [CacheStrategy.LRU, CacheStrategy.TTL_LRU]
                    else {}
                )
                self._configs[cache_name] = config
                self._locks[cache_name] = threading.RLock()
            return self._caches[cache_name]

    # ==================== 公共接口（分层缓存逻辑） ====================

    def set(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        namespace: str = "",
    ) -> None:
        """设置缓存值（同时写入 L1 和 L2）"""
        config = CacheConfig.for_type(cache_type)
        effective_ttl = ttl if ttl is not None else config.ttl
        
        # 写入 L1 本地缓存（使用较短的 TTL）
        l1_ttl = min(self.L1_DEFAULT_TTL, effective_ttl) if effective_ttl else self.L1_DEFAULT_TTL
        self._l1_set(cache_type, key, value, namespace, l1_ttl)
        
        # 写入 L2 (Redis 或内存)
        if self._use_redis and self._redis_backend and self._redis_backend.is_connected:
            self._redis_backend.set(cache_type, key, value, effective_ttl, namespace)
        else:
            # 回退到内存缓存
            self._set_memory(cache_type, key, value, effective_ttl, namespace, config)

    def _set_memory(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: Optional[float],
        namespace: str,
        config: CacheConfig,
    ) -> None:
        """写入 L2 内存缓存"""
        cache_name = self._get_cache_name(cache_type, namespace)
        cache = self._get_or_create_cache(cache_name, config)

        with self._locks[cache_name]:
            entry = CacheEntry(value=value, timestamp=time.time(), ttl=ttl)

            if config.strategy in [CacheStrategy.LRU, CacheStrategy.TTL_LRU]:
                if key in cache:
                    del cache[key]
                cache[key] = entry

                if config.max_size and len(cache) > config.max_size:
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
                    self._stats["evictions"] += 1
            else:
                cache[key] = entry

                if config.max_size and len(cache) > config.max_size:
                    victim_key = next(iter(cache))
                    del cache[victim_key]
                    self._stats["evictions"] += 1

        self._maybe_cleanup(cache_name)

    def get(
        self, cache_type: CacheType, key: str, namespace: str = ""
    ) -> Optional[Any]:
        """获取缓存值（L1 -> L2 分层查询）"""
        
        # 1. 先查 L1 本地缓存
        l1_value = self._l1_get(cache_type, key, namespace)
        if l1_value is not None:
            self._l1_stats["hits"] += 1
            return l1_value
        self._l1_stats["misses"] += 1
        
        # 2. L1 未命中，查 L2 (Redis 或内存)
        if self._use_redis and self._redis_backend and self._redis_backend.is_connected:
            result = self._redis_backend.get(cache_type, key, namespace)
            if result is not None:
                self._stats["hits"] += 1
                # 回填 L1
                self._l1_set(cache_type, key, result, namespace)
                self._l1_stats["backfills"] += 1
                return result
            self._stats["misses"] += 1
            return None
        
        # 回退到内存缓存
        return self._get_memory(cache_type, key, namespace)
    
    def _get_memory(
        self, cache_type: CacheType, key: str, namespace: str = ""
    ) -> Optional[Any]:
        """从 L2 内存缓存获取"""
        cache_name = self._get_cache_name(cache_type, namespace)

        if cache_name not in self._caches:
            self._stats["misses"] += 1
            return None

        cache = self._caches[cache_name]
        config = self._configs[cache_name]

        with self._locks[cache_name]:
            if key not in cache:
                self._stats["misses"] += 1
                return None

            entry = cache[key]

            if entry.is_expired():
                del cache[key]
                self._stats["misses"] += 1
                return None

            entry.touch()

            if config.strategy in [CacheStrategy.LRU, CacheStrategy.TTL_LRU]:
                del cache[key]
                cache[key] = entry

            self._stats["hits"] += 1
            return entry.value

    def delete(self, cache_type: CacheType, key: str, namespace: str = "") -> bool:
        """删除缓存条目（同时删除 L1 和 L2）"""
        # 删除 L1
        self._l1_delete(cache_type, key, namespace)
        
        # 删除 L2
        if self._use_redis and self._redis_backend and self._redis_backend.is_connected:
            return self._redis_backend.delete(cache_type, key, namespace)
        
        # 回退到内存缓存
        cache_name = self._get_cache_name(cache_type, namespace)

        if cache_name not in self._caches:
            return False

        cache = self._caches[cache_name]

        with self._locks[cache_name]:
            if key in cache:
                del cache[key]
                return True
            return False

    def clear(self, cache_type: CacheType, namespace: str = "") -> None:
        """清空指定缓存（同时清空 L1 和 L2）"""
        # 清空 L1 中对应类型的缓存
        prefix = f"{cache_type.value}:"
        if namespace:
            prefix = f"{cache_type.value}:{namespace}:"
        
        with self._l1_lock:
            keys_to_delete = [k for k in self._l1_cache.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._l1_cache[k]
        
        # 清空 L2
        if self._use_redis and self._redis_backend and self._redis_backend.is_connected:
            self._redis_backend.clear(cache_type, namespace)
            return
        
        # 回退到内存缓存
        cache_name = self._get_cache_name(cache_type, namespace)

        if cache_name not in self._caches:
            return

        with self._locks[cache_name]:
            self._caches[cache_name].clear()

    def invalidate_pattern(
        self, cache_type: CacheType, pattern: str, namespace: str = ""
    ) -> int:
        """按模式失效缓存条目（同时失效 L1 和 L2）"""
        # 失效 L1
        l1_deleted = self._l1_invalidate_pattern(cache_type, pattern, namespace)
        
        # 失效 L2
        if self._use_redis and self._redis_backend and self._redis_backend.is_connected:
            l2_deleted = self._redis_backend.invalidate_pattern(cache_type, pattern, namespace)
            return l1_deleted + l2_deleted
        
        # 回退到内存缓存
        cache_name = self._get_cache_name(cache_type, namespace)

        if cache_name not in self._caches:
            return l1_deleted

        cache = self._caches[cache_name]
        deleted_count = 0

        with self._locks[cache_name]:
            keys_to_delete = [key for key in cache.keys() if pattern in key]
            for key in keys_to_delete:
                del cache[key]
                deleted_count += 1

        return l1_deleted + deleted_count

    def _cleanup_expired(self, cache_name: str) -> int:
        """清理过期条目"""
        if cache_name not in self._caches:
            return 0

        cache = self._caches[cache_name]
        deleted_count = 0

        with self._locks[cache_name]:
            expired_keys = [key for key, entry in cache.items() if entry.is_expired()]
            for key in expired_keys:
                del cache[key]
                deleted_count += 1

        return deleted_count

    def _maybe_cleanup(self, cache_name: str):
        """定期清理检查"""
        config = self._configs.get(cache_name)
        if not config:
            return

        now = time.time()
        if now - self._last_cleanup > config.cleanup_interval:
            self._last_cleanup = now
            deleted = self._cleanup_expired(cache_name)
            if deleted > 0:
                self._stats["cleanups"] += 1
                self.logger.debug(f"清理缓存 {cache_name}: 删除 {deleted} 个过期条目")

    # ==================== 统计信息 ====================
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        return {
            "l1": {
                "hits": self._l1_stats["hits"],
                "misses": self._l1_stats["misses"],
                "backfills": self._l1_stats["backfills"],
                "size": len(self._l1_cache),
                "hit_rate": self._l1_stats["hits"] / max(1, self._l1_stats["hits"] + self._l1_stats["misses"]),
            },
            "l2": {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "cleanups": self._stats["cleanups"],
            },
            "redis_enabled": self._use_redis,
        }


# 创建全局缓存管理器实例
cache_manager = GlobalCacheManager()

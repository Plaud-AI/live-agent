"""
Live Agent API Client - Singleton HTTP client for live-agent-api

Features:
1. Singleton pattern ensures global unique httpx.Client instance
2. Connection pool reuse for better performance
3. Thread-safe for concurrent requests
4. JWT token parsing for user_id extraction
5. Agent config caching for reduced latency (TTL=60s)
"""

import os
import httpx
import jwt
from config.logger import setup_logging
from typing import Optional, List, Dict
from core.utils.cache.manager import cache_manager
from core.utils.cache.config import CacheType

logger = setup_logging()

# 缓存 TTL 常量（秒）
AGENT_CONFIG_CACHE_TTL = 600


class LiveAgentApiClient:
    """Singleton HTTP client for live-agent-api"""
    _instance = None
    _client: httpx.Client = None
    _base_url: str = None
    _secret_key: str = None  # JWT secret key for token parsing
    
    def __new__(cls, config: dict = None):
        """Singleton pattern ensures global unique instance"""
        if cls._instance is None:
            if config is None:
                raise ValueError("Config required for first initialization")
            cls._instance = super().__new__(cls)
            cls._init_client(config)
        return cls._instance
    
    @classmethod
    def _init_client(cls, config: dict):
        """Initialize persistent connection pool"""
        live_api_config = config.get("live-agent-api", {})
        cls._base_url = live_api_config.get("url", "http://live-agent-api:8080/api/live_agent/v1")
        cls._secret_key = live_api_config.get("secret_key")
        timeout = live_api_config.get("timeout", 30)
        
        cls._client = httpx.Client(
            base_url=cls._base_url,
            headers={
                "User-Agent": f"XiaozhiServer/1.0 (PID:{os.getpid()})",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
        logger.info(f"LiveAgentApiClient initialized: {cls._base_url}")
        if cls._secret_key:
            logger.info("JWT secret_key configured for user_id extraction")
    
    @classmethod
    def _request(cls, method: str, endpoint: str, **kwargs) -> dict:
        """Send HTTP request and handle response"""
        endpoint = endpoint.lstrip("/")
        response = cls._client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
    
    @classmethod
    def safe_close(cls):
        """Safely close connection pool"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._instance = None
            logger.info("LiveAgentApiClient closed")


def init_live_agent_api(config: dict):
    """Initialize the singleton client (call once at startup)"""
    LiveAgentApiClient(config)


def get_agent_config_from_api(agent_id: str, config: dict = None, timezone: str = "UTC+0") -> Optional[dict]:
    """
    Get agent configuration from live-agent-api (无缓存，直接调用 API)
    
    Args:
        agent_id: Agent ID
        config: System config (optional if client already initialized)
        timezone: Timezone string
    
    Returns:
        Agent config dict or None if failed
    """
    try:
        # Ensure client is initialized
        if LiveAgentApiClient._instance is None:
            if config is None:
                logger.error("LiveAgentApiClient not initialized and no config provided")
                return None
            LiveAgentApiClient(config)
        
        result = LiveAgentApiClient._request("GET", 
            f"/internal/agents/{agent_id}/config",
            params={"timezone": timezone}
        )
        
        if result.get("code") == 200 and "data" in result:
            logger.info(f"Successfully fetched agent config for agent_id={agent_id}")
            return result["data"]
        else:
            logger.error(f"Invalid response format from live-agent-api: {result}")
            return None
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(f"Agent not found: agent_id={agent_id}")
        else:
            logger.error(f"HTTP error fetching agent config: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch agent config for {agent_id}: {e}")
        return None


def get_agent_config_cached(agent_id: str, config: dict = None, timezone: str = "UTC+0") -> Optional[dict]:
    """
    Get agent configuration with caching (推荐使用)
    
    缓存策略:
    - TTL: 60秒（配置更新最多延迟 60 秒生效）
    - 缓存键: agent_id:timezone
    - API 返回 None 时不缓存（避免缓存穿透）
    
    Args:
        agent_id: Agent ID
        config: System config (optional if client already initialized)
        timezone: Timezone string
    
    Returns:
        Agent config dict or None if failed
    """
    cache_key = f"{agent_id}:{timezone}"
    
    # 尝试从缓存获取
    cached = cache_manager.get(CacheType.AGENT_CONFIG, cache_key)
    if cached is not None:
        logger.debug(f"Agent config cache hit: {cache_key}")
        return cached
    
    # 缓存未命中，调用 API
    logger.debug(f"Agent config cache miss: {cache_key}")
    result = get_agent_config_from_api(agent_id, config, timezone)
    
    # 只缓存成功的结果（避免缓存穿透）
    if result is not None:
        cache_manager.set(
            CacheType.AGENT_CONFIG, 
            cache_key, 
            result, 
            ttl=AGENT_CONFIG_CACHE_TTL
        )
        logger.debug(f"Agent config cached: {cache_key}, TTL={AGENT_CONFIG_CACHE_TTL}s")
    
    return result


def get_agent_by_wake_from_api(
    device_id: str,
    wake_word: str | None = None,
    config: dict = None,
) -> Optional[dict]:
    """
    Resolve agent for device by wake word; fallback to default binding. (无缓存)
    """
    try:
        if LiveAgentApiClient._instance is None:
            if config is None:
                logger.error("LiveAgentApiClient not initialized and no config provided")
                return None
            LiveAgentApiClient(config)

        params = {}
        if wake_word:
            params["wake_word"] = wake_word
        result = LiveAgentApiClient._request(
            "GET", f"/internal/devices/{device_id}/agent-by-wake", params=params
        )

        if result.get("code") == 200 and "data" in result:
            logger.info(
                f"Successfully resolved agent by wake_word for device_id={device_id}"
            )
            return result["data"]
        else:
            logger.error(f"Invalid response for agent-by-wake: {result}")
            return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error resolving agent by wake_word: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to resolve agent by wake_word for {device_id}: {e}")
        return None


def get_agent_by_wake_cached(
    device_id: str,
    wake_word: str | None = None,
    config: dict = None,
) -> Optional[dict]:
    """
    Resolve agent for device by wake word with caching (推荐使用)
    
    缓存策略:
    - TTL: 60秒
    - 缓存键: wake:{device_id}:{wake_word} 或 wake:{device_id}:__default__
    
    Args:
        device_id: Device ID (MAC address)
        wake_word: Wake word text (optional)
        config: System config
    
    Returns:
        Agent binding dict or None if failed
    """
    # 构建缓存键
    wake_key = wake_word if wake_word else "__default__"
    cache_key = f"wake:{device_id}:{wake_key}"
    
    # 尝试从缓存获取
    cached = cache_manager.get(CacheType.AGENT_CONFIG, cache_key)
    if cached is not None:
        logger.debug(f"Agent by wake cache hit: {cache_key}")
        return cached
    
    # 缓存未命中，调用 API
    logger.debug(f"Agent by wake cache miss: {cache_key}")
    result = get_agent_by_wake_from_api(device_id, wake_word, config)
    
    # 只缓存成功的结果
    if result is not None:
        cache_manager.set(
            CacheType.AGENT_CONFIG, 
            cache_key, 
            result, 
            ttl=AGENT_CONFIG_CACHE_TTL
        )
        logger.debug(f"Agent by wake cached: {cache_key}, TTL={AGENT_CONFIG_CACHE_TTL}s")
    
    return result


def invalidate_agent_config_cache(agent_id: str = None, device_id: str = None) -> int:
    """
    手动失效 Agent 配置缓存
    
    适用场景：用户在 App 端更新了 Agent 配置后，主动调用此函数清除缓存
    
    Args:
        agent_id: 失效指定 agent 的所有缓存
        device_id: 失效指定设备的唤醒词绑定缓存
    
    Returns:
        删除的缓存条目数
    """
    total_deleted = 0
    
    if agent_id:
        deleted = cache_manager.invalidate_pattern(CacheType.AGENT_CONFIG, agent_id)
        total_deleted += deleted
        logger.info(f"Invalidated {deleted} cache entries for agent_id={agent_id}")
    
    if device_id:
        deleted = cache_manager.invalidate_pattern(CacheType.AGENT_CONFIG, f"wake:{device_id}")
        total_deleted += deleted
        logger.info(f"Invalidated {deleted} cache entries for device_id={device_id}")
    
    return total_deleted


def report_chat_message(
    agent_id: str,
    role: int,
    content_items: List[Dict[str, str]],
    message_time: int = None,
    config: dict = None
) -> Optional[dict]:
    """
    Report chat message to live-agent-api
    
    Args:
        agent_id: Agent ID
        role: 1=user, 2=agent
        content_items: List of message parts, format:
            [
                {"message_type": "text", "message_content": "Hello"},
                {"message_type": "audio", "message_content": "base64_opus_data"},
                {"message_type": "image", "message_content": "s3_url"},
                {"message_type": "file", "message_content": "s3_url"}
            ]
        message_time: Unix timestamp when message actually occurred (for correct ordering)
        config: System config (optional if client already initialized)
    
    Returns:
        Response dict or None if failed
    """
    try:
        # Ensure client is initialized
        if LiveAgentApiClient._instance is None:
            if config is None:
                logger.error("LiveAgentApiClient not initialized and no config provided")
                return None
            LiveAgentApiClient(config)
        
        payload = {
            "agent_id": agent_id,
            "role": role,
            "content": content_items
        }
        
        # Add message_time if provided (for correct message ordering)
        if message_time is not None:
            payload["message_time"] = message_time
        
        result = LiveAgentApiClient._request("POST", "/chat/report", json=payload)
        
        if result.get("code") == 200:
            logger.debug(f"Successfully reported message for agent_id={agent_id}, role={role}")
            return result.get("data")
        else:
            logger.error(f"Failed to report message: {result}")
            return None
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error reporting message: {e}, response: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Failed to report message for {agent_id}: {e}")
        return None


def live_agent_api_safe_close():
    """Safe close for shutdown"""
    LiveAgentApiClient.safe_close()


def extract_user_id_from_jwt(token: str, config: dict = None) -> Optional[str]:
    """
    Extract user_id from live-agent-api JWT token.
    
    This allows xiaozhi-server to identify the user from the Bearer token
    passed by the App, enabling proper memory initialization with user_id.
    
    Args:
        token: JWT token string (with or without 'Bearer ' prefix)
        config: System config (optional if client already initialized)
    
    Returns:
        user_id string if extraction successful, None otherwise
    """
    try:
        # Ensure client is initialized to get secret_key
        if LiveAgentApiClient._instance is None:
            if config is None:
                logger.warning("LiveAgentApiClient not initialized, cannot extract user_id from JWT")
                return None
            LiveAgentApiClient(config)
        
        secret_key = LiveAgentApiClient._secret_key
        if not secret_key:
            logger.debug("No secret_key configured, skipping JWT user_id extraction")
            return None
        
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Decode JWT token
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if user_id:
            logger.debug(f"Successfully extracted user_id from JWT: {user_id[:20]}...")
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token expired, cannot extract user_id")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to extract user_id from JWT: {e}")
        return None

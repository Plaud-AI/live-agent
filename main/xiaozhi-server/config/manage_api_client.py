import os
import base64
from typing import Optional, Dict

import httpx

TAG = __name__


class DeviceNotFoundException(Exception):
    pass


class DeviceBindException(Exception):
    def __init__(self, bind_code):
        self.bind_code = bind_code
        super().__init__(f"设备绑定异常，绑定码: {bind_code}")


class ManageApiClient:
    _instance = None
    _async_clients = {}  # 为每个事件循环存储独立的客户端
    _secret = None

    def __new__(cls, config):
        """单例模式确保全局唯一实例，并支持传入配置参数"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._init_client(config)
        return cls._instance

    @classmethod
    def _init_client(cls, config):
        """初始化配置（延迟创建客户端）"""
        cls.config = config.get("manager-api")

        if not cls.config:
            raise Exception("manager-api配置错误")

        if not cls.config.get("url") or not cls.config.get("secret"):
            raise Exception("manager-api的url或secret配置错误")

        if "你" in cls.config.get("secret"):
            raise Exception("请先配置manager-api的secret")

        cls._secret = cls.config.get("secret")
        cls.max_retries = cls.config.get("max_retries", 6)  # 最大重试次数
        cls.retry_delay = cls.config.get("retry_delay", 10)  # 初始重试延迟(秒)
        # 不在这里创建 AsyncClient，延迟到实际使用时创建
        cls._async_clients = {}

    @classmethod
    async def _ensure_async_client(cls):
        """确保异步客户端已创建（为每个事件循环创建独立的客户端）"""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)

            # 为每个事件循环创建独立的客户端
            if loop_id not in cls._async_clients:
                cls._async_clients[loop_id] = httpx.AsyncClient(
                    base_url=cls.config.get("url"),
                    headers={
                        "User-Agent": f"PythonClient/2.0 (PID:{os.getpid()})",
                        "Accept": "application/json",
                        "Authorization": "Bearer " + cls._secret,
                    },
                    timeout=cls.config.get("timeout", 30),
                )
            return cls._async_clients[loop_id]
        except RuntimeError:
            # 如果没有运行中的事件循环，创建一个临时的
            raise Exception("必须在异步上下文中调用")

    @classmethod
    async def _async_request(cls, method: str, endpoint: str, **kwargs) -> Dict:
        """发送单次异步HTTP请求并处理响应"""
        # 确保客户端已创建
        client = await cls._ensure_async_client()
        endpoint = endpoint.lstrip("/")
        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()

        result = response.json()

        # 处理API返回的业务错误
        if result.get("code") == 10041:
            raise DeviceNotFoundException(result.get("msg"))
        elif result.get("code") == 10042:
            raise DeviceBindException(result.get("msg"))
        elif result.get("code") != 0:
            raise Exception(f"API返回错误: {result.get('msg', '未知错误')}")

        # 返回成功数据
        return result.get("data") if result.get("code") == 0 else None

    @classmethod
    def _should_retry(cls, exception: Exception) -> bool:
        """判断异常是否应该重试"""
        # 网络连接相关错误
        if isinstance(
            exception, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
        ):
            return True

        # HTTP状态码错误
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            return status_code in [408, 429, 500, 502, 503, 504]

        return False

    @classmethod
    async def _execute_async_request(cls, method: str, endpoint: str, **kwargs) -> Dict:
        """带重试机制的异步请求执行器"""
        import asyncio

        retry_count = 0

        while retry_count <= cls.max_retries:
            try:
                # 执行异步请求
                return await cls._async_request(method, endpoint, **kwargs)
            except Exception as e:
                # 判断是否应该重试
                if retry_count < cls.max_retries and cls._should_retry(e):
                    retry_count += 1
                    print(
                        f"{method} {endpoint} 异步请求失败，将在 {cls.retry_delay:.1f} 秒后进行第 {retry_count} 次重试"
                    )
                    await asyncio.sleep(cls.retry_delay)
                    continue
                else:
                    # 不重试，直接抛出异常
                    raise

    @classmethod
    def safe_close(cls):
        """安全关闭所有异步连接池"""
        import asyncio

        for client in list(cls._async_clients.values()):
            try:
                asyncio.run(client.aclose())
            except Exception:
                pass
        cls._async_clients.clear()
        cls._instance = None


async def get_server_config() -> Optional[Dict]:
    """获取服务器基础配置"""
    return await ManageApiClient._instance._execute_async_request(
        "POST", "/config/server-base"
    )


async def get_agent_models(
    mac_address: str, client_id: str, selected_module: Dict
) -> Optional[Dict]:
    """获取代理模型配置"""
    return await ManageApiClient._instance._execute_async_request(
        "POST",
        "/config/agent-models",
        json={
            "macAddress": mac_address,
            "clientId": client_id,
            "selectedModule": selected_module,
        },
    )


async def generate_and_save_chat_summary(session_id: str) -> Optional[Dict]:
    """生成并保存聊天记录总结"""
    try:
        return await ManageApiClient._instance._execute_async_request(
            "POST",
            f"/agent/chat-summary/{session_id}/save",
        )
    except Exception as e:
        print(f"生成并保存聊天记录总结失败: {e}")
        return None


async def get_agent_config_by_id(agent_id: str, use_cache: bool = True) -> Optional[Dict]:
    """
    根据智能体ID获取完整配置（带缓存）
    
    用于移动端连接时，根据 agent_id 从 manager-api 获取 LLM、TTS 等完整配置
    
    Args:
        agent_id: 智能体ID
        use_cache: 是否使用缓存，默认 True
    
    Returns:
        包含 selected_module、LLM、TTS、ASR 等所有模块配置的字典
    """
    from core.utils.cache.manager import cache_manager
    from core.utils.cache.config import CacheType
    
    if not ManageApiClient._instance:
        return None
    
    cache_key = f"agent:{agent_id}"
    
    # 尝试从缓存获取
    if use_cache:
        cached = cache_manager.get(CacheType.AGENT_CONFIG, cache_key)
        if cached is not None:
            print(f"[缓存命中] agent_id={agent_id}")
            return cached
    
    # 缓存未命中，从 API 获取
    try:
        config = await ManageApiClient._instance._execute_async_request(
            "GET",
            f"/config/internal/agent/{agent_id}/config",
        )
        
        # 存入缓存
        if config:
            cache_manager.set(CacheType.AGENT_CONFIG, cache_key, config)
            print(f"[缓存写入] agent_id={agent_id}")
        
        return config
    except Exception as e:
        print(f"获取智能体配置失败: {e}")
        return None


async def warmup_agent_config(agent_id: str) -> bool:
    """
    预热单个 agent 配置缓存
    
    在用户登录后或设备绑定后调用，提前加载配置到缓存
    
    Args:
        agent_id: 智能体ID
    
    Returns:
        预热是否成功
    """
    config = await get_agent_config_by_id(agent_id, use_cache=False)
    return config is not None


async def warmup_user_agents(user_id: int) -> int:
    """
    批量预热用户所有 agent 配置（需要 manager-api 支持批量接口）
    
    Args:
        user_id: 用户ID
    
    Returns:
        成功预热的 agent 数量
    """
    if not ManageApiClient._instance:
        return 0
    
    try:
        # 获取用户所有 agent 配置
        result = await ManageApiClient._instance._execute_async_request(
            "GET",
            f"/config/internal/user/{user_id}/agents",
        )
        
        if not result or not isinstance(result, list):
            return 0
        
        from core.utils.cache.manager import cache_manager
        from core.utils.cache.config import CacheType
        
        count = 0
        for agent_config in result:
            agent_id = agent_config.get("agent_id")
            if agent_id:
                cache_key = f"agent:{agent_id}"
                cache_manager.set(CacheType.AGENT_CONFIG, cache_key, agent_config)
                count += 1
        
        print(f"[批量预热] user_id={user_id}, 预热 {count} 个 agent 配置")
        return count
    except Exception as e:
        print(f"批量预热用户 agent 配置失败: {e}")
        return 0


def invalidate_agent_config_cache(agent_id: str) -> bool:
    """
    使指定 agent 的缓存失效
    
    当 agent 配置被修改时调用
    
    Args:
        agent_id: 智能体ID
    
    Returns:
        是否成功删除缓存
    """
    from core.utils.cache.manager import cache_manager
    from core.utils.cache.config import CacheType
    
    cache_key = f"agent:{agent_id}"
    return cache_manager.delete(CacheType.AGENT_CONFIG, cache_key)


async def report(
    mac_address: str, session_id: str, chat_type: int, content: str, audio, report_time
) -> Optional[Dict]:
    """异步聊天记录上报"""
    if not content or not ManageApiClient._instance:
        return None
    try:
        return await ManageApiClient._instance._execute_async_request(
            "POST",
            f"/agent/chat-history/report",
            json={
                "macAddress": mac_address,
                "sessionId": session_id,
                "chatType": chat_type,
                "content": content,
                "reportTime": report_time,
                "audioBase64": (
                    base64.b64encode(audio).decode("utf-8") if audio else None
                ),
            },
        )
    except Exception as e:
        print(f"TTS上报失败: {e}")
        return None


def init_service(config):
    ManageApiClient(config)


def manage_api_http_safe_close():
    ManageApiClient.safe_close()

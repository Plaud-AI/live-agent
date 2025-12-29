import traceback
from datetime import datetime, timezone as dt_timezone
from functools import wraps
from typing import Optional, Dict, Any, List, Callable

import requests

from ..base import MemoryProviderBase, logger
from memu import MemuClient
from core.utils.util import check_model_key

TAG = __name__

# 常量定义
DEFAULT_AGENT_ID = "xiaozhi_agent"
DEFAULT_BASE_URL = "https://api.memu.so"

# Category display titles with brief descriptions
CATEGORY_TITLES = {
    "profile": "Profile (user background and characteristics)",
    "event": "Events (important events in recent 7 days)",
}


def _format_relative_time(ts: datetime, now: datetime) -> str:
    """Format datetime as relative time string
    
    Args:
        ts: Target datetime (must be timezone-aware)
        now: Current datetime (must be timezone-aware)
    
    Returns:
        Relative time string like "Within the last hour", "3 hours ago", "Yesterday", "5 days ago"
    """
    time_delta = now - ts
    total_hours = int(time_delta.total_seconds() / 3600)
    
    if total_hours < 1:
        return "Within the last hour"
    elif total_hours < 24:
        return f"{total_hours} hours ago" if total_hours > 1 else "1 hour ago"
    elif time_delta.days == 1:
        return "Yesterday"
    else:
        return f"{time_delta.days} days ago"


def _process_summary(text: str) -> str:
    """Process MemU summary: remove first-level header and adjust remaining headers
    
    MemU summary starts with a # header (e.g. "# 事件", "# 用户档案") which is redundant
    since we already add our own title. We remove it and adjust remaining headers.
    
    Args:
        text: Markdown text from MemU summary
    
    Returns:
        Processed text with first header removed and headers adjusted
    """
    import re
    
    lines = text.strip().split('\n')
    
    # Remove first line ONLY if it's a single # header (e.g. "# 用户档案", not "## 近期动态")
    if lines and re.match(r'^#(?!#)\s+\S', lines[0]):
        lines = lines[1:]
    
    # Skip any leading empty lines after removing the header
    while lines and not lines[0].strip():
        lines = lines[1:]
    
    result = '\n'.join(lines)
    
    # Adjust remaining header levels: ## -> ####, ### -> #####, etc.
    def replace_header(match):
        hashes = match.group(1)
        content = match.group(2)
        # Add 2 levels: ## becomes ####
        return "#" * (len(hashes) + 2) + " " + content
    
    return re.sub(r'^(#{1,6})\s+(.+)$', replace_header, result, flags=re.MULTILINE)


def require_memu(func: Callable) -> Callable:
    """装饰器：检查 MemU 服务是否可用"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.use_memu:
            return {"success": False, "error": "MemU 服务未启用"}
        return func(self, *args, **kwargs)
    return wrapper


class MemoryProvider(MemoryProviderBase):
    """MemU 记忆服务提供者"""

    def __init__(self, config: dict, summary_memory=None):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", DEFAULT_BASE_URL)
        self.user_name = config.get("user_name", "用户")
        self.agent_name = config.get("agent_name", "小智")
        self.agent_id = config.get("agent_id", DEFAULT_AGENT_ID)
        self.use_memu = False
        self.client = None

        model_key_msg = check_model_key("MemU", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)
            return

        try:
            self.client = MemuClient(base_url=self.base_url, api_key=self.api_key)
            self.use_memu = True
            logger.bind(tag=TAG).info("成功连接到 MemU 服务")
        except Exception as e:
            logger.bind(tag=TAG).error(f"连接 MemU 服务失败: {e}")
            logger.bind(tag=TAG).debug(traceback.format_exc())

    # ==================== 内部工具方法 ====================

    @property
    def _headers(self) -> Dict[str, str]:
        """构造请求头"""
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

    def _base_payload(self, **extra) -> Dict[str, Any]:
        """构造基础请求体，包含 user_id 和 agent_id"""
        payload = {"user_id": self.role_id, "agent_id": self.agent_id}
        payload.update(extra)
        return payload

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """统一的 HTTP 请求方法"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                params=params,
                headers=self._headers,
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.bind(tag=TAG).error(f"请求失败 [{method} {endpoint}]: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            logger.bind(tag=TAG).error(f"请求异常 [{method} {endpoint}]: {e}")
            return {"success": False, "error": str(e)}

    async def save_memory(self, msgs, context=None):
        if not self.use_memu:
            return None
        if len(msgs) < 2:
            return None

        try:
            # Format the conversation as a single text string for memU
            conversation_text = ""
            for message in msgs:
                if message.role == "system":
                    continue
                role_name = self.user_name if message.role == "user" else self.agent_name
                conversation_text += f"{role_name}: {message.content}\n"

            if not conversation_text.strip():
                return None

            # 准备session_date参数（MEMu SDK支持的参数）
            import time
            from datetime import datetime
            
            session_date = None
            context_info = {}
            # 优先从 context 获取 agent_id，否则用 self.agent_id
            agent_id = self.agent_id
            if context:
                # 记录上下文信息到日志
                if "session_id" in context:
                    context_info["session_id"] = context["session_id"]
                if "mac_address" in context:
                    context_info["mac_address"] = context["mac_address"]
                if "device_id" in context:
                    context_info["device_id"] = context["device_id"]
                if "user_id" in context:
                    context_info["user_id"] = context["user_id"]
                if "agent_id" in context and context["agent_id"]:
                    agent_id = context["agent_id"]
                    context_info["agent_id"] = agent_id
                
                # 使用当前时间作为session_date
                session_date = datetime.now().strftime("%Y-%m-%d")
            
            # Use memorize_conversation to store the memory
            result = self.client.memorize_conversation(
                conversation=conversation_text.strip(),
                user_id=self.role_id,
                user_name=self.user_name,
                agent_id=agent_id,
                agent_name=self.agent_name,
                session_date=session_date
            )
            logger.bind(tag=TAG).info(f"保存记忆成功，user_id: {self.role_id}, agent_id: {agent_id}, context: {context_info}, session_date: {session_date}")
            logger.bind(tag=TAG).debug(f"Save memory result: {result}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"保存记忆失败: {str(e)}")
            logger.bind(tag=TAG).error(f"详细错误: {traceback.format_exc()}")
            return None
    
    @require_memu
    async def query_memory(self, query: str, client_timezone: str = None) -> str:
        """Retrieve memories related to the query
        
        Args:
            query: User query text to search for related memories
            client_timezone: Client timezone string (e.g., 'Asia/Shanghai', 'UTC+8')
            
        Returns:
            Formatted string of related memories grouped by category
        """
        import asyncio
        from core.utils.current_time import parse_timezone
        
        try:
            # Run sync HTTP call in thread pool to enable proper timeout cancellation
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.retrieve_related_memory_items(
                    user_id=self.role_id,
                    agent_id=self.agent_id,
                    query=query,
                    top_k=5,
                    min_similarity=0.3
                )
            )

            if not response.related_memories:
                return ""

            tz = parse_timezone(client_timezone)
            now = datetime.now(tz)
            
            # Group by original category (no merging)
            # tuple: (datetime for sorting, content)
            grouped: dict[str, list[tuple[datetime, str]]] = {}
            
            for item in response.related_memories:
                memory = item.memory
                category = memory.category
                ts = memory.happened_at or memory.created_at
                
                # Normalize timezone and convert to client timezone
                if ts:
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=dt_timezone.utc)
                    ts = ts.astimezone(tz)
                else:
                    ts = datetime.min.replace(tzinfo=dt_timezone.utc)
                
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append((ts, memory.content))

            # Format output: 
            # 1. category
            # - [x days ago] content
            output = []
            for idx, (category, items) in enumerate(grouped.items(), 1):
                output.append(f"{idx}. {category}")
                # Sort by time descending (most recent first), then format
                items.sort(key=lambda x: x[0], reverse=True)
                for ts, content in items:
                    if ts != datetime.min.replace(tzinfo=dt_timezone.utc):
                        time_str = _format_relative_time(ts, now)
                        output.append(f"- [{time_str}] {content}")
                    else:
                        output.append(f"- {content}")

            if not output:
                return ""

            memories_str = "\n".join(output)
            logger.bind(tag=TAG).debug(f"Query results: {memories_str}")
            return memories_str
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"查询记忆失败: {str(e)}")
            logger.bind(tag=TAG).error(f"详细错误: {traceback.format_exc()}")
            return ""

    @require_memu
    def get_user_persona(self, client_timezone: str = None) -> Optional[str]:
        """Get user persona with category summaries and recent events from MemU
        
        Args:
            client_timezone: Client timezone string (e.g., 'Asia/Shanghai', 'UTC+8')
        
        Retrieves:
        - profile category: summary only
        - event category: memory items from last 7 days
        
        Returns:
            Formatted user persona string for system prompt
        """
        from datetime import timedelta
        from core.utils.current_time import parse_timezone
        
        try:
            result = self.client.retrieve_default_categories(
                user_id=self.role_id,
                agent_id=self.agent_id,
                want_memory_items=True
            )
            
            logger.bind(tag=TAG).debug(f"User persona result: {result}")
            if not result.categories:
                return None
            
            # Use client timezone for "today/yesterday" calculation
            tz = parse_timezone(client_timezone)
            now = datetime.now(tz)
            seven_days_ago = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            output = []
            
            for cat in result.categories:
                # Only process profile and event categories
                if cat.name not in ("profile", "event"):
                    continue
                
                # Add category title
                title = CATEGORY_TITLES.get(cat.name, cat.name)
                section = [f"### {title}"]
                
                # For profile: add summary; for event: only add recent memory items
                if cat.name == "profile" and cat.summary and cat.summary.strip():
                    processed_summary = _process_summary(cat.summary.strip())
                    if processed_summary:
                        section.append(processed_summary)
                        logger.bind(tag=TAG).debug(f"Profile summary: {processed_summary}")
                
                # For event category, add recent memory items (last 7 days), skip summary
                if cat.name == "event" and cat.memory_items and cat.memory_items.memories:
                    recent_items = []
                    for memory in cat.memory_items.memories:
                        happened_at = memory.happened_at
                        if not happened_at:
                            continue
                        # Normalize to aware datetime for comparison
                        if happened_at.tzinfo is None:
                            happened_at = happened_at.replace(tzinfo=dt_timezone.utc)
                        # Convert to client timezone for calculation
                        happened_at_local = happened_at.astimezone(tz)
                        if happened_at_local >= seven_days_ago:
                            recent_items.append((happened_at_local, memory.content))
                    
                    if recent_items:
                        # Sort by time descending (most recent first), then format
                        recent_items.sort(key=lambda x: x[0], reverse=True)
                        for ts, content in recent_items[:10]:
                            time_str = _format_relative_time(ts, now)
                            section.append(f"- [{time_str}] {content}")
                        logger.bind(tag=TAG).debug(f"Recent events count: {len(recent_items)}")
                output.append("\n".join(section))
            
            if not output:
                return None
            
            persona_str = "\n\n".join(output)
            logger.bind(tag=TAG).debug(f"User persona loaded, length: {len(persona_str)}")
            return persona_str
            
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Failed to get user persona: {str(e)}")
            logger.bind(tag=TAG).debug(traceback.format_exc())
            return None

    async def get_user_persona_async(self, client_timezone: str = None) -> Optional[str]:
        """异步获取用户画像（不阻塞主线程）
        
        将同步的 get_user_persona 调用放到线程池中执行，避免阻塞事件循环。
        
        Args:
            client_timezone: 客户端时区字符串 (e.g., 'Asia/Shanghai', 'UTC+8')
        
        Returns:
            格式化后的用户画像字符串，如果获取失败或未启用则返回 None
        """
        import asyncio
        
        if not self.use_memu:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            persona = await loop.run_in_executor(
                None,  # 使用默认线程池
                lambda: self.get_user_persona(client_timezone=client_timezone)
            )
            return persona
        except Exception as e:
            logger.bind(tag=TAG).warning(f"异步获取用户画像失败: {str(e)}")
            return None

    # ==================== Memory Item CRUD ====================

    @require_memu
    def create_memory_item(self, memory_type: str, summary: str) -> Dict[str, Any]:
        """创建单条记忆记录
        
        Args:
            memory_type: 记忆类型
            summary: 记忆摘要内容
        """
        payload = self._base_payload(memory_type=memory_type, summary=summary)
        return self._request("POST", "/memory-items", payload=payload)

    @require_memu
    def update_memory_item(self, memory_item_id: str, summary: str) -> Dict[str, Any]:
        """修改单条记忆记录
        
        Args:
            memory_item_id: 记忆记录 ID
            summary: 新的摘要内容
        """
        payload = self._base_payload(summary=summary)
        return self._request("PUT", f"/memory-items/{memory_item_id}", payload=payload)

    @require_memu
    def delete_memory_item(self, memory_item_id: str) -> Dict[str, Any]:
        """删除单条记忆记录
        
        Args:
            memory_item_id: 记忆记录 ID
        """
        params = {"user_id": self.role_id, "agent_id": self.agent_id}
        return self._request("DELETE", f"/memory-items/{memory_item_id}", params=params)


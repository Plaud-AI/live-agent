"""
Memory API Handler
处理记忆查询请求，支持 mem0ai 和本地记忆模型
"""

import json
from typing import Optional, Tuple
from aiohttp import web
from config.logger import setup_logging
from core.utils.auth import AuthToken

TAG = __name__
logger = setup_logging()


class MemoryHandler:
    """记忆查询 API 处理器"""

    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        # 使用与 vision_handler 相同的认证密钥
        auth_key = config.get("server", {}).get("auth_key", "")
        if not auth_key:
            auth_key = config.get("manager-api", {}).get("secret", "")
        self.auth = AuthToken(auth_key)

    def _verify_auth_token(self, request) -> Tuple[bool, Optional[str]]:
        """
        验证 JWT token 并提取 device_id

        Args:
            request: aiohttp request 对象

        Returns:
            (是否有效, device_id)
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return False, None
        token = auth_header[7:]
        return self.auth.verify_token(token)

    def _create_error_response(self, error_message: str) -> dict:
        """创建错误响应"""
        return {"error": error_message}

    def _create_success_response(self, data: dict) -> dict:
        """创建成功响应"""
        return {"success": True, "data": data}

    async def handle_get(self, request):
        """处理 GET 请求（返回接口说明）"""
        return web.Response(
            text="Memory Query API. Use POST method.",
            content_type="text/plain",
        )

    async def handle_post(self, request):
        """
        处理 POST 请求：查询用户记忆

        请求格式：
        {
            "query": "用户最近的兴趣爱好",  // 可选，用于搜索特定记忆
            "limit": 10  // 可选，返回记忆条数，默认10
        }

        响应格式：
        {
            "success": true,
            "data": {
                "memories": [
                    {"memory": "用户喜欢编程", "timestamp": "2024-03-20T10:00:00"},
                    ...
                ],
                "user_persona": "- 名字：张三\n- 职业：程序员\n..."
            }
        }
        """
        try:
            # 1. 验证 token
            is_valid, token_device_id = self._verify_auth_token(request)
            if not is_valid:
                response = web.Response(
                    text=json.dumps(
                        self._create_error_response("无效的认证token或token已过期")
                    ),
                    content_type="application/json",
                    status=401,
                )
                return response

            # 2. 验证 Device-Id header
            device_id = request.headers.get("Device-Id", "")
            if not device_id:
                raise ValueError("缺少 Device-Id header")
            if device_id != token_device_id:
                raise ValueError("设备ID与token不匹配")

            # 3. 验证 Client-Id header（用于获取 agent 配置）
            client_id = request.headers.get("Client-Id", "")
            if not client_id:
                raise ValueError("缺少 Client-Id header")

            # 4. 解析请求参数
            try:
                body = await request.json()
                query = body.get("query", "user information, preferences, background")
                limit = body.get("limit", 10)
            except Exception:
                # 如果没有 body，使用默认值
                query = "user information, preferences, background"
                limit = 10

            # 5. 获取 Agent 配置
            from config.config_loader import get_private_config_from_api

            try:
                private_config = get_private_config_from_api(
                    self.config, device_id, client_id
                )
            except Exception as e:
                logger.bind(tag=TAG).error(f"获取 Agent 配置失败: {e}")
                raise ValueError(f"无法获取设备配置: {str(e)}")

            # 6. 初始化记忆提供者
            # 获取选中的记忆模型（从 selected_module）
            selected_memory_type = private_config.get("selected_module", {}).get("Memory", "nomem")
            
            # 获取具体的记忆配置
            memory_configs = private_config.get("Memory", {})
            memory_config = memory_configs.get(selected_memory_type, {})

            logger.bind(tag=TAG).info(
                f"查询记忆 - Device: {device_id}, Memory Type: {selected_memory_type}, Config: {memory_config.get('type', 'unknown')}"
            )

            # 7. 根据记忆类型查询
            if selected_memory_type == "Memory_mem0ai":
                # mem0ai 云端记忆
                from core.providers.memory.mem0ai.mem0ai import MemoryProvider

                memory_provider = MemoryProvider(memory_config)
                memory_provider.init_memory(device_id, None)

                # 查询记忆
                memories_str = await memory_provider.query_memory(query)
                user_persona = memory_provider.get_user_persona()

                # 解析记忆字符串为列表
                memories = []
                if memories_str:
                    for line in memories_str.split("\n"):
                        line = line.strip()
                        if line.startswith("- ["):
                            # 格式: - [2024-03-20 10:00:00] 用户喜欢编程
                            try:
                                timestamp_end = line.index("]")
                                timestamp = line[3:timestamp_end]
                                memory_text = line[timestamp_end + 2 :]
                                memories.append(
                                    {"timestamp": timestamp, "memory": memory_text}
                                )
                            except Exception:
                                memories.append({"timestamp": "", "memory": line[2:]})

                result = {
                    "memory_type": selected_memory_type,
                    "memories": memories[:limit],
                    "user_persona": user_persona,
                }

            elif selected_memory_type == "Memory_mem_local_short":
                # 本地短期记忆
                # 注意：本地记忆存储在数据库，应该通过 Java API 获取
                result = {
                    "memory_type": selected_memory_type,
                    "message": "本地记忆存储在数据库中，请使用 GET /agent/{id} 接口获取 summaryMemory 字段",
                }

            else:
                # 无记忆或其他类型
                result = {
                    "memory_type": selected_memory_type,
                    "memories": [],
                    "user_persona": None,
                }

            # 8. 返回响应
            response = web.Response(
                text=json.dumps(self._create_success_response(result), ensure_ascii=False),
                content_type="application/json",
                charset="utf-8"
            )
            return response

        except ValueError as e:
            logger.bind(tag=TAG).warning(f"Memory POST 请求参数错误: {e}")
            response = web.Response(
                text=json.dumps(self._create_error_response(str(e))),
                content_type="application/json",
                status=400,
            )
            return response

        except Exception as e:
            logger.bind(tag=TAG).error(f"Memory POST 请求异常: {e}", exc_info=True)
            response = web.Response(
                text=json.dumps(
                    self._create_error_response(f"服务器内部错误: {str(e)}")
                ),
                content_type="application/json",
                status=500,
            )
            return response


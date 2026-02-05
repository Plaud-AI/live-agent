"""
Agora API 处理器

提供 Agora RTC 相关的 HTTP API：
- Token 生成
- Agent 启动/停止
- 频道管理

API 端点：
- POST /api/agora/token/generate - 生成 Agora Token
- POST /api/agora/agent/start - 启动 Agent
- POST /api/agora/agent/stop - 停止 Agent
- POST /api/agora/agent/ping - 保活 Ping
"""

import json
import time
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional

from aiohttp import web
from core.api.base_handler import BaseHandler

TAG = __name__


class AgoraHandler(BaseHandler):
    """
    Agora API 处理器
    
    通过 ws_server 参数获取共享的 LLM/ASR/TTS 等模块，
    实现与 WebSocket 通道相同的对话处理逻辑。
    """
    
    def __init__(self, config: dict, ws_server=None):
        super().__init__(config)
        self.logger = logging.getLogger(TAG)
        self.ws_server = ws_server  # WebSocketServer 实例
        
        # 活跃的 Agent 会话
        # key: channel_name, value: {"conn": ConnectionHandler, "channel": AgoraChannel, ...}
        self._active_agents: Dict[str, Dict[str, Any]] = {}
        
        # 初始化 Agora 服务
        self._init_agora_service()
    
    def _init_agora_service(self):
        """初始化 Agora 服务"""
        import os
        try:
            from core.agora import AgoraServiceManager, TokenService
            
            # 从配置获取 Agora 凭证（支持环境变量回退）
            agora_config = self.config.get("agora", {})
            app_id = agora_config.get("app_id") or os.getenv("AGORA_APP_ID")
            app_certificate = agora_config.get("app_certificate") or os.getenv("AGORA_APP_CERTIFICATE", "")
            
            if app_id:
                # 初始化 AgoraServiceManager
                AgoraServiceManager.initialize(
                    app_id=app_id,
                    app_certificate=app_certificate
                )
                
                # 配置 TokenService
                TokenService.configure(
                    app_id=app_id,
                    app_certificate=app_certificate
                )
                
                self.logger.info(f"Agora 服务初始化成功: app_id={app_id[:8]}...")
            else:
                self.logger.warning("未配置 Agora 凭证，Agora 功能不可用")
                
        except ImportError as e:
            self.logger.warning(f"Agora SDK 不可用: {e}")
        except Exception as e:
            self.logger.error(f"Agora 服务初始化失败: {e}")
    
    async def _process_channel_messages(self, conn, channel, channel_name: str) -> None:
        """
        处理频道消息的后台任务
        
        使用 ConnectionHandler 处理 Agora 频道的消息（音频和文本）。
        
        Args:
            conn: ConnectionHandler 实例
            channel: AgoraChannel 实例
            channel_name: 频道名称
        """
        from core.handle.textHandle import handleTextMessage
        from core.handle.receiveAudioHandle import handleAudioMessage
        from core.channels import MessageType
        
        print(f"[AgoraHandler] 开始监听频道消息: {channel_name}")
        self.logger.info(f"开始监听频道消息: {channel_name}")
        
        message_count = 0
        try:
            async for message in channel.receive_messages():
                message_count += 1
                
                if message.type == MessageType.TEXT:
                    print(f"[AgoraHandler] 收到文本消息: {message.data[:100]}...")
                    self.logger.info(f"[Agora] 收到文本消息: {message.data[:100]}...")
                    
                    # 使用 ConnectionHandler 的消息处理流程
                    await handleTextMessage(conn, message.data)
                    
                elif message.type == MessageType.AUDIO:
                    # 音频消息：传递给 ASR 处理
                    audio_data = message.data.data if hasattr(message.data, 'data') else message.data
                    if audio_data:
                        await handleAudioMessage(conn, audio_data)
                    
        except asyncio.CancelledError:
            print(f"[AgoraHandler] 频道消息监听任务被取消: {channel_name}")
            self.logger.info(f"频道消息监听任务被取消: {channel_name}")
        except Exception as e:
            print(f"[AgoraHandler] 频道消息处理异常: {channel_name}, error={e}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"频道消息处理异常: {channel_name}, error={e}")
        finally:
            print(f"[AgoraHandler] 停止监听频道消息: {channel_name}, 共处理 {message_count} 条消息")
            self.logger.info(f"停止监听频道消息: {channel_name}")
    
    async def generate_token(self, request: web.Request) -> web.Response:
        """
        生成 Agora Token
        
        POST /api/agora/token/generate
        {
            "request_id": "uuid",
            "channel_name": "room_123",
            "uid": 12345
        }
        
        Response:
        {
            "code": 0,
            "data": {
                "appId": "xxx",
                "token": "xxx",
                "channel_name": "room_123",
                "uid": 12345
            }
        }
        """
        try:
            data = await request.json()
            print(f"[AgoraHandler] Token 请求: {data}")
            
            channel_name = data.get("channel_name")
            uid = data.get("uid", 0)
            
            if not channel_name:
                return self._error_response("channel_name 是必需的")
            
            # 生成 Token
            from core.agora import TokenService
            
            result = TokenService.generate_token_response(
                channel_name=channel_name,
                uid=uid,
                expire_seconds=3600
            )
            
            if result is None:
                return self._error_response("Token 生成失败")
            
            print(f"[AgoraHandler] Token 响应: appId={result.get('appId', '')[:8]}..., channel={channel_name}, uid={uid}")
            return self._success_response(result)
            
        except json.JSONDecodeError:
            return self._error_response("无效的 JSON 格式")
        except Exception as e:
            self.logger.error(f"Token 生成异常: {e}")
            return self._error_response(str(e))
    
    async def start_agent(self, request: web.Request) -> web.Response:
        """
        启动 Agent 加入 Agora 频道
        
        POST /api/agora/agent/start
        {
            "request_id": "uuid",
            "channel_name": "room_123",
            "user_uid": 12345,
            "agent_uid": 1234,
            "graph_name": "voice_assistant",
            "language": "zh-CN",
            "device_id": "xxx",
            "agent_id": "xxx"
        }
        """
        try:
            data = await request.json()
            
            channel_name = data.get("channel_name")
            user_uid = data.get("user_uid", 0)
            agent_uid = data.get("agent_uid", 1234)
            device_id = data.get("device_id", "agora_device")
            agent_id = data.get("agent_id")
            
            if not channel_name:
                return self._error_response("channel_name 是必需的")
            
            # 检查是否已有 Agent
            if channel_name in self._active_agents:
                return self._error_response(f"频道 {channel_name} 已有 Agent 运行")
            
            # 检查 WebSocketServer 是否可用
            if self.ws_server is None:
                return self._error_response("WebSocketServer 未初始化，无法创建 Agent")
            
            # 生成 Agent Token
            from core.agora import TokenService
            
            token = TokenService.generate_rtc_token(
                channel_name=channel_name,
                uid=agent_uid,
                expire_seconds=3600
            )
            
            # 创建 Agora 通道
            from core.channels import ChannelFactory
            
            channel = ChannelFactory.create_agora_channel(
                channel_name=channel_name,
                uid=agent_uid,
                token=token,
                remote_uid=user_uid,
            )
            
            # 加入频道
            success = await channel.join_channel()
            
            if not success:
                return self._error_response("Agent 加入频道失败")
            
            # 创建 ConnectionHandler 实例（复用 WebSocketServer 的模块）
            from core.connection import ConnectionHandler
            
            conn = ConnectionHandler(
                self.config,
                self.ws_server._vad,
                self.ws_server._asr,
                self.ws_server._llm,
                self.ws_server._memory,
                self.ws_server._intent,
                self.ws_server,  # server 实例
            )
            
            # 设置 Agora 通道和基本信息
            conn.channel = channel
            conn.device_id = device_id
            conn.client_id = f"agora_{channel_name}"
            conn.agent_id = agent_id
            conn.headers = {"device-id": device_id, "client-id": conn.client_id}
            conn.query_params = {"agent-id": agent_id} if agent_id else {}
            conn.loop = asyncio.get_running_loop()
            
            # Agora 连接不需要绑定设备，跳过设备配置获取
            conn.read_config_from_api = False
            conn.need_bind = False
            conn.bind_completed_event.set()
            
            # 初始化 ConnectionHandler（异步）
            asyncio.create_task(conn._background_initialize())
            
            # 启动消息处理任务
            message_task = asyncio.create_task(
                self._process_channel_messages(conn, channel, channel_name)
            )
            
            # 记录活跃 Agent
            self._active_agents[channel_name] = {
                "conn": conn,
                "channel": channel,
                "user_uid": user_uid,
                "agent_uid": agent_uid,
                "last_ping": time.time(),
                "started_at": time.time(),
                "message_task": message_task,
            }
            
            print(f"[AgoraHandler] Agent 启动成功: channel={channel_name}, agent_uid={agent_uid}")
            self.logger.info(
                f"Agent 启动成功: channel={channel_name}, agent_uid={agent_uid}, device_id={device_id}"
            )
            
            response_data = {
                "channel_name": channel_name,
                "agent_uid": agent_uid,
            }
            print(f"[AgoraHandler] 返回响应: {response_data}")
            return self._success_response(response_data)
            
        except json.JSONDecodeError:
            return self._error_response("无效的 JSON 格式")
        except Exception as e:
            self.logger.error(f"启动 Agent 异常: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(str(e))
    
    async def stop_agent(self, request: web.Request) -> web.Response:
        """
        停止 Agent 离开 Agora 频道
        
        POST /api/agora/agent/stop
        {
            "request_id": "uuid",
            "channel_name": "room_123"
        }
        """
        try:
            data = await request.json()
            
            channel_name = data.get("channel_name")
            
            if not channel_name:
                return self._error_response("channel_name 是必需的")
            
            # 获取 Agent
            agent_info = self._active_agents.get(channel_name)
            
            if agent_info is None:
                return self._error_response(f"频道 {channel_name} 没有运行的 Agent")
            
            # 取消消息处理任务
            message_task = agent_info.get("message_task")
            if message_task and not message_task.done():
                message_task.cancel()
                try:
                    await message_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭 ConnectionHandler
            conn = agent_info.get("conn")
            if conn:
                try:
                    conn.stop_event.set()
                    if hasattr(conn, 'close'):
                        await conn.close(None)
                except Exception as e:
                    self.logger.warning(f"关闭 ConnectionHandler 异常: {e}")
            
            # 离开频道
            channel = agent_info.get("channel")
            if channel:
                await channel.close()
            
            # 移除记录
            del self._active_agents[channel_name]
            
            self.logger.info(f"Agent 停止成功: channel={channel_name}")
            
            return self._success_response(None)
            
        except json.JSONDecodeError:
            return self._error_response("无效的 JSON 格式")
        except Exception as e:
            self.logger.error(f"停止 Agent 异常: {e}")
            return self._error_response(str(e))
    
    async def ping_agent(self, request: web.Request) -> web.Response:
        """
        Agent 保活 Ping
        
        POST /api/agora/agent/ping
        {
            "request_id": "uuid",
            "channel_name": "room_123"
        }
        """
        try:
            data = await request.json()
            
            channel_name = data.get("channel_name")
            
            if not channel_name:
                return self._error_response("channel_name 是必需的")
            
            # 更新最后 Ping 时间
            if channel_name in self._active_agents:
                self._active_agents[channel_name]["last_ping"] = time.time()
                return self._success_response(None)
            else:
                return self._error_response(f"频道 {channel_name} 没有运行的 Agent")
            
        except json.JSONDecodeError:
            return self._error_response("无效的 JSON 格式")
        except Exception as e:
            self.logger.error(f"Ping Agent 异常: {e}")
            return self._error_response(str(e))
    
    def _success_response(self, data: Any) -> web.Response:
        """返回成功响应"""
        return web.json_response({
            "code": 0,
            "data": data,
        })
    
    def _error_response(self, message: str, code: int = -1) -> web.Response:
        """返回错误响应"""
        return web.json_response({
            "code": code,
            "message": message,
        })

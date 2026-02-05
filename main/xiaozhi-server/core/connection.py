import os
import sys
import copy
import json
import uuid
import time
import queue
import asyncio
import threading
import traceback
import subprocess
import websockets

from core.utils.util import (
    extract_json_from_string,
    check_vad_update,
    check_asr_update,
    filter_sensitive_info,
)
from typing import Dict, Any
from collections import deque
from core.utils.modules_initialize import (
    initialize_modules,
    initialize_tts,
    initialize_asr,
)
from core.handle.reportHandle import report
from core.providers.tts.default import DefaultTTS
from concurrent.futures import ThreadPoolExecutor
from core.utils.dialogue import Message, Dialogue
from core.providers.asr.dto.dto import InterfaceType
from core.handle.textHandle import handleTextMessage
from core.providers.tools.unified_tool_handler import UnifiedToolHandler
from plugins_func.loadplugins import auto_import_modules
from plugins_func.register import Action
from core.auth import AuthenticationError
from config.config_loader import get_private_config_from_api, resolve_env_vars
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType
from config.logger import setup_logging, build_module_string, create_connection_logger
from config.manage_api_client import DeviceNotFoundException, DeviceBindException
from config.live_agent_api_client import get_agent_config_cached as get_agent_config_from_live_agent, init_live_agent_api
from core.utils.prompt_manager import PromptManager
from core.utils.voiceprint_provider import VoiceprintProvider
from core.utils import textUtils
from core.utils import expressionUtils
from core.utils.latency_metrics import LatencyMetrics, remove_metrics
from core.channels import ChannelFactory, BaseChannel, AudioPacket

TAG = __name__

auto_import_modules("plugins_func.functions")


class TTSException(RuntimeError):
    pass


class ConnectionHandler:
    def __init__(
        self,
        config: Dict[str, Any],
        _vad,
        _asr,
        _llm,
        _memory,
        _intent,
        server=None,
    ):
        # 使用临时 logger 记录构造函数进度
        import logging
        _init_logger = logging.getLogger(__name__)
        _init_logger.info("ConnectionHandler.__init__: 开始")
        
        self.common_config = config
        self.config = copy.deepcopy(config)
        self.session_id = str(uuid.uuid4())
        _init_logger.info(f"ConnectionHandler.__init__: session_id={self.session_id[:8]}")
        
        self.logger = setup_logging()
        self.server = server  # 保存server实例的引用

        self.need_bind = False  # 是否需要绑定设备
        self.bind_completed_event = asyncio.Event()
        self.bind_code = None  # 绑定设备的验证码
        self.last_bind_prompt_time = 0  # 上次播放绑定提示的时间戳(秒)
        self.bind_prompt_interval = 60  # 绑定提示播放间隔(秒)

        self.read_config_from_api = self.config.get("read_config_from_api", False)

        self.websocket = None
        self.channel: BaseChannel = None  # 通道抽象层（新增）
        self.headers = None
        self.query_params = {}  # URL query parameters
        self.device_id = None
        self.client_id = None
        self.agent_id = None  # Agent ID from mobile client
        self.client_ip = None
        self.prompt = None
        self.welcome_msg = None
        self.max_output_size = 0
        self.chat_history_conf = 0
        self.audio_format = "opus"

        # 客户端状态相关
        self.client_abort = False
        self.client_is_speaking = False
        self.client_listen_mode = "auto"

        # 线程任务相关
        self.loop = None  # 在 handle_connection 中获取运行中的事件循环
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.chat_future = None  # 当前 chat() 任务的 Future
        self.chat_lock = threading.Lock()  # 保护 chat_future 的锁

        # 添加上报线程池
        self.report_queue = queue.Queue()
        self.report_thread = None
        # 未来可以通过修改此处，调节asr的上报和tts的上报，目前默认都开启
        self.report_asr_enable = self.read_config_from_api
        self.report_tts_enable = self.read_config_from_api

        # 依赖的组件
        self.vad = None
        self.asr = None
        self.tts = None
        self._asr = _asr
        self._vad = _vad
        self.llm = _llm
        self.memory = _memory
        self.intent = _intent

        # 为每个连接单独管理声纹识别
        self.voiceprint_provider = None

        # vad相关变量
        self.client_audio_buffer = bytearray()
        self.client_have_voice = False
        self.client_voice_window = deque(maxlen=5)
        self.first_activity_time = 0.0  # 记录首次活动的时间（毫秒）
        self.last_activity_time = 0.0  # 统一的活动时间戳（毫秒）
        self.client_voice_stop = False
        self.last_is_voice = False

        # asr相关变量
        # 因为实际部署时可能会用到公共的本地ASR，不能把变量暴露给公共ASR
        # 所以涉及到ASR的变量，需要在这里定义，属于connection的私有变量
        self.asr_audio = []
        self.asr_audio_queue = queue.Queue()

        # llm相关变量
        self.llm_finish_task = True
        self.dialogue = Dialogue()
        self.llm_cancel_event = None  # LLM 取消事件，用于中断 LLM 请求

        # 延迟监控
        self.latency_metrics = None  # 延迟初始化，等待 session_id 设置

        # tts相关变量
        self.sentence_id = None
        # 处理TTS响应没有文本返回
        self.tts_MessageText = ""

        # iot相关变量
        self.iot_descriptors = {}
        self.func_handler = None

        self.cmd_exit = self.config["exit_commands"]

        # 是否在聊天结束后关闭连接
        self.close_after_chat = False
        self.load_function_plugin = False
        self.intent_type = "nointent"

        self.timeout_seconds = (
            int(self.config.get("close_connection_no_voice_time", 120)) + 60
        )  # 在原来第一道关闭的基础上加60秒，进行二道关闭
        self.timeout_task = None

        # {"mcp":true} 表示启用MCP功能
        self.features = None

        # 标记连接是否来自MQTT
        self.conn_from_mqtt_gateway = False

        # 初始化提示词管理器
        import logging
        _init_logger = logging.getLogger(__name__)
        _init_logger.info("ConnectionHandler.__init__: 准备初始化 PromptManager")
        self.prompt_manager = PromptManager(self.config, self.logger)
        _init_logger.info("ConnectionHandler.__init__: 构造函数完成")

    def _parse_query_params(self, path: str):
        """解析 URL query parameters"""
        from urllib.parse import urlparse, parse_qs
        try:
            parsed = urlparse(path)
            # parse_qs 返回 dict[str, list[str]]，取每个参数的第一个值
            qs = parse_qs(parsed.query)
            self.query_params = {k: v[0] if v else None for k, v in qs.items()}
        except Exception as e:
            self.logger.bind(tag=TAG).warning(f"Failed to parse query params: {e}")
            self.query_params = {}

    async def handle_connection(self, ws):
        try:
            # 获取运行中的事件循环（必须在异步上下文中）
            self.loop = asyncio.get_running_loop()

            # ========== 创建通道抽象层（新增） ==========
            self.channel = ChannelFactory.create_from_websocket(ws)
            self.logger.bind(tag=TAG).info(f"通道创建成功: {self.channel}")

            # ========== 从通道同步信息 ==========
            # 保留旧属性以兼容现有代码
            self.websocket = ws  # 兼容旧代码
            self.headers = self.channel.info.headers
            self.query_params = self.channel.info.query_params
            self.device_id = self.channel.info.device_id
            self.client_id = self.channel.info.client_id or self.device_id
            self.client_ip = self.channel.info.client_ip
            self.agent_id = self.channel.info.get_extra("agent_id")
            
            # 通道类型判断（替代旧的标志位判断）
            self.conn_from_mqtt_gateway = (self.channel.channel_type == "mqtt_gateway")
            
            self.logger.bind(tag=TAG).info(
                f"{self.client_ip} conn - channel_type: {self.channel.channel_type}, "
                f"device_id: {self.device_id}, client_id: {self.client_id}, agent_id: {self.agent_id}"
            )
            
            if self.conn_from_mqtt_gateway:
                self.logger.bind(tag=TAG).info("连接来自:MQTT网关")

            # 初始化活动时间戳
            self.first_activity_time = time.time() * 1000
            self.last_activity_time = time.time() * 1000

            # 启动超时检查任务
            self.timeout_task = asyncio.create_task(self._check_timeout())

            self.welcome_msg = self.config["xiaozhi"]
            self.welcome_msg["session_id"] = self.session_id

            # 初始化延迟监控
            self.latency_metrics = LatencyMetrics(session_id=self.session_id)

            # 在后台初始化配置和组件（完全不阻塞主循环）
            asyncio.create_task(self._background_initialize())

            try:
                # 使用通道接收消息（通道已处理好协议差异和乱序）
                from core.channels import MessageType
                async for msg in self.channel.receive_messages():
                    if msg.type == MessageType.TEXT:
                        await self._route_message(msg.data)
                    elif msg.type == MessageType.AUDIO:
                        # 音频消息：通道已处理头部解析和乱序，直接放入 ASR 队列
                        await self._handle_audio_from_channel(msg.data)
            except websockets.exceptions.ConnectionClosed:
                self.logger.bind(tag=TAG).info("客户端断开连接")

        except AuthenticationError as e:
            self.logger.bind(tag=TAG).error(f"Authentication failed: {str(e)}")
            return
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.bind(tag=TAG).error(f"Connection error: {str(e)}-{stack_trace}")
            return
        finally:
            try:
                await self._save_and_close(ws)
            except Exception as final_error:
                self.logger.bind(tag=TAG).error(f"最终清理时出错: {final_error}")
                # 确保即使保存记忆失败，也要关闭连接
                try:
                    await self.close(ws)
                except Exception as close_error:
                    self.logger.bind(tag=TAG).error(
                        f"强制关闭连接时出错: {close_error}"
                    )

    async def _save_and_close(self, ws):
        """保存记忆并关闭连接"""
        try:
            if self.memory:
                # 使用线程池异步保存记忆
                def save_memory_task():
                    try:
                        # 创建新事件循环（避免与主循环冲突）
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self.memory.save_memory(
                                self.dialogue.dialogue, self.session_id
                            )
                        )
                    except Exception as e:
                        self.logger.bind(tag=TAG).error(f"保存记忆失败: {e}")
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass

                # 启动线程保存记忆，不等待完成
                threading.Thread(target=save_memory_task, daemon=True).start()
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"保存记忆失败: {e}")
        finally:
            # 立即关闭连接，不等待记忆保存完成
            try:
                await self.close(ws)
            except Exception as close_error:
                self.logger.bind(tag=TAG).error(
                    f"保存记忆后关闭连接失败: {close_error}"
                )

    async def _discard_message_with_bind_prompt(self):
        """丢弃消息并检查是否需要播放绑定提示"""
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.bind(tag=TAG).debug(
                    f"_discard_message_with_bind_prompt: 丢弃消息, "
                    f"need_bind={self.need_bind}, bind_completed={self.bind_completed_event.is_set()}"
                )
            current_time = time.time()
            # 检查是否需要播放绑定提示
            if current_time - self.last_bind_prompt_time >= self.bind_prompt_interval:
                self.last_bind_prompt_time = current_time
                # 复用现有的绑定提示逻辑
                from core.handle.receiveAudioHandle import check_bind_device

                if hasattr(self, 'logger') and self.logger:
                    self.logger.bind(tag=TAG).info("_discard_message_with_bind_prompt: 触发绑定提示检查")
                asyncio.create_task(check_bind_device(self))
        except Exception as e:
            # 捕获异常，避免影响消息路由
            if hasattr(self, 'logger') and self.logger:
                self.logger.bind(tag=TAG).error(f"_discard_message_with_bind_prompt: 发生异常: {e}")

    async def _handle_audio_from_channel(self, packet):
        """
        处理从通道接收的音频包
        
        通道已经处理好：
        - MQTT 网关的 16 字节头部解析
        - 乱序包的重排序
        
        Args:
            packet: AudioPacket 对象
        """
        if self.vad is None or self.asr is None:
            return
        
        # 检查绑定状态
        if not self.bind_completed_event.is_set():
            try:
                await asyncio.wait_for(self.bind_completed_event.wait(), timeout=1)
            except asyncio.TimeoutError:
                await self._discard_message_with_bind_prompt()
                return
        
        if self.need_bind:
            await self._discard_message_with_bind_prompt()
            return
        
        # 直接放入 ASR 队列（通道已处理好乱序）
        self.asr_audio_queue.put(packet.data)

    async def _route_message(self, message):
        """
        消息路由（仅处理文本消息）
        
        音频消息由 _handle_audio_from_channel 处理
        """
        try:
            # 记录收到的消息（用于调试）
            message_preview = str(message)[:100]
            if hasattr(self, 'logger') and self.logger:
                self.logger.bind(tag=TAG).debug(f"_route_message: 收到文本消息, preview={message_preview}")
            
            # 检查是否已经获取到真实的绑定状态
            if not self.bind_completed_event.is_set():
                if hasattr(self, 'logger') and self.logger:
                    self.logger.bind(tag=TAG).debug(f"_route_message: 等待绑定状态确认, need_bind={self.need_bind}")
                try:
                    await asyncio.wait_for(self.bind_completed_event.wait(), timeout=1)
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.bind(tag=TAG).debug(f"_route_message: 绑定状态确认完成, need_bind={self.need_bind}")
                except asyncio.TimeoutError:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.bind(tag=TAG).warning(f"_route_message: 绑定状态确认超时，丢弃消息: {message_preview}")
                    await self._discard_message_with_bind_prompt()
                    return

            # 已经获取到真实状态，检查是否需要绑定
            if self.need_bind:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.bind(tag=TAG).info(f"_route_message: 设备需要绑定，丢弃消息: {message_preview}")
                await self._discard_message_with_bind_prompt()
                return

            # 处理文本消息
            await handleTextMessage(self, message)
            
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                import traceback
                self.logger.bind(tag=TAG).error(f"_route_message: 处理消息时发生异常: {e}, traceback: {traceback.format_exc()}")
            else:
                import logging
                import traceback
                logging.error(f"[{TAG}] _route_message: 处理消息时发生异常: {e}, traceback: {traceback.format_exc()}")

    async def handle_restart(self, message):
        """处理服务器重启请求"""
        try:

            self.logger.bind(tag=TAG).info("收到服务器重启指令，准备执行...")

            # 发送确认响应
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "success",
                        "message": "服务器重启中...",
                        "content": {"action": "restart"},
                    }
                )
            )

            # 异步执行重启操作
            def restart_server():
                """实际执行重启的方法"""
                time.sleep(1)
                self.logger.bind(tag=TAG).info("执行服务器重启...")
                subprocess.Popen(
                    [sys.executable, "app.py"],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    start_new_session=True,
                )
                os._exit(0)

            # 使用线程执行重启避免阻塞事件循环
            threading.Thread(target=restart_server, daemon=True).start()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"重启失败: {str(e)}")
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "error",
                        "message": f"Restart failed: {str(e)}",
                        "content": {"action": "restart"},
                    }
                )
            )

    def _initialize_components(self):
        try:
            if self.tts is None:
                self.tts = self._initialize_tts()
            # 打开语音合成通道
            asyncio.run_coroutine_threadsafe(
                self.tts.open_audio_channels(self), self.loop
            )
            if self.need_bind:
                self.bind_completed_event.set()
                return
            self.selected_module_str = build_module_string(
                self.config.get("selected_module", {})
            )
            self.logger = create_connection_logger(self.selected_module_str)

            """初始化组件"""
            if self.config.get("prompt") is not None:
                user_prompt = self.config["prompt"]
                # 使用快速提示词进行初始化
                prompt = self.prompt_manager.get_quick_prompt(user_prompt)
                self.change_system_prompt(prompt)
                self.logger.bind(tag=TAG).info(
                    f"快速初始化组件: prompt成功 {prompt[:50]}..."
                )

            """初始化本地组件"""
            if self.vad is None:
                self.vad = self._vad
            if self.asr is None:
                self.asr = self._initialize_asr()

            # 初始化声纹识别
            self._initialize_voiceprint()
            # 打开语音识别通道
            asyncio.run_coroutine_threadsafe(
                self.asr.open_audio_channels(self), self.loop
            )

            """加载记忆"""
            self._initialize_memory()
            """加载意图识别"""
            self._initialize_intent()
            """初始化上报线程"""
            self._init_report_threads()
            """更新系统提示词"""
            self._init_prompt_enhancement()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"实例化组件失败: {e}")

    def _init_prompt_enhancement(self):

        # 更新上下文信息
        self.prompt_manager.update_context_info(self, self.client_ip)
        enhanced_prompt = self.prompt_manager.build_enhanced_prompt(
            self.config["prompt"], self.device_id, self.client_ip
        )
        if enhanced_prompt:
            self.change_system_prompt(enhanced_prompt)
            self.logger.bind(tag=TAG).debug("系统提示词已增强更新")

    def _init_report_threads(self):
        """初始化ASR和TTS上报线程"""
        # App连接 (agent_id): 始终启动上报线程
        # 设备连接: 需要 read_config_from_api 且 chat_history_conf > 0
        if self.agent_id:
            # App连接：始终启动上报线程
            pass
        elif not self.read_config_from_api or self.need_bind:
            return
        elif self.chat_history_conf == 0:
            return
        
        if self.report_thread is None or not self.report_thread.is_alive():
            self.report_thread = threading.Thread(
                target=self._report_worker, daemon=True
            )
            self.report_thread.start()
            self.logger.bind(tag=TAG).info(
                f"聊天记录上报线程已启动 (agent_id={self.agent_id})"
            )

    def _initialize_tts(self):
        """初始化TTS"""
        tts = None
        if not self.need_bind:
            tts = initialize_tts(self.config)

        if tts is None:
            tts = DefaultTTS(self.config, delete_audio_file=True)

        return tts

    def _initialize_asr(self):
        """初始化ASR"""
        if (
            self._asr is not None
            and hasattr(self._asr, "interface_type")
            and self._asr.interface_type == InterfaceType.LOCAL
        ):
            # 如果公共ASR是本地服务，则直接返回
            # 因为本地一个实例ASR，可以被多个连接共享
            asr = self._asr
        else:
            # 如果公共ASR是远程服务，则初始化一个新实例
            # 因为远程ASR，涉及到websocket连接和接收线程，需要每个连接一个实例
            asr = initialize_asr(self.config)

        return asr

    def _initialize_voiceprint(self):
        """为当前连接初始化声纹识别"""
        try:
            voiceprint_config = self.config.get("voiceprint", {})
            if voiceprint_config:
                voiceprint_provider = VoiceprintProvider(voiceprint_config)
                if voiceprint_provider is not None and voiceprint_provider.enabled:
                    self.voiceprint_provider = voiceprint_provider
                    self.logger.bind(tag=TAG).info("声纹识别功能已在连接时动态启用")
                else:
                    self.logger.bind(tag=TAG).warning("声纹识别功能启用但配置不完整")
            else:
                self.logger.bind(tag=TAG).info("声纹识别功能未启用")
        except Exception as e:
            self.logger.bind(tag=TAG).warning(f"声纹识别初始化失败: {str(e)}")

    async def _background_initialize(self):
        """在后台初始化配置和组件（完全不阻塞主循环）"""
        try:
            # 异步获取差异化配置
            await self._initialize_private_config_async()
            # 在线程池中初始化组件
            self.executor.submit(self._initialize_components)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"后台初始化失败: {e}")

    def _convert_live_agent_config(self, agent_config: dict) -> dict:
        """
        将 live-agent-api 返回的配置转换为 xiaozhi-server 期望的格式
        
        live-agent-api 格式:
        {
            "voice": {"voice_id": "xxx", "reference_id": "xxx", "provider": "fishspeech"},
            "instruction": "...",
            "language": "en",
            ...
        }
        
        xiaozhi-server 格式:
        {
            "TTS": {"FishSpeechStreamTTS": {"private_voice": "xxx"}},
            "selected_module": {"TTS": "FishSpeechStreamTTS"},
            "prompt": "...",
            ...
        }
        """
        result = {}
        
        # 转换 voice 配置到 TTS 配置
        voice = agent_config.get("voice")
        if voice:
            provider = voice.get("provider", "fishspeech")
            reference_id = voice.get("reference_id")
            
            if reference_id:
                # 根据 provider 选择 TTS 模块
                # 模块名称映射（与 config.yaml 中的 selected_module.TTS 和 TTS 配置块名称一致）
                if provider == "fishspeech":
                    tts_module = "FishSpeechStream"  # config.yaml 中的名称
                    # 获取当前 TTS 配置作为基础
                    base_tts_config = copy.deepcopy(self.config.get("TTS", {}).get(tts_module, {}))
                    base_tts_config["private_voice"] = reference_id
                    result["TTS"] = {tts_module: base_tts_config}
                    result["selected_module"] = result.get("selected_module", {})
                    result["selected_module"]["TTS"] = tts_module
                    self.logger.bind(tag=TAG).info(
                        f"转换 voice 配置: provider={provider}, reference_id={reference_id}, tts_module={tts_module}"
                    )
                elif provider == "minimax":
                    tts_module = "MinimaxTTSWebSocket"  # config.yaml 中的名称
                    base_tts_config = copy.deepcopy(self.config.get("TTS", {}).get(tts_module, {}))
                    base_tts_config["private_voice"] = reference_id
                    result["TTS"] = {tts_module: base_tts_config}
                    result["selected_module"] = result.get("selected_module", {})
                    result["selected_module"]["TTS"] = tts_module
                    self.logger.bind(tag=TAG).info(
                        f"转换 voice 配置: provider={provider}, reference_id={reference_id}, tts_module={tts_module}"
                    )
        
        # 转换 instruction 到 prompt
        instruction = agent_config.get("instruction")
        if instruction:
            result["prompt"] = instruction
        
        # 保留原始配置供其他用途
        result["_live_agent_config"] = agent_config
        
        return result

    async def _initialize_private_config_async(self):
        """从接口异步获取差异化配置（异步版本，不阻塞主循环）"""
        if not self.read_config_from_api:
            self.need_bind = False
            self.bind_completed_event.set()
            return
        
        # 如果有 agent_id（移动端连接），从 live-agent-api 获取配置
        if self.agent_id:
            self.logger.bind(tag=TAG).info(
                f"Mobile client with agent_id={self.agent_id}, fetching agent config from live-agent-api"
            )
            self.need_bind = False
            self.bind_completed_event.set()
            try:
                begin_time = time.time()
                
                # 初始化 live-agent-api 客户端（如果尚未初始化）
                if self.config.get("live-agent-api"):
                    init_live_agent_api(self.config)
                agent_config = get_agent_config_from_live_agent(self.agent_id, self.config)
                # 转换 live-agent-api 配置格式为 xiaozhi-server 格式
                private_config = self._convert_live_agent_config(agent_config) if agent_config else None
                
                if private_config:
                    # 解析环境变量（配置可能包含 ${env:VAR_NAME} 语法）
                    private_config = resolve_env_vars(private_config)
                    private_config["delete_audio"] = bool(self.config.get("delete_audio", True))
                    
                    # 应用 api_defaults 配置（如果存在）
                    # 用于设置 API 角色的 LLM、ASR、VAD、Memory、Intent 等默认模块
                    api_defaults = self.config.get("api_defaults")
                    if api_defaults:
                        # 合并 selected_module（api_defaults 优先级高于全局默认）
                        if "selected_module" in api_defaults:
                            if "selected_module" not in private_config:
                                private_config["selected_module"] = {}
                            for key, value in api_defaults["selected_module"].items():
                                # 只设置 private_config 中未指定的模块
                                if key not in private_config["selected_module"]:
                                    private_config["selected_module"][key] = value
                        self.logger.bind(tag=TAG).info(
                            f"API角色应用本地 api_defaults 配置: {api_defaults.get('selected_module', {})}"
                        )
                    
                    self.logger.bind(tag=TAG).info(
                        f"{time.time() - begin_time:.2f} 秒，根据 agent_id={self.agent_id} 获取配置成功: {json.dumps(filter_sensitive_info(private_config), ensure_ascii=False)}"
                    )
                else:
                    self.logger.bind(tag=TAG).warning(
                        f"根据 agent_id={self.agent_id} 获取配置失败，使用默认配置"
                    )
                    private_config = {}
            except Exception as e:
                self.logger.bind(tag=TAG).error(
                    f"根据 agent_id={self.agent_id} 获取配置异常: {e}，使用默认配置"
                )
                private_config = {}
        else:
            # 传统设备（ESP32等），从 manager-api 获取配置
            try:
                begin_time = time.time()
                private_config = await get_private_config_from_api(
                    self.config,
                    self.device_id,
                    self.client_id,
                )
                # 解析环境变量（配置可能包含 ${env:VAR_NAME} 语法）
                private_config = resolve_env_vars(private_config)
                private_config["delete_audio"] = bool(self.config.get("delete_audio", True))
                self.logger.bind(tag=TAG).info(
                    f"{time.time() - begin_time} 秒，异步获取差异化配置成功: {json.dumps(filter_sensitive_info(private_config), ensure_ascii=False)}"
                )
                self.need_bind = False
                self.bind_completed_event.set()
            except DeviceNotFoundException as e:
                self.need_bind = True
                private_config = {}
            except DeviceBindException as e:
                self.need_bind = True
                self.bind_code = e.bind_code
                private_config = {}
            except Exception as e:
                self.need_bind = True
                self.logger.bind(tag=TAG).error(f"异步获取差异化配置失败: {e}")
                private_config = {}

        init_llm, init_tts, init_memory, init_intent = (
            False,
            False,
            False,
            False,
        )

        init_vad = check_vad_update(self.common_config, private_config)
        init_asr = check_asr_update(self.common_config, private_config)

        if init_vad:
            self.config["VAD"] = private_config["VAD"]
            self.config["selected_module"]["VAD"] = private_config["selected_module"][
                "VAD"
            ]
        if init_asr:
            self.config["ASR"] = private_config["ASR"]
            self.config["selected_module"]["ASR"] = private_config["selected_module"][
                "ASR"
            ]
        if private_config.get("TTS", None) is not None:
            init_tts = True
            self.config["TTS"] = private_config["TTS"]
            self.config["selected_module"]["TTS"] = private_config["selected_module"][
                "TTS"
            ]
        if private_config.get("LLM", None) is not None:
            init_llm = True
            self.config["LLM"] = private_config["LLM"]
            self.config["selected_module"]["LLM"] = private_config["selected_module"][
                "LLM"
            ]
        if private_config.get("VLLM", None) is not None:
            self.config["VLLM"] = private_config["VLLM"]
            self.config["selected_module"]["VLLM"] = private_config["selected_module"][
                "VLLM"
            ]
        if private_config.get("Memory", None) is not None:
            init_memory = True
            self.config["Memory"] = private_config["Memory"]
            self.config["selected_module"]["Memory"] = private_config[
                "selected_module"
            ]["Memory"]
        if private_config.get("Intent", None) is not None:
            init_intent = True
            self.config["Intent"] = private_config["Intent"]
            model_intent = private_config.get("selected_module", {}).get("Intent", {})
            self.config["selected_module"]["Intent"] = model_intent
            # 加载插件配置
            if model_intent != "Intent_nointent":
                plugin_from_server = private_config.get("plugins", {})
                for plugin, config_str in plugin_from_server.items():
                    plugin_from_server[plugin] = json.loads(config_str)
                self.config["plugins"] = plugin_from_server
                self.config["Intent"][self.config["selected_module"]["Intent"]][
                    "functions"
                ] = plugin_from_server.keys()
        if private_config.get("prompt", None) is not None:
            self.config["prompt"] = private_config["prompt"]
        # 获取声纹信息
        if private_config.get("voiceprint", None) is not None:
            self.config["voiceprint"] = private_config["voiceprint"]
        if private_config.get("summaryMemory", None) is not None:
            self.config["summaryMemory"] = private_config["summaryMemory"]
        if private_config.get("device_max_output_size", None) is not None:
            self.max_output_size = int(private_config["device_max_output_size"])
        if private_config.get("chat_history_conf", None) is not None:
            self.chat_history_conf = int(private_config["chat_history_conf"])
        if private_config.get("mcp_endpoint", None) is not None:
            self.config["mcp_endpoint"] = private_config["mcp_endpoint"]
        if private_config.get("context_providers", None) is not None:
            self.config["context_providers"] = private_config["context_providers"]

        # 使用 run_in_executor 在线程池中执行 initialize_modules，避免阻塞主循环
        try:
            modules = await self.loop.run_in_executor(
                None,  # 使用默认线程池
                initialize_modules,
                self.logger,
                private_config,
                init_vad,
                init_asr,
                init_llm,
                init_tts,
                init_memory,
                init_intent,
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"初始化组件失败: {e}")
            modules = {}
        if modules.get("tts", None) is not None:
            self.tts = modules["tts"]
        if modules.get("vad", None) is not None:
            self.vad = modules["vad"]
        if modules.get("asr", None) is not None:
            self.asr = modules["asr"]
        if modules.get("llm", None) is not None:
            self.llm = modules["llm"]
        if modules.get("intent", None) is not None:
            self.intent = modules["intent"]
        if modules.get("memory", None) is not None:
            self.memory = modules["memory"]

    def _initialize_memory(self):
        if self.memory is None:
            return
        """初始化记忆模块"""
        self.memory.init_memory(
            role_id=self.device_id,
            llm=self.llm,
            summary_memory=self.config.get("summaryMemory", None),
            save_to_file=not self.read_config_from_api,
        )

        # 获取记忆总结配置
        memory_config = self.config["Memory"]
        memory_type = self.config["Memory"][self.config["selected_module"]["Memory"]][
            "type"
        ]
        # 如果使用 nomen，直接返回
        if memory_type == "nomem":
            return
        # 使用 mem_local_short 模式
        elif memory_type == "mem_local_short":
            memory_llm_name = memory_config[self.config["selected_module"]["Memory"]][
                "llm"
            ]
            if memory_llm_name and memory_llm_name in self.config["LLM"]:
                # 如果配置了专用LLM，则创建独立的LLM实例
                from core.utils import llm as llm_utils

                memory_llm_config = self.config["LLM"][memory_llm_name]
                memory_llm_type = memory_llm_config.get("type", memory_llm_name)
                memory_llm = llm_utils.create_instance(
                    memory_llm_type, memory_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"为记忆总结创建了专用LLM: {memory_llm_name}, 类型: {memory_llm_type}"
                )
                self.memory.set_llm(memory_llm)
            else:
                # 否则使用主LLM
                self.memory.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("使用主LLM作为意图识别模型")

    def _initialize_intent(self):
        if self.intent is None:
            return
        self.intent_type = self.config["Intent"][
            self.config["selected_module"]["Intent"]
        ]["type"]
        if self.intent_type == "function_call" or self.intent_type == "intent_llm":
            self.load_function_plugin = True
        """初始化意图识别模块"""
        # 获取意图识别配置
        intent_config = self.config["Intent"]
        intent_type = self.config["Intent"][self.config["selected_module"]["Intent"]][
            "type"
        ]

        # 如果使用 nointent，直接返回
        if intent_type == "nointent":
            return
        # 使用 intent_llm 模式
        elif intent_type == "intent_llm":
            intent_llm_name = intent_config[self.config["selected_module"]["Intent"]][
                "llm"
            ]

            if intent_llm_name and intent_llm_name in self.config["LLM"]:
                # 如果配置了专用LLM，则创建独立的LLM实例
                from core.utils import llm as llm_utils

                intent_llm_config = self.config["LLM"][intent_llm_name]
                intent_llm_type = intent_llm_config.get("type", intent_llm_name)
                intent_llm = llm_utils.create_instance(
                    intent_llm_type, intent_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"为意图识别创建了专用LLM: {intent_llm_name}, 类型: {intent_llm_type}"
                )
                self.intent.set_llm(intent_llm)
            else:
                # 否则使用主LLM
                self.intent.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("使用主LLM作为意图识别模型")

        """加载统一工具处理器"""
        self.func_handler = UnifiedToolHandler(self)

        # 异步初始化工具处理器
        if hasattr(self, "loop") and self.loop:
            asyncio.run_coroutine_threadsafe(self.func_handler._initialize(), self.loop)

    def change_system_prompt(self, prompt):
        self.prompt = prompt
        # 更新系统prompt至上下文
        self.dialogue.update_system_message(self.prompt)

    def chat(self, query, depth=0):
        if query is not None:
            self.logger.bind(tag=TAG).info(f"大模型收到用户消息: {query}")

        # 为最顶层时新建会话ID和发送FIRST请求
        if depth == 0:
            # 检查是否已被取消（被新的 chat() 任务取代）
            if self.client_abort:
                self.logger.bind(tag=TAG).info("chat() 启动时已被取消，直接退出")
                return None
            
            self.llm_finish_task = False
            self.sentence_id = str(uuid.uuid4().hex)
            self.dialogue.put(Message(role="user", content=query))
            
            # llm_cancel_event 已在 receiveAudioHandle 中创建
            # 这里不再重复创建，确保使用正确的事件
            
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )
            # 重置延迟监控
            if self.latency_metrics:
                self.latency_metrics.reset()

        # 设置最大递归深度，避免无限循环，可根据实际需求调整
        MAX_DEPTH = 5
        force_final_answer = False  # 标记是否强制最终回答

        if depth >= MAX_DEPTH:
            self.logger.bind(tag=TAG).debug(
                f"已达到最大工具调用深度 {MAX_DEPTH}，将强制基于现有信息回答"
            )
            force_final_answer = True
            # 添加系统指令，要求 LLM 基于现有信息回答
            self.dialogue.put(
                Message(
                    role="user",
                    content="[系统提示] 已达到最大工具调用次数限制，请你基于目前已经获取的所有信息，直接给出最终答案。不要再尝试调用任何工具。",
                )
            )

        # Define intent functions
        functions = None
        # 达到最大深度时，禁用工具调用，强制 LLM 直接回答
        if (
            self.intent_type == "function_call"
            and hasattr(self, "func_handler")
            and not force_final_answer
        ):
            functions = self.func_handler.get_functions()
        response_message = []

        try:
            # 使用带记忆的对话
            memory_str = None
            if self.memory is not None:
                future = asyncio.run_coroutine_threadsafe(
                    self.memory.query_memory(query), self.loop
                )
                try:
                    # 添加10秒超时保护，避免 memory 查询无限等待
                    memory_str = future.result(timeout=10.0)
                except TimeoutError:
                    self.logger.bind(tag=TAG).warning(
                        f"memory.query_memory 超时(10s), 继续使用空记忆"
                    )
                    memory_str = None
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"memory.query_memory 异常: {e}")
                    memory_str = None

            # 记录 LLM 请求时间
            if self.latency_metrics and depth == 0:
                self.latency_metrics.mark_llm_request()

            if self.intent_type == "function_call" and functions is not None:
                # 使用支持functions的streaming接口
                llm_responses = self.llm.response_with_functions(
                    self.session_id,
                    self.dialogue.get_llm_dialogue_with_memory(
                        memory_str, self.config.get("voiceprint", {})
                    ),
                    functions=functions,
                )
            else:
                llm_responses = self.llm.response(
                    self.session_id,
                    self.dialogue.get_llm_dialogue_with_memory(
                        memory_str, self.config.get("voiceprint", {})
                    ),
                )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LLM 处理出错 {query}: {e}")
            return None

        # 处理流式响应
        tool_call_flag = False
        # 支持多个并行工具调用 - 使用列表存储
        tool_calls_list = []  # 格式: [{"id": "", "name": "", "arguments": ""}]
        content_arguments = ""
        # 注意：client_abort 已在 chat() 开始时重置，这里不再重复设置
        # 以避免覆盖并发任务取消时设置的状态
        llm_first_token_recorded = False  # 标记是否已记录首 token 时间
        
        # 表情处理相关变量
        expression_flag = True  # 是否需要提取表情（每轮只提取一次）
        expression_buffer = ""  # 用于累积文本，确保能完整提取 [expr:xxx] 标签
        expression_extracted = False  # 表情是否已提取
        
        response_count = 0
        for response in llm_responses:
            response_count += 1
            # 检查是否被取消或打断
            if self.client_abort or (self.llm_cancel_event and self.llm_cancel_event.is_set()):
                self.logger.bind(tag=TAG).info(f"LLM 请求被取消 (response_count={response_count}, client_abort={self.client_abort}, event_set={self.llm_cancel_event.is_set() if self.llm_cancel_event else 'None'})")
                break
            
            # 记录首 token 时间
            if not llm_first_token_recorded and self.latency_metrics and depth == 0:
                self.latency_metrics.mark_llm_first_token()
                llm_first_token_recorded = True
            if self.intent_type == "function_call" and functions is not None:
                content, tools_call = response
                if "content" in response:
                    content = response["content"]
                    tools_call = None
                if content is not None and len(content) > 0:
                    content_arguments += content

                if not tool_call_flag and content_arguments.startswith("<tool_call>"):
                    # print("content_arguments", content_arguments)
                    tool_call_flag = True

                if tools_call is not None and len(tools_call) > 0:
                    tool_call_flag = True
                    self._merge_tool_calls(tool_calls_list, tools_call)
            else:
                content = response

            if content is not None and len(content) > 0:
                if not tool_call_flag:
                    # 表情标签处理逻辑
                    if expression_flag and not expression_extracted:
                        expression_buffer += content
                        
                        # 检查是否有完整的表情标签 [expr:xxx]
                        if expressionUtils.has_expression_tag(expression_buffer):
                            # 提取表情并发送
                            expression_name, clean_text = expressionUtils.extract_expression(expression_buffer)
                            if expression_name:
                                asyncio.run_coroutine_threadsafe(
                                    expressionUtils.send_expression(self, expression_name),
                                    self.loop,
                                )
                            expression_extracted = True
                            expression_flag = False
                            
                            # 发送清理后的文本到 TTS（如果有内容）
                            if clean_text.strip():
                                response_message.append(clean_text)
                                self.tts.tts_text_queue.put(
                                    TTSMessageDTO(
                                        sentence_id=self.sentence_id,
                                        sentence_type=SentenceType.MIDDLE,
                                        content_type=ContentType.TEXT,
                                        content_detail=clean_text,
                                    )
                                )
                            expression_buffer = ""  # 清空缓冲区
                            continue
                        
                        # 检查是否有不完整的标签（正在接收中）
                        elif expressionUtils.has_incomplete_expression_tag(expression_buffer):
                            # 继续等待更多内容
                            continue
                        
                        # 累积超过 30 字符还没有表情标签，说明这轮回复没有表情
                        elif len(expression_buffer) > 30:
                            expression_flag = False
                            # 发送累积的内容
                            response_message.append(expression_buffer)
                            self.tts.tts_text_queue.put(
                                TTSMessageDTO(
                                    sentence_id=self.sentence_id,
                                    sentence_type=SentenceType.MIDDLE,
                                    content_type=ContentType.TEXT,
                                    content_detail=expression_buffer,
                                )
                            )
                            expression_buffer = ""
                            continue
                        else:
                            # 继续累积
                            continue
                    
                    # 正常发送文本（已提取过表情或无表情标签）
                    response_message.append(content)
                    self.tts.tts_text_queue.put(
                        TTSMessageDTO(
                            sentence_id=self.sentence_id,
                            sentence_type=SentenceType.MIDDLE,
                            content_type=ContentType.TEXT,
                            content_detail=content,
                        )
                    )
        # 记录 LLM 响应循环结束
        self.logger.bind(tag=TAG).info(f"LLM 响应循环结束: expression_buffer长度={len(expression_buffer)}, tool_call_flag={tool_call_flag}, response_message长度={len(response_message)}")
        
        # 处理 expression_buffer 中未发送的内容
        # 当 LLM 响应结束时，如果 buffer 中还有未处理的内容，需要发送到 TTS
        if expression_buffer and not tool_call_flag:
            self.logger.bind(tag=TAG).info(f"发送 expression_buffer 剩余内容到 TTS: {expression_buffer[:50]}...")
            response_message.append(expression_buffer)
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.MIDDLE,
                    content_type=ContentType.TEXT,
                    content_detail=expression_buffer,
                )
            )

        # 处理function call
        if tool_call_flag:
            bHasError = False
            # 处理基于文本的工具调用格式
            if len(tool_calls_list) == 0 and content_arguments:
                a = extract_json_from_string(content_arguments)
                if a is not None:
                    try:
                        content_arguments_json = json.loads(a)
                        tool_calls_list.append(
                            {
                                "id": str(uuid.uuid4().hex),
                                "name": content_arguments_json["name"],
                                "arguments": json.dumps(
                                    content_arguments_json["arguments"],
                                    ensure_ascii=False,
                                ),
                            }
                        )
                    except Exception as e:
                        bHasError = True
                        response_message.append(a)
                else:
                    bHasError = True
                    response_message.append(content_arguments)
                if bHasError:
                    self.logger.bind(tag=TAG).error(
                        f"function call error: {content_arguments}"
                    )

            if not bHasError and len(tool_calls_list) > 0:
                # 如需要大模型先处理一轮，添加相关处理后的日志情况
                if len(response_message) > 0:
                    text_buff = "".join(response_message)
                    self.tts_MessageText = text_buff
                    self.dialogue.put(Message(role="assistant", content=text_buff))
                response_message.clear()

                self.logger.bind(tag=TAG).debug(
                    f"检测到 {len(tool_calls_list)} 个工具调用"
                )

                # 收集所有工具调用的 Future
                futures_with_data = []
                for tool_call_data in tool_calls_list:
                    self.logger.bind(tag=TAG).debug(
                        f"function_name={tool_call_data['name']}, function_id={tool_call_data['id']}, function_arguments={tool_call_data['arguments']}"
                    )

                    future = asyncio.run_coroutine_threadsafe(
                        self.func_handler.handle_llm_function_call(
                            self, tool_call_data
                        ),
                        self.loop,
                    )
                    futures_with_data.append((future, tool_call_data))

                # 等待协程结束，同时检查打断状态
                tool_results = []
                tool_errors = []
                for future, tool_call_data in futures_with_data:
                    # 使用带超时的等待，以便定期检查打断状态
                    while True:
                        # 检查是否被打断
                        if self.client_abort or (self.llm_cancel_event and self.llm_cancel_event.is_set()):
                            self.logger.bind(tag=TAG).info("工具调用期间检测到打断，取消处理")
                            # 取消所有未完成的 future
                            for f, _ in futures_with_data:
                                if not f.done():
                                    f.cancel()
                            return None
                        
                        try:
                            result = future.result(timeout=0.5)  # 500ms 超时
                            tool_results.append((result, tool_call_data))
                            break
                        except (TimeoutError, Exception) as e:
                            # 检查是否是真正的超时（concurrent.futures.TimeoutError）
                            if type(e).__name__ == 'TimeoutError' or 'TimeoutError' in type(e).__name__:
                                # 超时后继续循环检查打断状态
                                continue
                            else:
                                # 其他异常，记录并跳出
                                import traceback
                                self.logger.bind(tag=TAG).error(f"工具调用异常: {e}\n{traceback.format_exc()}")
                                tool_errors.append((tool_call_data.get("name", "unknown"), str(e)))
                                break
                
                # 如果有工具调用错误且没有成功的结果，发送错误提示给用户
                if tool_errors and not tool_results:
                    error_msg = "抱歉，我在执行任务时遇到了一些问题，请稍后再试。"
                    self.tts.tts_text_queue.put(
                        TTSMessageDTO(
                            sentence_id=self.sentence_id,
                            sentence_type=SentenceType.MIDDLE,
                            content_type=ContentType.TEXT,
                            content_detail=error_msg,
                        )
                    )
                    response_message.append(error_msg)

                # 统一处理所有工具调用结果
                if tool_results:
                    self._handle_function_result(tool_results, depth=depth)

        # 存储对话内容
        if len(response_message) > 0:
            text_buff = "".join(response_message)
            self.tts_MessageText = text_buff
            self.dialogue.put(Message(role="assistant", content=text_buff))
        if depth == 0:
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )
            self.llm_finish_task = True
            # 使用lambda延迟计算，只有在DEBUG级别时才执行get_llm_dialogue()
            self.logger.bind(tag=TAG).debug(
                lambda: json.dumps(
                    self.dialogue.get_llm_dialogue(), indent=4, ensure_ascii=False
                )
            )

        return True

    def _handle_function_result(self, tool_results, depth):
        need_llm_tools = []

        for result, tool_call_data in tool_results:
            if result.action in [
                Action.RESPONSE,
                Action.NOTFOUND,
                Action.ERROR,
            ]:  # 直接回复前端
                text = result.response if result.response else result.result
                self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=text)
                self.dialogue.put(Message(role="assistant", content=text))
            elif result.action == Action.REQLLM:
                # 收集需要 LLM 处理的工具
                need_llm_tools.append((result, tool_call_data))
            else:
                pass

        if need_llm_tools:
            all_tool_calls = [
                {
                    "id": tool_call_data["id"],
                    "function": {
                        "arguments": (
                            "{}"
                            if tool_call_data["arguments"] == ""
                            else tool_call_data["arguments"]
                        ),
                        "name": tool_call_data["name"],
                    },
                    "type": "function",
                    "index": idx,
                }
                for idx, (_, tool_call_data) in enumerate(need_llm_tools)
            ]
            self.dialogue.put(Message(role="assistant", tool_calls=all_tool_calls))

            for result, tool_call_data in need_llm_tools:
                text = result.result
                if text is not None and len(text) > 0:
                    self.dialogue.put(
                        Message(
                            role="tool",
                            tool_call_id=(
                                str(uuid.uuid4())
                                if tool_call_data["id"] is None
                                else tool_call_data["id"]
                            ),
                            content=text,
                        )
                    )

            self.chat(None, depth=depth + 1)

    def _report_worker(self):
        """聊天记录上报工作线程"""
        while not self.stop_event.is_set():
            try:
                # 从队列获取数据，设置超时以便定期检查停止事件
                item = self.report_queue.get(timeout=1)
                if item is None:  # 检测毒丸对象
                    break
                try:
                    # 检查线程池状态
                    if self.executor is None:
                        continue
                    # 提交任务到线程池
                    self.executor.submit(self._process_report, *item)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"聊天记录上报线程异常: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"聊天记录上报工作线程异常: {e}")

        self.logger.bind(tag=TAG).info("聊天记录上报线程已退出")

    def _process_report(self, type, text, audio_data, report_time):
        """处理上报任务"""
        try:
            # 执行异步上报（在事件循环中运行）
            asyncio.run(report(self, type, text, audio_data, report_time))
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"上报处理异常: {e}")
        finally:
            # 标记任务完成
            self.report_queue.task_done()

    def clearSpeakStatus(self):
        self.client_is_speaking = False
        self.logger.bind(tag=TAG).debug(f"清除服务端讲话状态")

    # ==================== 通道发送方法（新增） ====================

    async def send_audio_via_channel(self, audio_data: bytes, timestamp: int = 0, sequence: int = 0) -> None:
        """
        通过通道发送音频包
        
        自动适配不同通道类型的发送格式：
        - WebSocket 直连：纯 Opus 数据
        - MQTT 网关：16 字节头部 + Opus 数据
        
        Args:
            audio_data: Opus 编码的音频数据
            timestamp: 时间戳（毫秒）
            sequence: 序列号
        """
        if self.channel and not self.channel.is_closed:
            packet = AudioPacket(data=audio_data, timestamp=timestamp, sequence=sequence)
            await self.channel.send_audio(packet)
        elif self.websocket:
            # 降级：使用旧方式（兼容）
            await self.websocket.send(audio_data)

    async def send_text_via_channel(self, message: str) -> None:
        """
        通过通道发送文本消息
        
        Args:
            message: 文本消息（通常是 JSON 字符串）
        """
        if self.channel and not self.channel.is_closed:
            await self.channel.send_text(message)
        elif self.websocket:
            # 降级：使用旧方式（兼容）
            await self.websocket.send(message)

    async def send_json_via_channel(self, data: dict) -> None:
        """
        通过通道发送 JSON 消息
        
        Args:
            data: 字典对象
        """
        await self.send_text_via_channel(json.dumps(data, ensure_ascii=False))

    # ==================== 通道发送方法结束 ====================

    async def close(self, ws=None):
        """资源清理方法"""
        try:
            # 输出延迟指标摘要
            if self.latency_metrics:
                summary = self.latency_metrics.get_summary()
                if summary:
                    self.logger.bind(tag=TAG).info(f"会话延迟摘要: {summary}")
                remove_metrics(self.session_id)
                self.latency_metrics = None
            
            # 清理音频缓冲区
            if hasattr(self, "audio_buffer"):
                self.audio_buffer.clear()

            # 取消超时任务
            if self.timeout_task and not self.timeout_task.done():
                self.timeout_task.cancel()
                try:
                    await self.timeout_task
                except asyncio.CancelledError:
                    pass
                self.timeout_task = None

            # 清理工具处理器资源
            if hasattr(self, "func_handler") and self.func_handler:
                try:
                    await self.func_handler.cleanup()
                except Exception as cleanup_error:
                    self.logger.bind(tag=TAG).error(
                        f"清理工具处理器时出错: {cleanup_error}"
                    )

            # 触发停止事件
            if self.stop_event:
                self.stop_event.set()

            # 清空任务队列
            self.clear_queues()

            # 关闭WebSocket连接
            try:
                if ws:
                    # 安全地检查WebSocket状态并关闭
                    try:
                        if hasattr(ws, "closed") and not ws.closed:
                            await ws.close()
                        elif hasattr(ws, "state") and ws.state.name != "CLOSED":
                            await ws.close()
                        else:
                            # 如果没有closed属性，直接尝试关闭
                            await ws.close()
                    except Exception:
                        # 如果关闭失败，忽略错误
                        pass
                elif self.websocket:
                    try:
                        if (
                            hasattr(self.websocket, "closed")
                            and not self.websocket.closed
                        ):
                            await self.websocket.close()
                        elif (
                            hasattr(self.websocket, "state")
                            and self.websocket.state.name != "CLOSED"
                        ):
                            await self.websocket.close()
                        else:
                            # 如果没有closed属性，直接尝试关闭
                            await self.websocket.close()
                    except Exception:
                        # 如果关闭失败，忽略错误
                        pass
            except Exception as ws_error:
                self.logger.bind(tag=TAG).error(f"关闭WebSocket连接时出错: {ws_error}")

            # 关闭通道（新增）
            if self.channel and not self.channel.is_closed:
                try:
                    await self.channel.close()
                    self.logger.bind(tag=TAG).debug("通道已关闭")
                except Exception as channel_error:
                    self.logger.bind(tag=TAG).error(f"关闭通道时出错: {channel_error}")

            # 关闭 TTS 资源（带超时保护，防止阻塞事件循环）
            if self.tts:
                try:
                    self.logger.bind(tag=TAG).debug("开始关闭 TTS 资源...")
                    await asyncio.wait_for(self.tts.close(), timeout=5.0)
                    self.logger.bind(tag=TAG).debug("TTS 资源关闭完成")
                except asyncio.TimeoutError:
                    self.logger.bind(tag=TAG).warning("TTS 资源关闭超时（5s），强制跳过")
                except Exception as tts_error:
                    self.logger.bind(tag=TAG).error(f"关闭 TTS 资源时出错: {tts_error}")

            # 最后关闭线程池（避免阻塞）
            if self.executor:
                try:
                    self.executor.shutdown(wait=False)
                except Exception as executor_error:
                    self.logger.bind(tag=TAG).error(
                        f"关闭线程池时出错: {executor_error}"
                    )
                self.executor = None
            self.logger.bind(tag=TAG).info("连接资源已释放")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"关闭连接时出错: {e}")
        finally:
            # 确保停止事件被设置
            if self.stop_event:
                self.stop_event.set()

    def clear_queues(self):
        """清空所有任务队列"""
        if self.tts:
            self.logger.bind(tag=TAG).debug(
                f"开始清理: TTS队列大小={self.tts.tts_text_queue.qsize()}, 音频队列大小={self.tts.tts_audio_queue.qsize()}"
            )

            # 使用非阻塞方式清空队列
            for q in [
                self.tts.tts_text_queue,
                self.tts.tts_audio_queue,
                self.report_queue,
            ]:
                if not q:
                    continue
                while True:
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        break

            # 重置音频流控器（取消后台任务并清空队列）
            if hasattr(self, "audio_rate_controller") and self.audio_rate_controller:
                self.audio_rate_controller.reset()
                self.logger.bind(tag=TAG).debug("已重置音频流控器")

            self.logger.bind(tag=TAG).debug(
                f"清理结束: TTS队列大小={self.tts.tts_text_queue.qsize()}, 音频队列大小={self.tts.tts_audio_queue.qsize()}"
            )

    def reset_vad_states(self):
        self.client_audio_buffer = bytearray()
        self.client_have_voice = False
        self.client_voice_stop = False
        self.logger.bind(tag=TAG).debug("VAD states reset.")

    def chat_and_close(self, text):
        """Chat with the user and then close the connection"""
        try:
            # Use the existing chat method
            self.chat(text)

            # After chat is complete, close the connection
            self.close_after_chat = True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Chat and close error: {str(e)}")

    async def _check_timeout(self):
        """检查连接超时"""
        check_count = 0
        try:
            while not self.stop_event.is_set():
                check_count += 1
                last_activity_time = self.last_activity_time
                if self.need_bind:
                    last_activity_time = self.first_activity_time

                # 检查是否超时（只有在时间戳已初始化的情况下）
                if last_activity_time > 0.0:
                    current_time = time.time() * 1000
                    idle_seconds = (current_time - last_activity_time) / 1000
                    
                    # 每30秒(3次检查)记录一次连接状态，便于诊断
                    if check_count % 3 == 0:
                        self.logger.bind(tag=TAG).debug(
                            f"连接状态: idle={idle_seconds:.1f}s, "
                            f"timeout={self.timeout_seconds}s, "
                            f"client_speaking={self.client_is_speaking}, "
                            f"need_bind={self.need_bind}"
                        )
                    
                    if idle_seconds > self.timeout_seconds:
                        if not self.stop_event.is_set():
                            self.logger.bind(tag=TAG).info(
                                f"连接超时，准备关闭 (idle={idle_seconds:.1f}s)"
                            )
                            # 设置停止事件，防止重复处理
                            self.stop_event.set()
                            # 使用 try-except 包装关闭操作，确保不会因为异常而阻塞
                            try:
                                await self.close(self.websocket)
                            except Exception as close_error:
                                self.logger.bind(tag=TAG).error(
                                    f"超时关闭连接时出错: {close_error}"
                                )
                        break
                # 每10秒检查一次，避免过于频繁
                await asyncio.sleep(10)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"超时检查任务出错: {e}")
        finally:
            self.logger.bind(tag=TAG).info(f"超时检查任务已退出 (总检查次数={check_count})")

    def _merge_tool_calls(self, tool_calls_list, tools_call):
        """合并工具调用列表

        Args:
            tool_calls_list: 已收集的工具调用列表
            tools_call: 新的工具调用
        """
        for tool_call in tools_call:
            tool_index = getattr(tool_call, "index", None)
            if tool_index is None:
                if tool_call.function.name:
                    # 有 function_name，说明是新的工具调用
                    tool_index = len(tool_calls_list)
                else:
                    tool_index = len(tool_calls_list) - 1 if tool_calls_list else 0

            # 确保列表有足够的位置
            if tool_index >= len(tool_calls_list):
                tool_calls_list.append({"id": "", "name": "", "arguments": ""})

            # 更新工具调用信息
            if tool_call.id:
                tool_calls_list[tool_index]["id"] = tool_call.id
            if tool_call.function.name:
                tool_calls_list[tool_index]["name"] = tool_call.function.name
            if tool_call.function.arguments:
                tool_calls_list[tool_index]["arguments"] += tool_call.function.arguments

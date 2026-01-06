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
)
from core.utils import textUtils
from typing import Dict, Any
from collections import deque
from core.utils.modules_initialize import (
    initialize_modules,
    initialize_tts,
    initialize_asr,
)
from core.utils import turn_detection as turn_detection_factory
from core.handle.reportHandle import report, enqueue_asr_report
from core.providers.tts.default import DefaultTTS
from concurrent.futures import ThreadPoolExecutor
from core.utils.dialogue import Message, Dialogue
from core.providers.asr.dto.dto import InterfaceType
from core.providers.tts.dto.dto import MessageTag
from core.providers.llm.base import LLMProviderBase
from core.providers.vad.base import VADStream, VADProviderBase
from core.handle.textHandle import handleTextMessage
from core.providers.tools.unified_tool_handler import UnifiedToolHandler
from plugins_func.loadplugins import auto_import_modules
from plugins_func.register import Action
from core.auth import AuthenticationError
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType
from config.logger import setup_logging, build_module_string, create_connection_logger
from core.utils.prompt_manager import PromptManager
from core.utils.voiceprint_provider import VoiceprintProvider
from config.live_agent_api_client import (
    get_agent_config_from_api,
    get_agent_config_cached,
    get_agent_by_wake_from_api,
    extract_user_id_from_jwt,
)
from core.utils import tokenize

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
        self.common_config = config
        self.config = copy.deepcopy(config)
        self.session_id = str(uuid.uuid4())
        self.logger = setup_logging()
        self.server = server  # 保存server实例的引用

        self.need_bind = False
        self.bind_code = None
        self.read_config_from_api = self.config.get("read_config_from_api", False)
        self.read_config_from_live_agent_api = self.config.get("read_config_from_live_agent_api", False)

        self.websocket = None
        self.headers = None
        self.device_id = None
        self.owner_id = None  # Device owner's user_id for memory storage
        self.client_ip = None
        self.client_timezone = "UTC+0"  # Client timezone (e.g., 'Asia/Shanghai', 'UTC+8')
        
        self.prompt = None
        self.welcome_msg = None
        self.max_output_size = 0
        self.chat_history_conf = 0
        self.audio_format = "opus"
        self.defer_agent_init = False
        # 首轮对话完成标志，用于禁用首轮对话期间的打断检测
        self.first_dialogue_completed = False

        # 客户端状态相关
        self.client_abort = False
        self.client_is_speaking = False
        self.client_listen_mode = "auto"

        # 线程任务相关
        self.loop = asyncio.get_event_loop()
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)

        # 添加上报线程池
        self.report_queue = queue.Queue()
        self.report_thread = None
        # Enable report for both manager-api and live-agent-api modes
        self._report_enabled = self.read_config_from_api or self.read_config_from_live_agent_api
        self.report_asr_enable = self._report_enabled
        self.report_tts_enable = self._report_enabled

        # 依赖的组件
        self.vad: VADProviderBase = None
        self.asr = None
        self.tts = None
        self.turn_detection = None  # Turn Detection provider (optional)
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
        self.last_activity_time = 0.0  # 统一的活动时间戳（毫秒）
        self.client_voice_stop = False
        self.last_is_voice = False
        self._vad_states = {}
        
        # Updated when VAD inference event detects speaking (milliseconds)
        self._last_speaking_time: int | None = None

        # asr相关变量
        # 因为实际部署时可能会用到公共的本地ASR，不能把变量暴露给公共ASR
        # 所以涉及到ASR的变量，需要在这里定义，属于connection的私有变量
        self.asr_audio = []
        self.asr_audio_queue = queue.Queue()
        self.input_audio_stream_ready = False
        # VAD stream instance (created per connection)
        self.vad_stream: VADStream = None
        # VAD event processor task
        self._vad_event_task = None
        
        # ASR text buffer for current turn (used for smart interrupt)
        # Accumulated ASR transcription text in current conversation turn
        self.asr_text_buffer: str = ""
        
        # Interruption Configuration
        # Only interrupt when both conditions are met:
        # 1. Speech duration >= min_interrupt_speech_duration_ms
        # 2. len(asr_text_buffer) >= min_interrupt_text_length
        self.enable_interruption: bool = self.config["Interruption"]["enabled"]
        self.min_interrupt_speech_duration_ms: float = self.config["Interruption"]["min_interrupt_speech_duration_ms"]
        self.min_interrupt_text_length: int = self.config["Interruption"]["min_interrupt_text_length"]

        # llm相关变量
        self.llm_finish_task = True
        self.dialogue = Dialogue()

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
        # identify the connection is from device-end (audio without header)
        self.conn_from_device = False

        # 初始化提示词管理器
        self.prompt_manager = PromptManager(config, self.logger)

        # agent-related configs
        self._instruction = None
        self._greeting_config = {
            "enable_greeting": False,
        }
        self._voice_closing = None
        self._language = None

        # reconnected flag
        self.reconnected: bool = False
        # memory
        self.relevant_memories_this_turn: str = "No relevant memories retrieved for this turn."
        self._memory_task = None  # Async task for memory prefetch
        
        # Agent 初始化就绪信号（用于解耦唤醒回复与初始化）
        # 唤醒词处理时先播放缓存音频，后台异步初始化 agent
        # 后续对话前通过此 Event 等待初始化完成
        self._agent_ready_event: asyncio.Event = asyncio.Event()
        self._agent_init_error: str | None = None  # 初始化错误信息

    async def handle_connection(self, ws):
        try:
            # 获取并验证headers
            self.headers = dict(ws.request.headers)
            real_ip = self.headers.get("x-real-ip") or self.headers.get(
                "x-forwarded-for"
            )
            if real_ip:
                self.client_ip = real_ip.split(",")[0].strip()
            else:
                self.client_ip = ws.remote_address[0]
            self.logger.bind(tag=TAG).info(
                f"{self.client_ip} conn - Headers: {self.headers}"
            )

            self.device_id = self.headers.get("device-id", None)
            self.agent_id = self.headers.get("agent-id", None)
            self.client_timezone = self.headers.get("timezone", "UTC+0")
            
            # Extract user_id from JWT token (if live-agent-api secret_key configured)
            # This enables proper memory initialization with the real user identity
            auth_header = self.headers.get("authorization", "")
            if auth_header and self.read_config_from_live_agent_api:
                jwt_user_id = extract_user_id_from_jwt(auth_header, self.config)
                if jwt_user_id:
                    self.owner_id = jwt_user_id
                    self.logger.bind(tag=TAG).info(
                        f"Extracted owner_id from JWT: {jwt_user_id[:20]}..."
                    )

            # 认证通过,继续处理
            self.websocket = ws

            # check if the connection is reconnected by the mobile-end
            self.reconnected = self.headers.get("reconnected", "0") == "1"
            self.logger.bind(tag=TAG).debug(f"reconnected: {self.reconnected}")
            # 检查是否来自MQTT连接
            request_path = ws.request.path
            self.conn_from_mqtt_gateway = request_path.endswith("?from=mqtt_gateway")
            if self.conn_from_mqtt_gateway:
                self.logger.bind(tag=TAG).info("连接来自:MQTT网关")
            
            # Device-end connection: no agent_id in headers (audio without header)
            self.conn_from_device = not self.agent_id
            if self.conn_from_device:
                self.logger.bind(tag=TAG).info("connection is from device-end (audio without header)")

            # 初始化活动时间戳
            self.last_activity_time = time.time() * 1000

            # 启动超时检查任务
            self.timeout_task = asyncio.create_task(self._check_timeout())

            # todo: welcome message need to be set after private config is loaded
            self.welcome_msg = self.config["xiaozhi"]
            self.welcome_msg["session_id"] = self.session_id

            # 获取差异化配置
            # asynchronous initialize
            # self._initialize_agent_config()
            # 异步初始化
            self.executor.submit(self._initialize_components)

            try:
                async for message in self.websocket:
                    await self._route_message(message)
            except websockets.exceptions.ConnectionClosed as cc:
                # 详细记录连接关闭信息
                close_code_desc = {
                    1000: "正常关闭",
                    1001: "端点离开",
                    1002: "协议错误",
                    1003: "不支持的数据类型",
                    1005: "未收到关闭码",
                    1006: "异常关闭（网络问题）",
                    1007: "数据类型不一致",
                    1008: "策略违规",
                    1009: "消息过大",
                    1011: "服务器意外错误",
                    1012: "服务重启",
                    1015: "TLS握手失败",
                }.get(cc.code, f"未知({cc.code})")
                
                self.logger.bind(tag=TAG).info(
                    f"🔌 [WS断开] Device={self.device_id} | IP={self.client_ip} | "
                    f"关闭码={cc.code}({close_code_desc}) | 原因={cc.reason or '无'}"
                )

        except AuthenticationError as e:
            self.logger.bind(tag=TAG).error(f"Authentication failed: {str(e)}")
            return
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.bind(tag=TAG).error(
                f"❌ [连接错误] Device={self.device_id} | IP={self.client_ip} | "
                f"异常={type(e).__name__}: {str(e)}"
            )
            self.logger.bind(tag=TAG).debug(f"堆栈: {stack_trace}")
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
                # 准备上下文信息
                context = {
                    "session_id": self.session_id,
                    "device_id": self.device_id,
                    "user_id": self.owner_id,  # 设备所有者的 user_id
                    "mac_address": getattr(self, 'mac_address', None),
                    "agent_id": getattr(self, 'agent_id', None),
                }
                
                # 使用线程池异步保存记忆
                def save_memory_task():
                    try:
                        # 创建新事件循环（避免与主循环冲突）
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self.memory.save_memory(self.dialogue.dialogue, context)
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

    async def send_server_ready(self):
        """Send ready signal to client after ASR/VAD initialized.
        
        Client should wait for this message before sending audio data
        to avoid missing the first utterance.
        """
        try:
            ready_message = json.dumps({
                "type": "server",
                "state": "ready",
                "session_id": self.session_id,
            })
            await self.websocket.send(ready_message)
            self.logger.bind(tag=TAG).info("Sent server ready signal to client")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to send ready signal: {e}")

    async def _route_message(self, message):
        """消息路由"""
        if isinstance(message, str):
            await handleTextMessage(self, message)
        elif isinstance(message, bytes):
            if self.vad is None or self.asr is None:
                return

            # 调试日志：确认在 TTS 播放期间是否收到用户音频
            if self.client_is_speaking:
                # 每50个包记录一次，避免日志过多
                if not hasattr(self, '_audio_recv_count_during_tts'):
                    self._audio_recv_count_during_tts = 0
                    self._audio_bytes_during_tts = 0
                self._audio_recv_count_during_tts += 1
                self._audio_bytes_during_tts += len(message)
                if self._audio_recv_count_during_tts % 50 == 1:
                    self.logger.bind(tag=TAG).debug(
                        f"📥 [打断调试] TTS播放期间收到音频包: count={self._audio_recv_count_during_tts}, "
                        f"this_bytes={len(message)}, total_bytes={self._audio_bytes_during_tts}"
                    )
            else:
                # TTS 结束后重置计数
                if hasattr(self, '_audio_recv_count_during_tts') and self._audio_recv_count_during_tts > 0:
                    self.logger.bind(tag=TAG).debug(
                        f"📥 [打断调试] TTS播放期间共收到 {self._audio_recv_count_during_tts} 个音频包, "
                        f"总字节数={self._audio_bytes_during_tts}"
                    )
                    self._audio_recv_count_during_tts = 0
                    self._audio_bytes_during_tts = 0

            # 处理来自MQTT网关的音频包
            if self.conn_from_mqtt_gateway and len(message) >= 16:
                handled = await self._process_mqtt_audio_message(message)
                if handled:
                    return

            # 不需要头部处理或没有头部时，直接处理原始消息
            
            self.asr_audio_queue.put(message)

    async def _process_mqtt_audio_message(self, message):
        """
        处理来自MQTT网关的音频消息，解析16字节头部并提取音频数据

        Args:
            message: 包含头部的音频消息

        Returns:
            bool: 是否成功处理了消息
        """
        try:
            # 提取头部信息
            timestamp = int.from_bytes(message[8:12], "big")
            audio_length = int.from_bytes(message[12:16], "big")

            # 提取音频数据
            if audio_length > 0 and len(message) >= 16 + audio_length:
                # 有指定长度，提取精确的音频数据
                audio_data = message[16 : 16 + audio_length]
                # 基于时间戳进行排序处理
                self._process_websocket_audio(audio_data, timestamp)
                return True
            elif len(message) > 16:
                # 没有指定长度或长度无效，去掉头部后处理剩余数据
                audio_data = message[16:]
                self.asr_audio_queue.put(audio_data)
                return True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"解析WebSocket音频包失败: {e}")

        # 处理失败，返回False表示需要继续处理
        return False

    def _process_websocket_audio(self, audio_data, timestamp):
        """处理WebSocket格式的音频包"""
        # 初始化时间戳序列管理
        if not hasattr(self, "audio_timestamp_buffer"):
            self.audio_timestamp_buffer = {}
            self.last_processed_timestamp = 0
            self.max_timestamp_buffer_size = 20

        # 如果时间戳是递增的，直接处理
        if timestamp >= self.last_processed_timestamp:
            self.asr_audio_queue.put(audio_data)
            self.last_processed_timestamp = timestamp

            # 处理缓冲区中的后续包
            processed_any = True
            while processed_any:
                processed_any = False
                for ts in sorted(self.audio_timestamp_buffer.keys()):
                    if ts > self.last_processed_timestamp:
                        buffered_audio = self.audio_timestamp_buffer.pop(ts)
                        self.asr_audio_queue.put(buffered_audio)
                        self.last_processed_timestamp = ts
                        processed_any = True
                        break
        else:
            # 乱序包，暂存
            if len(self.audio_timestamp_buffer) < self.max_timestamp_buffer_size:
                self.audio_timestamp_buffer[timestamp] = audio_data
            else:
                self.asr_audio_queue.put(audio_data)

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
            self.selected_module_str = build_module_string(
                self.config.get("selected_module", {})
            )
            self.logger = create_connection_logger(self.selected_module_str)

            # when missing agent_id, we identify the request is from device-end rather app-side
            # 优化：即使没有 agent_id，也预初始化默认模块，减少首次对话延迟
            if self.read_config_from_live_agent_api and not self.agent_id:
                self.defer_agent_init = True
                self.logger.bind(tag=TAG).info(
                    "agent-id missing, pre-initializing default modules for faster first response"
                )
                # 预初始化默认的 LLM/TTS/ASR 模块（使用默认配置）
                try:
                    modules = initialize_modules(
                        self.logger,
                        self.config,
                        init_vad=False,  # VAD 使用公共实例
                        init_asr=True,
                        init_llm=True,
                        init_tts=True,
                        init_memory=False,
                        init_intent=False,
                    )
                    if modules.get("tts"):
                        self.tts = modules["tts"]
                    if modules.get("llm"):
                        self.llm = modules["llm"]
                    if modules.get("asr"):
                        self.asr = modules["asr"]
                    self.logger.bind(tag=TAG).info("Pre-initialized LLM/TTS/ASR modules successfully")
                except Exception as e:
                    self.logger.bind(tag=TAG).warning(f"Pre-initialization failed: {e}, will init on wake")
            else:
                self._initialize_agent_config()
            
            init_llm = True
            init_tts = True
            init_memory = not self.defer_agent_init
            init_intent = not self.defer_agent_init

            if init_tts and self.tts:
                open_tts_audio_future = asyncio.run_coroutine_threadsafe(
                    self.tts.open_audio_channels(self), self.loop
                )
                # wait for 2 seconds to open the audio channels
                open_tts_audio_future.result(timeout=2)

                # self.logger.bind(tag=TAG).info("TTS audio channels opened")
                # 预热唤醒词短回复缓存：确保首唤醒尽可能命中本地 wav（同音色、低时延）
                try:
                    from core.handle.helloHandle import prewarm_wakeup_reply_cache
                    asyncio.run_coroutine_threadsafe(
                        prewarm_wakeup_reply_cache(self), self.loop
                    )
                except Exception as e:
                    self.logger.bind(tag=TAG).debug(f"wakeup prewarm schedule failed: {e}")
                # once tts ready, we can initialize the report threads
                self._init_report_threads()

            # if greeting is enabled, we can send the opening message at once
            if self.tts and self._greeting_config["enable_greeting"]:
                greeting = self._greeting_config["greeting"]
                self.logger.bind(tag=TAG).debug(f"send the opening message: {greeting}")
                    
                opening_sentence_id = str(uuid.uuid4().hex)
                message_tag = MessageTag.OPENING
                # FIRST: Start session
                self.tts.tts_text_queue.put(TTSMessageDTO(
                    sentence_id=opening_sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                    message_tag=message_tag,
                ))

                self.tts.tts_text_queue.put(TTSMessageDTO(
                    sentence_id=str(uuid.uuid4().hex),
                    sentence_type=SentenceType.MIDDLE,
                    content_type=ContentType.TEXT,
                    content_detail=greeting,
                    message_tag=message_tag,
                    )
                )

                self.tts.tts_text_queue.put(TTSMessageDTO(
                    sentence_id=opening_sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                    message_tag=message_tag,
                ))

            # open audio channels for ASR
            # Initialize VAD stream for this connection
            self.vad = self._vad if self.vad is None else self.vad
            self._initialize_vad_stream()
            # Open ASR audio channels (sends ready signal to client when done)
            asyncio.run_coroutine_threadsafe(
                self.asr.open_audio_channels(self), self.loop
            )
            # 初始化声纹识别
            self._initialize_voiceprint()

            # Initialize Turn Detection (optional)
            self._initialize_turn_detection()

            # prewarm LLM first connection
            if init_llm and isinstance(self.llm, LLMProviderBase):
                self.llm.prewarm()

            """加载记忆"""
            if init_memory:
                self._initialize_memory()
            """加载意图识别"""
            if init_intent:
                self._initialize_intent()
            """更新系统提示词（必须在 TTS 初始化前，以便加载 role 的 TTS 配置）"""
            if init_tts or init_llm:
                self._init_prompt_enhancement()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"实例化组件失败: {e}")

    def _init_prompt_enhancement(self, skip_persona: bool = False):
        """初始化并更新系统提示词
        
        Args:
            skip_persona: 是否跳过用户画像加载（用于异步并行加载场景）
                - True: 立即返回基础 prompt，用户画像后台加载
                - False: 同步加载用户画像（默认行为，兼容现有调用）
        """
        # 更新上下文信息
        self.prompt_manager.update_context_info(self, self.client_ip)
        
        # 获取用户画像（如果 Memory 模块已初始化且未跳过）
        user_persona = None
        if not skip_persona and self.memory and hasattr(self.memory, 'get_user_persona'):
            try:
                user_persona = self.memory.get_user_persona(client_timezone=self.client_timezone)
                if user_persona:
                    self.logger.bind(tag=TAG).debug(f"获取到用户画像，长度: {len(user_persona)}")
            except Exception as e:
                self.logger.bind(tag=TAG).warning(f"获取用户画像失败: {e}")
        
        result = self.prompt_manager.build_enhanced_prompt(
            user_prompt=self._instruction,
            device_id=self.device_id,
            client_ip=self.client_ip,
            language=self._language,
            user_persona=user_persona,
            client_timezone=self.client_timezone,
        )
        
        # 解包返回值
        if isinstance(result, tuple):
            enhanced_prompt, role_tts_config = result
            # 保存 role 的 TTS 配置到 self.config（供 TTS 初始化使用）
            if role_tts_config:
                self.config["_role_tts_config"] = role_tts_config
                self.logger.bind(tag=TAG).info(
                    f"保存 Role TTS 配置到 config: {role_tts_config}"
                )
        else:
            # 兼容旧版本返回值（仅返回 prompt 字符串）
            enhanced_prompt = result
        
        if enhanced_prompt:
            # Store base prompt as template (with {relevant_memory} placeholder)
            self.base_prompt = enhanced_prompt
            # Initialize system prompt with empty memory placeholder
            initial_prompt = enhanced_prompt.replace(
                "{relevant_memory}", 
                "No relevant memories retrieved for this turn."
            )
            self.change_system_prompt(initial_prompt)
            self.logger.bind(tag=TAG).info("system prompt loaded")

    async def _load_user_persona_async(self):
        """后台异步加载用户画像
        
        在唤醒流程中启动，不阻塞唤醒响应。
        加载完成后自动更新 system prompt。
        """
        if not self.memory or not hasattr(self.memory, 'get_user_persona_async'):
            return
        
        # 防止重复加载
        if getattr(self, '_persona_loading', False):
            return
        
        self._persona_loading = True
        load_start = time.time() * 1000
        
        try:
            persona = await self.memory.get_user_persona_async(
                client_timezone=self.client_timezone
            )
            load_elapsed = time.time() * 1000 - load_start
            
            if persona:
                self._user_persona = persona
                self._update_system_prompt_with_persona(persona)
                self.logger.bind(tag=TAG).info(
                    f"✅ [后台] 用户画像加载完成: {load_elapsed:.0f}ms, 长度: {len(persona)}"
                )
            else:
                self.logger.bind(tag=TAG).debug(
                    f"[后台] 用户画像为空: {load_elapsed:.0f}ms"
                )
        except Exception as e:
            self.logger.bind(tag=TAG).warning(f"[后台] 用户画像加载失败: {e}")
        finally:
            self._persona_loading = False

    def _update_system_prompt_with_persona(self, persona: str):
        """使用用户画像更新 system prompt
        
        在后台画像加载完成后调用，将画像注入到 system prompt 中。
        
        Args:
            persona: 用户画像字符串
        """
        if not self.base_prompt:
            self.logger.bind(tag=TAG).warning("base_prompt 未初始化，无法更新用户画像")
            return
        
        # 检查是否有 {user_persona} 占位符
        if "{user_persona}" in self.base_prompt:
            # 有占位符，替换它
            updated_prompt = self.base_prompt.replace("{user_persona}", persona)
        else:
            # 没有占位符，追加到末尾（在 {relevant_memory} 占位符之前）
            # 找到合适的插入位置
            if "{relevant_memory}" in self.base_prompt:
                # 在 relevant_memory 占位符之前插入
                updated_prompt = self.base_prompt.replace(
                    "{relevant_memory}",
                    f"\n\n## 用户画像\n{persona}\n\n{{relevant_memory}}"
                )
            else:
                # 追加到末尾
                updated_prompt = f"{self.base_prompt}\n\n## 用户画像\n{persona}"
        
        # 更新 base_prompt（包含画像的版本）
        self.base_prompt = updated_prompt
        
        # 同时更新当前的 system prompt
        current_prompt = updated_prompt.replace(
            "{relevant_memory}",
            "No relevant memories retrieved for this turn."
        )
        self.change_system_prompt(current_prompt)
        self.logger.bind(tag=TAG).debug("system prompt 已更新（注入用户画像）")

    def _init_report_threads(self):
        """Initialize chat message report thread for live-agent-api"""
        # Only enable for live-agent-api mode
        if not self.read_config_from_live_agent_api or self.need_bind:
            return
        if self.chat_history_conf == 0:
            return
        if self.report_thread is None or not self.report_thread.is_alive():
            self.report_thread = threading.Thread(
                target=self._report_worker, daemon=True
            )
            self.report_thread.start()
            self.logger.bind(tag=TAG).info("Chat report thread started")

    def _initialize_tts(self):
        """
        初始化TTS（支持三级优先级配置）
        
        优先级：
        1. API 下发的 TTS 配置（在 _initialize_private_config 中已应用）
        2. Role 中的 TTS 配置
        3. selected_module.TTS（兜底配置）
        """
        tts = None
        if not self.need_bind:
            # 检查是否有 role 的 TTS 配置（优先级2）
            role_tts_config = self.config.get("_role_tts_config")
            self.logger.bind(tag=TAG).info(f"🔍 检查 _role_tts_config: {role_tts_config}")
            if role_tts_config:
                self.logger.bind(tag=TAG).info("✅ 发现 Role TTS 配置，准备应用")
                self._apply_role_tts_config(role_tts_config)
            else:
                self.logger.bind(tag=TAG).info("ℹ️  没有 Role TTS 配置，使用默认配置")
            
            # 初始化 TTS（优先级1和3在这里统一处理）
            tts = initialize_tts(self.config)

        if tts is None:
            tts = DefaultTTS(self.config, delete_audio_file=True)

        return tts
    
    def _apply_role_tts_config(self, role_tts_config: dict):
        """应用 role 中的 TTS 配置"""
        self.logger.bind(tag=TAG).debug(f"开始应用 Role TTS 配置: {role_tts_config}")
        provider = role_tts_config.get("provider")
        voice_id = role_tts_config.get("voice_id")
        
        if not provider or not voice_id:
            self.logger.bind(tag=TAG).warning("Role TTS 配置不完整，跳过应用")
            return
        
        # 检查当前 selected_module.TTS 是否已经被 API 覆盖
        # 如果 API 已经设置了 TTS，则不应用 role 配置（API 优先级更高）
        current_tts = self.config["selected_module"]["TTS"]
        if self.config.get("_api_tts_applied"):
            self.logger.bind(tag=TAG).info(
                f"API 已设置 TTS 配置（优先级1），跳过 Role TTS 配置: {provider}"
            )
            return
        
        # 应用 role 的 TTS 配置
        # 根据 provider 映射到实际的 TTS 模块名
        tts_module_map = {
            "elevenlabs": "ElevenLabsSDK",
            "cartesia": "CartesiaSDK",
            "edge": "EdgeTTS",
            "doubao": "VolcanoStreamTTS",
            # 可以继续添加更多映射...
        }
        
        tts_module = tts_module_map.get(provider.lower())
        if not tts_module:
            self.logger.bind(tag=TAG).warning(
                f"未知的 TTS provider: {provider}，使用默认配置"
            )
            return
        
        # 检查该 TTS 模块是否在配置中存在
        if tts_module not in self.config.get("TTS", {}):
            self.logger.bind(tag=TAG).warning(
                f"TTS 模块 {tts_module} 未在配置中定义，跳过应用"
            )
            return
        
        # 更新 selected_module.TTS
        self.config["selected_module"]["TTS"] = tts_module
        
        # 更新 voice_id（如果该 TTS 模块支持）
        if "voice_id" in self.config["TTS"][tts_module]:
            self.config["TTS"][tts_module]["voice_id"] = voice_id
            self.logger.bind(tag=TAG).info(
                f"✅ 应用 Role TTS 配置: provider={provider}, "
                f"module={tts_module}, voice_id={voice_id[:16]}..."
            )
        else:
            self.logger.bind(tag=TAG).warning(
                f"TTS 模块 {tts_module} 不支持 voice_id 配置"
            )

    def _initialize_asr(self):
        """初始化ASR"""
        # 检查 _asr 是否为 None
        if self._asr is None:
            return initialize_asr(self.config)
        
        if self._asr.interface_type == InterfaceType.LOCAL:
            # 如果公共ASR是本地服务，则直接返回
            # 因为本地一个实例ASR，可以被多个连接共享
            asr = self._asr
        else:
            # 如果公共ASR是远程服务，则初始化一个新实例
            # 因为远程ASR，涉及到websocket连接和接收线程，需要每个连接一个实例
            asr = initialize_asr(self.config)

        return asr

    def _initialize_vad_stream(self):
        """Initialize VAD stream instance for this connection
        
        Only creates the VAD stream instance here (sync context).
        The stream's task and event processor are started later in
        open_audio_channels() which runs in async context.
        """
        try:
            # Create VAD stream for this connection
            # Note: stream() only creates the instance, task is started via start()
            self.vad_stream = self.vad.stream()
            self.logger.bind(tag=TAG).info("VAD stream instance created")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to create VAD stream: {e}")
            self.vad_stream = None

    def _initialize_turn_detection(self):
        """Initialize Turn Detection provider (optional)
        
        If TurnDetection is configured as "noop" type, turn_detection will be set to None
        to skip turn detection entirely. Otherwise, creates the configured provider.
        """
        try:
            selected_module = self.config.get("selected_module", {})
            turn_detection_module = selected_module.get("TurnDetection")
            
            if not turn_detection_module:
                self.logger.bind(tag=TAG).debug("TurnDetection not configured, skipping")
                self.turn_detection = None
                return
            
            turn_detection_config = self.config.get("TurnDetection", {}).get(turn_detection_module, {})
            turn_detection_type = turn_detection_config.get("type", "noop")
            
            # Create the turn detection provider (noop implementation handles disabled case)
            self.turn_detection = turn_detection_factory.create_instance(
                turn_detection_type,
                turn_detection_config
            )
            self.logger.bind(tag=TAG).info(
                f"TurnDetection initialized: {turn_detection_module} (type={turn_detection_type})"
            )
            
        except Exception as e:
            self.logger.bind(tag=TAG).warning(
                f"TurnDetection initialization failed: {e}, disabled"
            )
            self.turn_detection = None

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

    def _initialize_memory(self):
        if self.memory is None:
            return
        """初始化记忆模块"""
        # Use owner_id (real user_id) for memory storage, fallback to device_id if not available
        memory_user_id = self.owner_id if self.owner_id else self.device_id
        self.memory.init_memory(
            role_id=memory_user_id,
            llm=self.llm,
            agent_id=self.agent_id,
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

    def _initialize_agent_config(self):
        """initialize agent config from live-agent-api"""
        if not self.read_config_from_live_agent_api:
            # 非 live-agent-api 模式，直接标记 agent 就绪
            self._agent_ready_event.set()
            return
        # self.logger.bind(tag=TAG).info(f"get agent config from live-agent-api for {self.agent_id}")
        # 使用缓存版本，减少 API 调用延迟
        private_config = get_agent_config_cached(self.agent_id, self.config, self.headers.get("timezone", "UTC+0"))
        if not private_config:
            self.logger.bind(tag=TAG).error(f"Failed to get agent config for {self.agent_id}")
            return
        self._apply_agent_runtime_config(private_config)

        init_llm, init_tts, init_memory, init_intent = (
            True,
            True,
            False,
            False,
        )

        init_vad = False
        init_asr = True

        try:
            modules = initialize_modules(
                self.logger,
                self.config,
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
        
        # 同步初始化完成，标记 agent 就绪
        self._agent_ready_event.set()

    def _apply_agent_runtime_config(self, private_config: dict):
        """Apply agent-specific runtime config to connection"""
        if not private_config:
            return
        voice = private_config.get("voice")
        if voice:
            reference_id = voice.get("reference_id")  # Provider's voice ID (Fish/MiniMax)
            provider = voice.get("provider")
            if reference_id and provider:
                self._apply_voice_tts_config(provider, reference_id)
        self._instruction = private_config.get("instruction", self._instruction)
        # greeting config
        self._greeting_config["enable_greeting"] = private_config.get("enable_greeting", False)
        self._greeting_config["greeting"] = private_config.get("greeting", None)
        self._voice_closing = private_config.get("voice_closing", self._voice_closing)
        self._language = private_config.get("language", self._language)

        # Set chat history config for live-agent-api mode
        # 0: disable, 1: text only, 2: text + audio
        live_api_config = self.config.get("live-agent-api", {})
        self.chat_history_conf = live_api_config.get("chat_history_conf", 2)
        
        # Load recent conversation history for dialogue context
        recent_messages = private_config.get("recent_messages")
        if recent_messages:
            loaded = self.dialogue.load_history_messages(recent_messages)
            if loaded > 0:
                self.logger.bind(tag=TAG).info(f"Loaded {loaded} history messages for dialogue context")

    def _apply_voice_tts_config(self, provider: str, reference_id: str):
        """Apply TTS config based on voice provider
        
        Dynamically select TTS module based on voice provider from live-agent-api.
        
        Args:
            provider: TTS provider name (fishspeech, minimax)
            reference_id: Provider's voice ID (Fish Audio ID, MiniMax voice ID, etc.)
                         This is the downstream provider's voice identifier, not our voice_id.
        """
        # Provider to TTS module mapping
        # Use dual stream for better latency when available
        provider_tts_map = {
            "fishspeech": "FishSingleStreamTTS",
            "minimax": "MinimaxDualStreamTTS",  # WebSocket dual stream (lower latency)
        }
        
        provider_lower = provider.lower()
        if provider_lower not in provider_tts_map:
            self.logger.bind(tag=TAG).warning(
                f"Unknown TTS provider: {provider}, using default TTS config"
            )
            return
        
        tts_module = provider_tts_map[provider_lower]
        
        # Check if TTS module exists in config
        if tts_module not in self.config.get("TTS", {}):
            self.logger.bind(tag=TAG).warning(
                f"TTS module {tts_module} not defined in config, skipping"
            )
            return
        
        # Update selected TTS module
        self.config["selected_module"]["TTS"] = tts_module
        
        # Apply reference_id to TTS config based on provider
        # Note: Each TTS provider reads voice from different config keys:
        # - FishSpeech: reference_id
        # - MiniMax: voice_id (then applied to voice_setting internally)
        if provider_lower == "fishspeech":
            self.config["TTS"][tts_module]["reference_id"] = reference_id
        elif provider_lower == "minimax":
            self.config["TTS"][tts_module]["voice_id"] = reference_id
        
        self.logger.bind(tag=TAG).info(
            f"Applied voice TTS config: provider={provider}, "
            f"module={tts_module}, reference_id={reference_id[:20]}..."
        )
        
        # Mark that API has set TTS config (prevent role config from overriding)
        self.config["_api_tts_applied"] = True

    # ensure_agent_ready is used to ensure the agent is ready when the wake word is detected
    async def ensure_agent_ready(self, wake_word: str | None = None) -> bool:
        """
        Resolve agent when missing and apply agent config.
        模块已在连接时预初始化，这里只需要解析 agent 并应用配置。
        
        注意：此方法完成后会 set _agent_ready_event，供 startToChat 等待。
        """
        try:
            result = await self._do_ensure_agent_ready(wake_word)
            if result:
                self._agent_ready_event.set()
            else:
                self._agent_init_error = "Agent initialization failed"
                self._agent_ready_event.set()  # 即使失败也要 set，避免死锁
            return result
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"ensure_agent_ready exception: {e}")
            self._agent_init_error = str(e)
            self._agent_ready_event.set()  # 异常时也要 set，避免死锁
            return False

    async def _do_ensure_agent_ready(self, wake_word: str | None = None) -> bool:
        """
        实际执行 agent 初始化的内部方法。
        从 ensure_agent_ready 分离出来，便于错误处理和事件管理。
        """
        if not self.read_config_from_live_agent_api:
            return True
        if not self.defer_agent_init and self.tts and self.llm:
            return True

        init_start_time = time.time() * 1000
        self.logger.bind(tag=TAG).info("🚀 [后台初始化] 开始异步拉取 agent 配置...")

        private_config = None
        if not self.agent_id:
            resolved = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: get_agent_by_wake_from_api(
                    self.device_id, wake_word=wake_word, config=self.config
                )
            )
            if not resolved:
                self.logger.bind(tag=TAG).error(
                    f"Failed to resolve agent by wake_word for device {self.device_id}"
                )
                self.need_bind = True
                return False
            self.agent_id = resolved.get("agent_id")
            # Only set owner_id from API if not already extracted from JWT
            if not self.owner_id:
                self.owner_id = resolved.get("owner_id")  # Device owner's user_id
            private_config = resolved.get("agent_config")

        if private_config is None:
            # 使用缓存版本，减少 API 调用延迟
            private_config = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: get_agent_config_cached(self.agent_id, self.config)
            )
        if not private_config:
            self.logger.bind(tag=TAG).error(
                f"Failed to get agent config for {self.agent_id}"
            )
            return False

        api_elapsed = time.time() * 1000 - init_start_time
        self.logger.bind(tag=TAG).info(f"⚡ [后台初始化] API 调用完成: {api_elapsed:.0f}ms")

        self._apply_agent_runtime_config(private_config)
        self.defer_agent_init = False

        # 更新已预初始化的 TTS 实例的 reference_id（voice_id）
        # 因为预初始化时还没有 agent 配置，reference_id 为 null
        # voice_id 可能在顶层或嵌套在 voice 对象中
        voice_id = private_config.get("voice_id")
        if not voice_id:
            voice_config = private_config.get("voice", {})
            voice_id = voice_config.get("voice_id") or voice_config.get("reference_id")
        if voice_id and self.tts and hasattr(self.tts, "reference_id"):
            self.tts.reference_id = voice_id
            self.logger.bind(tag=TAG).info(f"✅ 更新 TTS reference_id: {voice_id[:16]}...")
            # voice 更新后，后台预热唤醒短回复缓存（避免首唤醒回退到固定录音）
            try:
                from core.handle.helloHandle import prewarm_wakeup_reply_cache
                asyncio.create_task(prewarm_wakeup_reply_cache(self))
            except Exception as e:
                self.logger.bind(tag=TAG).debug(f"wakeup prewarm(schedule after voice update) failed: {e}")

        # 模块已在连接时预初始化，这里只需要确保 ASR 和 VAD stream 就绪
        # 只有在模块未初始化时才重新初始化（正常情况下不会进入）
        if not self.llm or not self.tts:
            self.logger.bind(tag=TAG).warning("Modules not pre-initialized, initializing now...")
            try:
                modules = initialize_modules(
                    self.logger,
                    self.config,
                    init_vad=False,  # VAD 使用公共实例
                    init_asr=True,   # ASR 需要初始化！
                    init_llm=True,
                    init_tts=True,
                    init_memory=False,
                    init_intent=False,
                )
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"初始化组件失败: {e}")
                modules = {}
            if modules.get("llm", None) is not None:
                self.llm = modules["llm"]
                if isinstance(self.llm, LLMProviderBase):
                    self.llm.prewarm()
            if modules.get("tts", None) is not None:
                self.tts = modules["tts"]
                asyncio.run_coroutine_threadsafe(
                    self.tts.open_audio_channels(self), self.loop
                )
            if modules.get("asr", None) is not None:
                self.asr = modules["asr"]
            if modules.get("intent", None) is not None:
                self.intent = modules["intent"]
            if modules.get("memory", None) is not None:
                self.memory = modules["memory"]

        # 初始化 VAD stream（使用公共 VAD 实例）
        if self.vad is None:
            self.vad = self._vad
        if self.vad is not None and self.vad_stream is None:
            self._initialize_vad_stream()
        
        # 打开 ASR 音频通道（如果尚未打开）
        if self.asr is not None:
            asyncio.run_coroutine_threadsafe(
                self.asr.open_audio_channels(self), self.loop
            )
        
        # 初始化 Memory（必须在 owner_id 设置后）

        if self.memory and not getattr(self.memory, 'role_id', None):
            self.logger.bind(tag=TAG).debug(
                f"Initializing Memory with owner_id={self.owner_id or self.device_id}"
            )
            self._initialize_memory()
        
        # Phase 6 优化：异步并行加载用户画像
        # 1. 使用 skip_persona=True 跳过同步画像加载，立即返回基础 prompt
        # 2. 启动后台任务异步加载用户画像，完成后更新 system prompt
        # 预期收益：唤醒延迟从 ~3s 降低到 ~500ms
        self._init_prompt_enhancement(skip_persona=True)
        
        # 启动后台任务异步加载用户画像（不阻塞唤醒流程）
        if self.memory and hasattr(self.memory, 'get_user_persona_async'):
            asyncio.create_task(self._load_user_persona_async())
            self.logger.bind(tag=TAG).debug("🚀 [后台] 启动用户画像异步加载任务")
        
        self._init_report_threads()
        
        total_elapsed = time.time() * 1000 - init_start_time
        self.logger.bind(tag=TAG).info(f"✅ [后台初始化] 完成: {total_elapsed:.0f}ms (画像后台加载中)")
        return True
    
    async def wait_agent_ready(self, timeout: float = 5.0) -> bool:
        """
        等待 agent 初始化完成。
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            True: 初始化成功
            False: 初始化失败或超时
        """
        # 如果不需要延迟初始化，直接返回成功
        if not getattr(self, "defer_agent_init", False) and self._agent_ready_event.is_set():
            return self._agent_init_error is None
        
        # 如果 event 已经 set，直接返回
        if self._agent_ready_event.is_set():
            return self._agent_init_error is None
        
        try:
            await asyncio.wait_for(self._agent_ready_event.wait(), timeout=timeout)
            if self._agent_init_error:
                self.logger.bind(tag=TAG).error(f"Agent init failed: {self._agent_init_error}")
                return False
            return True
        except asyncio.TimeoutError:
            self.logger.bind(tag=TAG).error(f"wait_agent_ready timeout after {timeout}s")
            return False

    def change_system_prompt(self, prompt):
        self.prompt = prompt
        # 更新系统prompt至上下文
        self.dialogue.update_system_message(self.prompt)

    def chat(self, query, depth=0):
        """
        Process user message and generate response
        
        Args:
            query: User message, can be:
                - str: Text content
                - List[Dict]: Multimodal content
            depth: Recursive depth, for function calling
        """
        self.logger.bind(tag=TAG).info(f"大模型收到用户消息: {query}")
        
        # 记录 LLM 开始处理时间
        llm_start_time = time.time() * 1000
        llm_first_token_time = None
        
        # 检查 TTS 是否已初始化
        if self.tts is None:
            self.logger.bind(tag=TAG).error("TTS 未初始化，无法处理聊天请求")
            return False
        
        self.llm_finish_task = False

        # extract text content for memory query
        if isinstance(query, list):
            # multimodal content: extract text part
            text_parts = [item.get("text", "") for item in query if item.get("type") == "text"]
            query_text = " ".join(text_parts)
        else:
            query_text = query

        # 为最顶层时新建会话ID和发送FIRST请求
        if depth == 0:
            self.sentence_id = str(uuid.uuid4().hex)
            self.dialogue.put(Message(role="user", content=query))
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )

        # Define intent functions
        functions = None
        if self.intent_type == "function_call" and hasattr(self, "func_handler"):
            functions = self.func_handler.get_functions()
        response_message = []

        try:
            # Use retrieved memory (prefetched during turn detection delay)
            memories = self.relevant_memories_this_turn
            
            # Log relevant memory for this turn
            if memories and memories.strip():
                self.logger.bind(tag=TAG).info(f"[Memory] Relevant memories for this turn:\n{memories}")
            else:
                self.logger.bind(tag=TAG).info("[Memory] No relevant memories for this turn")
            
            # Inject memory into base prompt template for this turn
            if self.base_prompt:
                if memories and memories.strip():
                    turn_prompt = self.base_prompt.replace("{relevant_memory}", memories)
                else:
                    turn_prompt = self.base_prompt.replace(
                        "{relevant_memory}", 
                        "No relevant memories retrieved for this turn."
                    )
                # Update system message for this turn
                self.dialogue.update_system_message(turn_prompt)

            # Build dialogue history (with voiceprint speakers info)
            dialogue_history = self.dialogue.get_llm_dialogue_with_memory(
                None, self.config.get("voiceprint", {})
            )
            
            if self.intent_type == "function_call" and functions is not None:
                # 直接使用同步生成器（response_with_functions 是同步方法）
                llm_responses = self.llm.response_with_functions(
                    self.session_id,
                    dialogue_history,
                    functions=functions,
                )
            else:
                # 直接使用同步生成器（response 是同步方法）
                llm_responses = self.llm.response(
                    self.session_id,
                    dialogue_history,
                )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LLM 处理出错 {query}: {e}", exc_info=True)
            return None

        # 处理流式响应
        tool_call_flag = False
        function_name = None
        function_id = None
        function_arguments = ""
        content_arguments = ""
        self.client_abort = False
        emotion_flag = True
        
        for response in llm_responses:
            if self.client_abort:
                break
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
                    if tools_call[0].id is not None:
                        function_id = tools_call[0].id
                    if tools_call[0].function.name is not None:
                        function_name = tools_call[0].function.name
                    if tools_call[0].function.arguments is not None:
                        function_arguments += tools_call[0].function.arguments
            else:
                content = response

            # 记录首个 token 时间（首字延迟）
            if llm_first_token_time is None and content is not None and len(content) > 0:
                llm_first_token_time = time.time() * 1000
                first_token_delay = llm_first_token_time - llm_start_time
                
                # 计算从用户说完到首 token 的延迟
                e2e_first_token = 0
                if hasattr(self, '_latency_voice_end_time'):
                    e2e_first_token = llm_first_token_time - self._latency_voice_end_time
                
                self.logger.bind(tag=TAG).info(
                    f"🤖 [延迟追踪] LLM首token: {first_token_delay:.0f}ms | "
                    f"用户说完→首token: {e2e_first_token:.0f}ms"
                )

            # 在llm回复中获取情绪表情，一轮对话只在开头获取一次
            # 发送 llm 消息，包含 emoji 和 emotion，用于设备端显示表情
            if emotion_flag and content is not None and content.strip():
                asyncio.run_coroutine_threadsafe(
                    textUtils.get_emotion(self, content),
                    self.loop,
                )
                emotion_flag = False

            if content is not None and len(content) > 0:
                if not tool_call_flag:
                    response_message.append(content)
                    self.tts.tts_text_queue.put(
                        TTSMessageDTO(
                            sentence_id=self.sentence_id,
                            sentence_type=SentenceType.MIDDLE,
                            content_type=ContentType.TEXT,
                            content_detail=content,
                        )
                    )
        # 处理function call
        if tool_call_flag:
            bHasError = False
            if function_id is None:
                a = extract_json_from_string(content_arguments)
                if a is not None:
                    try:
                        content_arguments_json = json.loads(a)
                        function_name = content_arguments_json["name"]
                        function_arguments = json.dumps(
                            content_arguments_json["arguments"], ensure_ascii=False
                        )
                        function_id = str(uuid.uuid4().hex)
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
            if not bHasError:
                # 如需要大模型先处理一轮，添加相关处理后的日志情况
                if len(response_message) > 0:
                    text_buff = "".join(response_message)
                    self.tts_MessageText = text_buff
                    self.dialogue.put(Message(role="assistant", content=text_buff))
                response_message.clear()
                self.logger.bind(tag=TAG).debug(
                    f"function_name={function_name}, function_id={function_id}, function_arguments={function_arguments}"
                )
                function_call_data = {
                    "name": function_name,
                    "id": function_id,
                    "arguments": function_arguments,
                }

                # 使用统一工具处理器处理所有工具调用
                result = asyncio.run_coroutine_threadsafe(
                    self.func_handler.handle_llm_function_call(
                        self, function_call_data
                    ),
                    self.loop,
                ).result()
                self._handle_function_result(result, function_call_data, depth=depth)

        # 记录 LLM 完成时间
        llm_end_time = time.time() * 1000
        llm_total_delay = llm_end_time - llm_start_time
        
        # 计算从用户说完到 LLM 完成的延迟
        e2e_llm_complete = 0
        if hasattr(self, '_latency_voice_end_time'):
            e2e_llm_complete = llm_end_time - self._latency_voice_end_time
        
        self.logger.bind(tag=TAG).info(
            f"🤖 [延迟追踪] LLM完成: {llm_total_delay:.0f}ms | "
            f"用户说完→LLM完成: {e2e_llm_complete:.0f}ms"
        )
        
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
        self.relevant_memories_this_turn = "No relevant memories retrieved for this turn."
        # 使用lambda延迟计算，只有在DEBUG级别时才执行get_llm_dialogue()
        self.logger.bind(tag=TAG).debug(
            lambda: json.dumps(
                self.dialogue.get_llm_dialogue(), indent=4, ensure_ascii=False
            )
        )

        return True

    def _handle_function_result(self, result, function_call_data, depth):
        if result.action == Action.RESPONSE:  # 直接回复前端
            text = result.response
            self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=text)
            self.dialogue.put(Message(role="assistant", content=text))
        elif result.action == Action.REQLLM:  # 调用函数后再请求llm生成回复
            text = result.result
            if text is not None and len(text) > 0:
                function_id = function_call_data["id"]
                function_name = function_call_data["name"]
                function_arguments = function_call_data["arguments"]
                self.dialogue.put(
                    Message(
                        role="assistant",
                        tool_calls=[
                            {
                                "id": function_id,
                                "function": {
                                    "arguments": (
                                        "{}"
                                        if function_arguments == ""
                                        else function_arguments
                                    ),
                                    "name": function_name,
                                },
                                "type": "function",
                                "index": 0,
                            }
                        ],
                    )
                )

                self.dialogue.put(
                    Message(
                        role="tool",
                        tool_call_id=(
                            str(uuid.uuid4()) if function_id is None else function_id
                        ),
                        content=text,
                    )
                )
                self.chat(text, depth=depth + 1)
        elif result.action == Action.NOTFOUND or result.action == Action.ERROR:
            text = result.response if result.response else result.result
            self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=text)
            self.dialogue.put(Message(role="assistant", content=text))
        else:
            pass

    def _report_worker(self):
        """聊天记录上报工作线程"""
        while not self.stop_event.is_set():
            try:
                # 从队列获取数据，设置超时以便定期检查停止事件
                item = self.report_queue.get(timeout=1)
                try:
                    self._process_report(*item)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"聊天记录上报线程异常: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"聊天记录上报工作线程异常: {e}")

        # stop_event is set, continue processing remaining messages in report_queue
        self.logger.bind(tag=TAG).info("processing remaining report messages...")
        while not self.report_queue.empty():
            try:
                item = self.report_queue.get(timeout=0.1)
                try:
                    self._process_report(*item)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"processing remaining report messages failed: {e}")
            except queue.Empty:
                break  # Queue is empty, exit

        self.logger.bind(tag=TAG).info("聊天记录上报线程已退出")

    def _process_report(self, role, text, audio_data, report_time, attachments=None):
        """处理上报任务"""
        try:
            # 执行上报（传入二进制数据和附件）
            report(self, role, text, audio_data, report_time, attachments)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"上报处理异常: {e}")
        finally:
            # 标记任务完成
            self.report_queue.task_done()

    def clearSpeakStatus(self):
        self.client_is_speaking = False
        self.logger.bind(tag=TAG).debug(f"清除服务端讲话状态")

    async def on_end_of_turn(self) -> None:
        """Called when user's turn ends (detected by turn detection or ASR)
        
        Handles:
        1. Get text from asr_text_buffer
        2. Clear the buffer
        3. Start chat with the accumulated text
        4. Report ASR message
        """
        from core.handle.receiveAudioHandle import startToChat
        
        full_text = self.asr_text_buffer
        if len(tokenize.split_words(full_text, ignore_punctuation=True, split_character=True)) < self.min_interrupt_text_length:
            return
        
        # Clear buffer before processing
        self.asr_text_buffer = ""
        
        # Start chat with accumulated text
        asr_report_time = int(time.time())
        await startToChat(self, full_text)
        
        # Report ASR message
        enqueue_asr_report(self, full_text, [], report_time=asr_report_time)

    async def close(self, ws=None):
        """资源清理方法"""
        self.logger.bind(tag=TAG).info(
            f"🧹 [开始清理] Device={self.device_id} | IP={self.client_ip} | Session={self.session_id[:8]}..."
        )
        try:
            # 清理音频缓冲区
            if hasattr(self, "audio_buffer"):
                self.audio_buffer.clear()

            # Close VAD stream
            if self.vad_stream:
                try:
                    await self.vad_stream.close()
                    self.vad_stream = None
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Error closing VAD stream: {e}")
            
            if self._vad_event_task and not self._vad_event_task.done():
                self._vad_event_task.cancel()
                try:
                    await self._vad_event_task
                except asyncio.CancelledError:
                    pass
                self._vad_event_task = None

            # Close Turn Detection provider (also clears its internal buffer)
            if self.turn_detection:
                try:
                    await self.turn_detection.close()
                    self.turn_detection = None
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Error closing Turn Detection: {e}")

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

            # clear TTS text queue and audio queue, except report_queue
            self.clear_queues()

            # process remaining messages in report_queue
            if self._report_enabled and self.report_queue:
                try:
                    self.logger.bind(tag=TAG).info("waiting for report queue to be processed...")
                    # wait for all messages to be processed
                    self.report_queue.join()
                    self.logger.bind(tag=TAG).info("report queue processed")
                except Exception as e:
                    self.logger.bind(tag=TAG).warning(f"waiting for report queue timeout or failed: {e}")

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

            if self.tts:
                await self.tts.close()

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
        """clear TTS task queues (except report_queue, which is handled by close method)"""
        if self.tts:
            self.logger.bind(tag=TAG).debug(
                f"开始清理: TTS队列大小={self.tts.tts_text_queue.qsize()}, 音频队列大小={self.tts.tts_audio_queue.qsize()}"
            )

            # use non-blocking way to clear TTS queues
            for q in [
                self.tts.tts_text_queue,
                self.tts.tts_audio_queue,
            ]:
                if not q:
                    continue
                while True:
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        break

            self.logger.bind(tag=TAG).debug(
                f"清理结束: TTS队列大小={self.tts.tts_text_queue.qsize()}, 音频队列大小={self.tts.tts_audio_queue.qsize()}"
            )

    def reset_vad_states(self):
        self.client_audio_buffer = bytearray()
        self.client_have_voice = False
        self.client_voice_stop = False
        self._vad_states= {}
        # reset VAD exponential filter
        # if self.vad:
        #     self.vad.reset_filter()
        self.logger.bind(tag=TAG).debug("VAD states reset.")

    def _interrupt_by_audio(self, speech_duration_ms: float) -> None:
        """Check interruption conditions and trigger interrupt if met
        
        Interruption strategy:
        1. Interruption must be enabled
        2. TTS must be speaking (client_is_speaking = True)
        3. Not in manual listen mode
        4. Speech duration >= min_interrupt_speech_duration_ms
        5. For streaming ASR: text buffer length >= min_interrupt_text_length
           For non-streaming ASR: skip text check (not available during speech)
        
        Args:
            speech_duration_ms: Current speech duration in milliseconds
        """
        # 调试日志：记录打断检测条件
        if self.client_is_speaking:
            self.logger.bind(tag=TAG).debug(
                f"🔍 [打断检测] 条件检查: enable={self.enable_interruption}, "
                f"speaking={self.client_is_speaking}, mode={self.client_listen_mode}, "
                f"defer={getattr(self, 'defer_agent_init', False)}, "
                f"first_done={getattr(self, 'first_dialogue_completed', False)}, "
                f"speech_ms={speech_duration_ms:.0f}"
            )
        
        if not self.enable_interruption:
            return
        if not self.client_is_speaking:
            return
        if self.client_listen_mode == "manual":
            return
        # 在 agent 配置加载完成之前禁用打断检测
        # defer_agent_init=True 表示正在等待 ensure_agent_ready 完成
        # 这样可以避免在 agent 配置加载期间误触发打断
        if getattr(self, "defer_agent_init", False):
            return
        # 首轮对话完成之前禁用打断检测
        # 避免唤醒词响应期间设备继续发送音频被误判为打断
        if not getattr(self, "first_dialogue_completed", False):
            return
        
        # Check speech duration threshold
        speech_ok = speech_duration_ms >= self.min_interrupt_speech_duration_ms
        if not speech_ok:
            return
        
        # Check text length threshold (only for streaming ASR)
        # Non-streaming ASR doesn't have real-time text during speech
        from core.providers.asr.dto import InterfaceType
        is_streaming_asr = (
            self.asr is not None 
            and hasattr(self.asr, 'interface_type') 
            and self.asr.interface_type == InterfaceType.STREAM
        )
        
        if is_streaming_asr:
            words = tokenize.split_words(
                self.asr_text_buffer, 
                ignore_punctuation=True,
                split_character=True,
                retain_format=False,
            )
            asr_text_len = len(words)
            text_ok = asr_text_len >= self.min_interrupt_text_length
            if not text_ok:
                return
            log_msg = (
                f"Interrupt triggered (streaming): speech={speech_duration_ms:.0f}ms, "
                f"text_len={asr_text_len} >= {self.min_interrupt_text_length}"
            )
        else:
            log_msg = f"Interrupt triggered (non-streaming): speech={speech_duration_ms:.0f}ms >= {self.min_interrupt_speech_duration_ms:.0f}ms"
        
        self.logger.bind(tag=TAG).info(log_msg)
        
        # Trigger interrupt
        self.client_abort = True
        self.clear_queues()
        # Send stop message to client
        async def send_stop_message():
            await self.websocket.send(
                json.dumps({"type": "tts", "state": "stop", "session_id": self.session_id})
            )
        asyncio.create_task(send_stop_message())
        self.clearSpeakStatus()

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
        try:
            while not self.stop_event.is_set():
                # 检查是否超时（只有在时间戳已初始化的情况下）
                if self.last_activity_time > 0.0:
                    current_time = time.time() * 1000
                    if (
                        current_time - self.last_activity_time
                        > self.timeout_seconds * 1000
                    ):
                        if not self.stop_event.is_set():
                            self.logger.bind(tag=TAG).info("连接超时，准备关闭")
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
            self.logger.bind(tag=TAG).info("超时检查任务已退出")


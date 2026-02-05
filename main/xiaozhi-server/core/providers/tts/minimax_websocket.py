# -*- coding: utf-8 -*-
"""
MiniMax TTS WebSocket 流式实现
使用 WebSocket 双向流式接口，相比 HTTP SSE 延迟更低

特点：
- WebSocket 双向流式通信
- 支持连接复用和 keepalive
- 支持字幕/时间戳功能
- 支持打断取消和优雅关闭
- 支持音色混合 (timber_weights)
"""

import os
import ssl
import json
import time
import queue
import asyncio
import traceback
from typing import Callable, Any, Optional
from dataclasses import dataclass, field

import websockets

from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.utils import opus_encoder_utils, textUtils
from core.utils.util import parse_string_to_list
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()

# TTS 事件类型
EVENT_TTS_SENTENCE_START = 350
EVENT_TTS_SENTENCE_END = 351
EVENT_TTS_RESPONSE = 352
EVENT_TTS_TASK_FINISHED = 353
EVENT_TTS_FLUSH = 354
EVENT_TTS_TASK_FAILED = 355


@dataclass
class TTSWord:
    """TTS 单词时间戳信息"""
    word: str
    start_ms: int
    duration_ms: int


@dataclass
class TTSTextResult:
    """TTS 文本结果（包含时间戳）"""
    request_id: str
    text: str
    start_ms: int
    duration_ms: int
    words: list[TTSWord] = field(default_factory=list)
    text_result_end: bool = False


class MinimaxTTSTaskFailedException(Exception):
    """MiniMax TTS 任务失败异常"""

    def __init__(self, error_msg: str, error_code: int):
        self.error_msg = error_msg
        self.error_code = error_code
        super().__init__(f"TTS 任务失败: {error_msg} (code: {error_code})")


class MinimaxWebSocketClient:
    """MiniMax TTS WebSocket 客户端"""

    def __init__(
        self,
        config: dict,
        on_audio_data: Optional[Callable[[bytes, int], Any]] = None,
        on_transcription: Optional[Callable[[TTSTextResult], Any]] = None,
        on_error: Optional[Callable[[MinimaxTTSTaskFailedException], None]] = None,
    ):
        self.config = config
        self.on_audio_data = on_audio_data
        self.on_transcription = on_transcription
        self.on_error = on_error

        # 配置参数（支持 key 和 api_key 两种写法）
        self.api_key = config.get("key", config.get("api_key", ""))
        self.group_id = config.get("group_id", "")
        
        # WebSocket URL（支持 url 和 ws_url 两种写法）
        default_url = "wss://api.minimax.io/ws/v1/t2a_v2"
        self.url = config.get("url", config.get("ws_url", default_url))
        
        # 模型选择
        self.model = config.get("model", "speech-02-turbo")
        
        # 是否启用字幕
        self.enable_words = config.get("enable_words", False)

        # 音频设置（支持嵌套对象格式）
        audio_setting = config.get("audio_setting", {})
        self.sample_rate = int(audio_setting.get("sample_rate", config.get("sample_rate", 16000)))
        self.channels = int(audio_setting.get("channel", config.get("channels", 1)))
        self.bitrate = int(audio_setting.get("bitrate", config.get("bitrate", 128000)))
        
        self.audio_setting = {
            "sample_rate": self.sample_rate,
            "bitrate": self.bitrate,
            "format": audio_setting.get("format", "pcm"),
            "channel": self.channels,
        }

        # 音色设置（支持嵌套对象格式）
        voice_setting = config.get("voice_setting", {})
        default_voice_setting = {
            "voice_id": voice_setting.get("voice_id", config.get("voice_id", "female-shaonv")),
            "speed": float(voice_setting.get("speed", config.get("speed", 1.0))),
            "vol": float(voice_setting.get("vol", config.get("vol", 1.0))),
            "pitch": int(voice_setting.get("pitch", config.get("pitch", 0))),
        }
        
        # 情感设置
        emotion = voice_setting.get("emotion", config.get("emotion"))
        if emotion:
            default_voice_setting["emotion"] = emotion

        self.voice_setting = default_voice_setting

        # 音色混合
        self.timber_weights = parse_string_to_list(config.get("timber_weights"))
        if self.timber_weights:
            self.voice_setting["voice_id"] = ""

        # 发音词典
        self.pronunciation_dict = config.get("pronunciation_dict", {})

        # 连接状态
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id = ""
        self.stopping = False
        self.discarding = False
        self.callbacks_enabled = True
        self.last_active_time: Optional[float] = None

        # 连接就绪事件（用于预热等待）
        self._connection_ready = asyncio.Event()
        self._connection_error: Optional[str] = None

        # 任务队列
        self.tts_task_queue: asyncio.Queue = asyncio.Queue()

        # WebSocket 主循环任务引用（用于正确取消）
        self._websocket_task: Optional[asyncio.Task] = None

        # 时间戳追踪
        self.current_request_start_ms = 0
        self.estimated_duration_this_request = 0
        self.last_word_end_ms = 0

    async def start(self, wait_ready: bool = False, timeout: float = 5.0):
        """
        启动 WebSocket 处理器
        
        Args:
            wait_ready: 是否等待连接就绪
            timeout: 等待超时时间（秒）
        """
        logger.bind(tag=TAG).info(f"MiniMax TTS: 启动 WebSocket 处理器 (wait_ready={wait_ready}, timeout={timeout})")
        self._connection_ready.clear()
        self._connection_error = None
        # 保存任务引用，用于正确取消
        self._websocket_task = asyncio.create_task(self._process_websocket())
        
        if wait_ready:
            try:
                await asyncio.wait_for(self._connection_ready.wait(), timeout=timeout)
                if self._connection_error:
                    logger.bind(tag=TAG).warning(f"MiniMax TTS: 连接出错: {self._connection_error}")
                else:
                    logger.bind(tag=TAG).info("MiniMax TTS: 连接预热完成")
            except asyncio.TimeoutError:
                logger.bind(tag=TAG).warning(f"MiniMax TTS: 连接预热超时（{timeout}s），将在后台继续")

    async def stop(self):
        """停止并清理"""
        logger.bind(tag=TAG).info(f"MiniMax TTS: stop 开始 (stopping={self.stopping}, discarding={self.discarding})")
        self.stopping = True
        
        # 先取消当前操作（关闭 WebSocket 连接等）
        await self.cancel()
        
        # 显式取消并等待 WebSocket 主循环任务完成
        if self._websocket_task and not self._websocket_task.done():
            logger.bind(tag=TAG).info("MiniMax TTS: 取消 WebSocket 主循环任务")
            self._websocket_task.cancel()
            try:
                # 设置超时，避免无限等待
                await asyncio.wait_for(self._websocket_task, timeout=3.0)
            except asyncio.CancelledError:
                logger.bind(tag=TAG).info("MiniMax TTS: WebSocket 任务已取消")
            except asyncio.TimeoutError:
                logger.bind(tag=TAG).warning("MiniMax TTS: 等待 WebSocket 任务超时，强制跳过")
            except Exception as e:
                logger.bind(tag=TAG).warning(f"MiniMax TTS: 等待 WebSocket 任务时出错: {e}")
            finally:
                self._websocket_task = None
        
        logger.bind(tag=TAG).info("MiniMax TTS: stop 完成")

    async def cancel(self):
        """取消当前操作"""
        logger.bind(tag=TAG).info(f"MiniMax TTS: cancel 开始 (discarding={self.discarding}, ws_connected={self.ws is not None})")

        if self.discarding:
            logger.bind(tag=TAG).info("MiniMax TTS: cancel 跳过（已在取消中）")
            return

        self.callbacks_enabled = False
        self.discarding = True

        # 关闭 WebSocket
        if self.ws:
            try:
                logger.bind(tag=TAG).info("MiniMax TTS: 关闭 WebSocket 连接")
                await self.ws.close()
            except Exception as e:
                logger.bind(tag=TAG).warning(f"MiniMax TTS: 关闭 WebSocket 时出错: {e}")
            self.ws = None

        # 清空任务队列
        queue_size = self.tts_task_queue.qsize()
        while not self.tts_task_queue.empty():
            try:
                self.tts_task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.bind(tag=TAG).info(f"MiniMax TTS: 清空队列完成，原大小={queue_size}")

        # 插入哨兵值唤醒队列
        await self.tts_task_queue.put(None)
        logger.bind(tag=TAG).info("MiniMax TTS: cancel 完成")

    async def get(self, text: str, is_end: bool = False):
        """发送 TTS 请求"""
        if self.discarding:
            logger.bind(tag=TAG).info(f"MiniMax TTS: get 跳过（正在取消中）, text={text[:20] if text else '[empty]'}...")
            return

        queue_size = self.tts_task_queue.qsize()
        await self.tts_task_queue.put({"text": text, "is_end": is_end})
        logger.bind(tag=TAG).info(f"MiniMax TTS: 请求已提交 is_end={is_end}, queue_size_before={queue_size}, text={text[:30] if text else '[empty]'}...")

    async def _process_websocket(self):
        """WebSocket 连接管理主循环"""
        logger.bind(tag=TAG).info("MiniMax TTS: WebSocket 主循环开始")
        loop_count = 0
        
        while not self.stopping:
            loop_count += 1
            logger.bind(tag=TAG).info(f"MiniMax TTS: WebSocket 连接循环 #{loop_count}")
            try:
                # 建立连接
                headers = {"Authorization": f"Bearer {self.api_key}"}
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                logger.bind(tag=TAG).info(f"MiniMax TTS: 正在连接到 {self.url}")

                self.ws = await websockets.connect(
                    self.url,
                    additional_headers=headers,
                    ssl=ssl_context,
                    max_size=1024 * 1024 * 16,
                )

                self.last_active_time = time.time()
                logger.bind(tag=TAG).info("MiniMax TTS: WebSocket 连接建立成功")

                # 处理初始化响应
                init_response = json.loads(await self.ws.recv())
                logger.bind(tag=TAG).info(f"MiniMax TTS: 初始化响应: event={init_response.get('event')}")

                if init_response.get("event") != "connected_success":
                    error_msg = init_response.get("base_resp", {}).get(
                        "status_msg", "未知错误"
                    )
                    error_code = init_response.get("base_resp", {}).get("status_code", 0)
                    logger.bind(tag=TAG).error(f"MiniMax TTS: 连接失败: {error_msg} (code={error_code})")
                    continue

                self.session_id = init_response.get("session_id", "")

                # 发送 task_start
                start_msg = self._create_start_task_msg()
                logger.bind(tag=TAG).info(f"MiniMax TTS: 发送 task_start, model={start_msg.get('model')}")
                await self.ws.send(json.dumps(start_msg))

                start_response = json.loads(await self.ws.recv())
                logger.bind(tag=TAG).info(f"MiniMax TTS: 任务启动响应: event={start_response.get('event')}")

                if start_response.get("event") != "task_started":
                    error_msg = start_response.get("base_resp", {}).get(
                        "status_msg", "未知错误"
                    )
                    error_code = start_response.get("base_resp", {}).get("status_code", 0)
                    logger.bind(tag=TAG).error(f"MiniMax TTS: 任务启动失败: {error_msg} (code={error_code})")

                    if self.on_error and self.callbacks_enabled:
                        self.on_error(
                            MinimaxTTSTaskFailedException(error_msg, error_code)
                        )
                    await asyncio.sleep(1)
                    continue

                logger.bind(tag=TAG).info(f"MiniMax TTS: 会话就绪 session_id={self.session_id}")

                # 标记连接就绪（用于预热等待）
                self._connection_ready.set()

                # 处理 TTS 任务
                await self._process_tts_tasks()

            except websockets.exceptions.ConnectionClosedError as e:
                logger.bind(tag=TAG).warning(f"MiniMax TTS: WebSocket 连接关闭: {e}")
                self._connection_error = str(e)
                self._connection_ready.set()  # 即使出错也要唤醒等待
            except websockets.exceptions.InvalidHandshake as e:
                logger.bind(tag=TAG).warning(f"MiniMax TTS: WebSocket 握手失败: {e}")
                self._connection_error = str(e)
                self._connection_ready.set()
                if self.on_error and self.callbacks_enabled:
                    self.on_error(MinimaxTTSTaskFailedException(str(e), -1))
                await asyncio.sleep(1)
            except Exception as e:
                logger.bind(tag=TAG).warning(f"MiniMax TTS: WebSocket 异常: {e}, traceback: {traceback.format_exc()}")
                self._connection_error = str(e)
                self._connection_ready.set()
                await asyncio.sleep(1)
            finally:
                self.ws = None
                self.discarding = False
                logger.bind(tag=TAG).info(f"MiniMax TTS: WebSocket 连接循环 #{loop_count} 结束")

        logger.bind(tag=TAG).info(f"MiniMax TTS: WebSocket 主循环退出 (loop_count={loop_count}, stopping={self.stopping})")

    async def _process_tts_tasks(self):
        """处理 TTS 任务队列"""
        keepalive_interval = 30.0
        task_count = 0
        logger.bind(tag=TAG).info("MiniMax TTS: 开始处理任务队列")

        while not self.stopping:
            if self.discarding:
                logger.bind(tag=TAG).info(f"MiniMax TTS: 任务处理退出（discarding=True, task_count={task_count}）")
                return

            try:
                # 等待任务，带超时用于 keepalive
                queue_size = self.tts_task_queue.qsize()
                task = await asyncio.wait_for(
                    self.tts_task_queue.get(), timeout=keepalive_interval
                )

                if task is None:
                    logger.bind(tag=TAG).info(f"MiniMax TTS: 收到哨兵值，退出任务处理 (task_count={task_count})")
                    return

                task_count += 1
                logger.bind(tag=TAG).info(f"MiniMax TTS: 从队列获取任务 #{task_count}, is_end={task['is_end']}, text={task['text'][:20] if task['text'] else '[empty]'}...")
                
                # 处理单个 TTS 请求
                await self._process_single_request(task["text"], task["is_end"])
                logger.bind(tag=TAG).info(f"MiniMax TTS: 任务 #{task_count} 处理完成")

            except asyncio.TimeoutError:
                # 发送 keepalive
                if self.ws:
                    try:
                        logger.bind(tag=TAG).debug("MiniMax TTS: 发送 keepalive")
                        keepalive_msg = {"event": "task_continue", "text": ""}
                        await self.ws.send(json.dumps(keepalive_msg))
                        await asyncio.wait_for(self.ws.recv(), timeout=10.0)
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"MiniMax TTS: Keepalive 失败: {e}")
                        raise
        
        logger.bind(tag=TAG).info(f"MiniMax TTS: 任务处理循环退出 (stopping={self.stopping}, task_count={task_count})")

    async def _process_single_request(self, text: str, is_end: bool):
        """处理单个 TTS 请求"""
        logger.bind(tag=TAG).info(f"MiniMax TTS: 处理请求开始 is_end={is_end}, discarding={self.discarding}, stopping={self.stopping}, ws_connected={self.ws is not None}")
        
        if self.discarding or self.stopping or not self.ws:
            logger.bind(tag=TAG).info(f"MiniMax TTS: 处理请求跳过（状态不允许）")
            return

        # 跳过空文本
        if not text.strip():
            logger.bind(tag=TAG).info(f"MiniMax TTS: 跳过空文本, is_end={is_end}")
            if is_end and self.on_audio_data and self.callbacks_enabled:
                self.on_audio_data(b"", EVENT_TTS_SENTENCE_END)
            return

        # 发送请求
        ws_req = {"event": "task_continue", "text": text}
        logger.bind(tag=TAG).info(f"MiniMax TTS: 发送文本到 WebSocket: {text[:30]}...")
        await self.ws.send(json.dumps(ws_req))

        # 重置时间戳追踪
        self.estimated_duration_this_request = 0
        self.last_word_end_ms = 0

        # 接收响应
        audio_chunk_count = 0
        logger.bind(tag=TAG).info(f"MiniMax TTS: 开始接收响应 text={text[:20]}...")
        while not self.stopping and not self.discarding:
            try:
                response_bytes = await self.ws.recv()
                response = json.loads(response_bytes)

                event = response.get("event")

                if event == "task_failed":
                    error_msg = response.get("base_resp", {}).get(
                        "status_msg", "未知错误"
                    )
                    error_code = response.get("base_resp", {}).get("status_code", 0)
                    logger.bind(tag=TAG).error(f"MiniMax TTS: 任务失败: {error_msg} (code={error_code})")

                    if is_end and self.on_audio_data and self.callbacks_enabled:
                        self.on_audio_data(b"", EVENT_TTS_TASK_FAILED)

                    if self.on_error and self.callbacks_enabled:
                        self.on_error(
                            MinimaxTTSTaskFailedException(error_msg, error_code)
                        )
                    break

                if event == "task_finished":
                    logger.bind(tag=TAG).info(f"MiniMax TTS: 任务完成 (audio_chunks={audio_chunk_count})")
                    if self.on_audio_data and self.callbacks_enabled:
                        self.on_audio_data(b"", EVENT_TTS_TASK_FINISHED)
                    break

                if response.get("is_final", False):
                    logger.bind(tag=TAG).info(f"MiniMax TTS: 收到 is_final (audio_chunks={audio_chunk_count}, duration={self.estimated_duration_this_request}ms)")

                    # 更新时间戳基准
                    if "extra_info" in response:
                        extra_info = response["extra_info"]
                        if "audio_sample_rate" in extra_info:
                            new_sample_rate = int(extra_info["audio_sample_rate"])
                            if new_sample_rate != self.sample_rate:
                                logger.bind(tag=TAG).info(
                                    f"MiniMax TTS: 更新 sample_rate {self.sample_rate} -> {new_sample_rate}"
                                )
                                self.sample_rate = new_sample_rate
                                # 通知 TTSProvider 更新 frame_bytes（通过回调传递）
                                # 注意：这里我们通过一个特殊的事件来通知，但当前实现中
                                # TTSProvider 的 frame_bytes 在初始化时已计算，运行时不会更新
                                # 如果 sample_rate 变化，可能会导致编码问题

                    # 发送事件处理剩余的 PCM 数据
                    # 无论 is_end 是否为 True，都需要 flush 剩余的 PCM 数据
                    if self.on_audio_data and self.callbacks_enabled:
                        if is_end:
                            # 最后一个任务，发送 SENTENCE_END 事件
                            self.on_audio_data(b"", EVENT_TTS_SENTENCE_END)
                        else:
                            # 中间任务，发送 FLUSH 事件处理剩余数据
                            self.on_audio_data(b"", EVENT_TTS_FLUSH)
                    break

                # 处理音频数据
                if "data" in response and "audio" in response["data"]:
                    audio_hex = response["data"]["audio"]
                    audio_bytes = bytes.fromhex(audio_hex)
                    audio_chunk_count += 1

                    # 计算音频时长
                    if len(audio_bytes) > 0:
                        bytes_per_sample = 2  # 16-bit
                        chunk_duration = (
                            len(audio_bytes)
                            * 1000
                            // (self.sample_rate * bytes_per_sample * self.channels)
                        )
                        self.estimated_duration_this_request += chunk_duration
                        
                        # 每10个音频块记录一次日志
                        if audio_chunk_count % 10 == 1:
                            logger.bind(tag=TAG).info(f"MiniMax TTS: 收到音频块 #{audio_chunk_count}, size={len(audio_bytes)}, total_duration={self.estimated_duration_this_request}ms")

                    # 处理字幕数据
                    if (
                        self.enable_words
                        and "subtitle" in response["data"]
                        and self.on_transcription
                        and self.callbacks_enabled
                    ):
                        subtitle_data = response["data"]["subtitle"]
                        words = self._process_subtitle_data(subtitle_data)

                        if words:
                            transcription = TTSTextResult(
                                request_id=self.session_id,
                                text=subtitle_data.get("text", ""),
                                start_ms=words[0].start_ms if words else 0,
                                duration_ms=sum(w.duration_ms for w in words),
                                words=words,
                                text_result_end=is_end,
                            )
                            self.on_transcription(transcription)

                    # 发送音频数据
                    if self.on_audio_data and len(audio_bytes) > 0 and self.callbacks_enabled:
                        self.on_audio_data(audio_bytes, EVENT_TTS_RESPONSE)
                else:
                    logger.bind(tag=TAG).warning(f"MiniMax TTS: 响应中没有音频数据, event={event}")
                    break

            except websockets.exceptions.ConnectionClosed:
                logger.bind(tag=TAG).warning(f"MiniMax TTS: WebSocket 连接关闭 (audio_chunks={audio_chunk_count})")
                break
            except Exception as e:
                logger.bind(tag=TAG).error(f"MiniMax TTS: 处理响应时出错: {e}, traceback: {traceback.format_exc()}")
                raise
        
        logger.bind(tag=TAG).info(f"MiniMax TTS: 请求处理完成 audio_chunks={audio_chunk_count}, duration={self.estimated_duration_this_request}ms")

    def _create_start_task_msg(self) -> dict:
        """创建 task_start 消息"""
        msg = {
            "event": "task_start",
            "model": self.model,
            "voice_setting": self.voice_setting,
            "audio_setting": self.audio_setting,
        }

        if self.timber_weights:
            msg["timber_weights"] = self.timber_weights

        if self.pronunciation_dict:
            msg["pronunciation_dict"] = self.pronunciation_dict

        if self.enable_words:
            msg["subtitle_enable"] = True
            msg["subtitle_type"] = "word"

        return msg

    def _process_subtitle_data(self, subtitle_data: dict) -> list[TTSWord]:
        """处理字幕数据，转换为 TTSWord 列表"""
        words = []

        if "timestamped_words" not in subtitle_data:
            return words

        timestamped_words = subtitle_data["timestamped_words"]
        if not timestamped_words:
            return words

        for word_data in timestamped_words:
            time_begin = word_data.get("time_begin", 0)
            time_end = word_data.get("time_end", 0)

            word_text = word_data.get("word", "")
            if word_text == "[SPACE]":
                word_text = " "

            word = TTSWord(
                word=word_text,
                start_ms=int(self.current_request_start_ms + time_begin),
                duration_ms=int(time_end - time_begin),
            )
            words.append(word)

            self.last_word_end_ms = int(self.current_request_start_ms + time_end)

        return words


class TTSProvider(TTSProviderBase):
    """MiniMax TTS WebSocket 流式提供者"""

    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        # 设置接口类型为双向流式
        self.interface_type = InterfaceType.DUAL_STREAM

        # 保存配置
        self.config = config

        # 音频参数（支持嵌套对象格式）
        audio_setting = config.get("audio_setting", {})
        self.sample_rate = int(audio_setting.get("sample_rate", config.get("sample_rate", 16000)))
        self.channels = int(audio_setting.get("channel", config.get("channels", 1)))

        # 创建 Opus 编码器
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=self.sample_rate, channels=self.channels, frame_size_ms=60
        )

        # PCM 缓冲区
        self.pcm_buffer = bytearray()

        # 计算每帧字节数
        self.frame_bytes = int(
            self.sample_rate * self.channels * 60 / 1000 * 2  # 16-bit = 2 bytes
        )

        # WebSocket 客户端（延迟初始化）
        self.ws_client: Optional[MinimaxWebSocketClient] = None

        # 字幕回调存储
        self.transcription_results: list[TTSTextResult] = []

    async def open_audio_channels(self, conn):
        """打开音频通道，初始化 WebSocket 客户端"""
        await super().open_audio_channels(conn)

        # 创建 WebSocket 客户端
        self.ws_client = MinimaxWebSocketClient(
            config=self.config,
            on_audio_data=self._on_audio_data,
            on_transcription=self._on_transcription,
            on_error=self._on_error,
        )

        # 启动客户端（等待连接就绪，预热以降低首次 TTS 延迟）
        await self.ws_client.start(wait_ready=True, timeout=3.0)

    def _on_audio_data(self, audio_bytes: bytes, event_type: int):
        """音频数据回调"""
        if event_type == EVENT_TTS_RESPONSE and len(audio_bytes) > 0:
            # 记录 TTS 首音频时间
            if hasattr(self, 'conn') and self.conn:
                if hasattr(self.conn, 'latency_metrics') and self.conn.latency_metrics:
                    self.conn.latency_metrics.mark_tts_first_audio()
            
            # 累积 PCM 数据
            self.pcm_buffer.extend(audio_bytes)

            # 编码并发送
            frames_encoded = 0
            pcm_size_before = len(self.pcm_buffer)
            while len(self.pcm_buffer) >= self.frame_bytes:
                frame = bytes(self.pcm_buffer[: self.frame_bytes])
                del self.pcm_buffer[: self.frame_bytes]
                frames_encoded += 1

                logger.bind(tag=TAG).debug(
                    f"MiniMax TTS Provider: 编码 PCM 帧, frame_size={len(frame)} bytes, "
                    f"frames_encoded={frames_encoded}, pcm_buffer_remaining={len(self.pcm_buffer)}"
                )
                
                self.opus_encoder.encode_pcm_to_opus_stream(
                    frame, end_of_stream=False, callback=self.handle_opus
                )
            
            # 记录调试信息
            if frames_encoded > 0:
                logger.bind(tag=TAG).info(
                    f"MiniMax TTS Provider: 编码完成, 收到={len(audio_bytes)} bytes, "
                    f"编码帧数={frames_encoded}, pcm_buffer_before={pcm_size_before}, "
                    f"pcm_buffer_after={len(self.pcm_buffer)}"
                )
            elif len(self.pcm_buffer) > 0:
                # 有数据但不足一帧，记录日志以便调试
                logger.bind(tag=TAG).debug(
                    f"MiniMax TTS Provider: PCM缓冲区累积中, 收到={len(audio_bytes)} bytes, "
                    f"buffer_size={len(self.pcm_buffer)}, frame_bytes={self.frame_bytes}, "
                    f"sample_rate={self.sample_rate}, channels={self.channels}, "
                    f"需要={self.frame_bytes - len(self.pcm_buffer)} bytes 才能编码一帧"
                )

        elif event_type == EVENT_TTS_SENTENCE_END:
            logger.bind(tag=TAG).info(f"MiniMax TTS Provider: 收到 SENTENCE_END, pcm_buffer_size={len(self.pcm_buffer)}")
            # 处理剩余数据
            if self.pcm_buffer:
                self.opus_encoder.encode_pcm_to_opus_stream(
                    bytes(self.pcm_buffer),
                    end_of_stream=True,
                    callback=self.handle_opus,
                )
                self.pcm_buffer.clear()

            # 处理待播放文件
            self._process_before_stop_play_files()
            logger.bind(tag=TAG).info("MiniMax TTS Provider: SENTENCE_END 处理完成")

        elif event_type == EVENT_TTS_FLUSH:
            logger.bind(tag=TAG).info(f"MiniMax TTS Provider: 收到 FLUSH, pcm_buffer_size={len(self.pcm_buffer)}")
            # 处理剩余数据（中间任务完成时 flush 剩余 PCM 数据）
            if self.pcm_buffer:
                self.opus_encoder.encode_pcm_to_opus_stream(
                    bytes(self.pcm_buffer),
                    end_of_stream=False,  # 中间任务，不是流结束
                    callback=self.handle_opus,
                )
                self.pcm_buffer.clear()
            logger.bind(tag=TAG).info("MiniMax TTS Provider: FLUSH 处理完成")

        elif event_type == EVENT_TTS_TASK_FAILED:
            logger.bind(tag=TAG).error("MiniMax TTS Provider: 任务失败")
            self.tts_audio_queue.put((SentenceType.LAST, [], None))

    def _on_transcription(self, result: TTSTextResult):
        """字幕回调"""
        self.transcription_results.append(result)
        logger.bind(tag=TAG).debug(
            f"收到字幕: {result.text}, 单词数: {len(result.words)}"
        )

    def _on_error(self, error: MinimaxTTSTaskFailedException):
        """错误回调"""
        logger.bind(tag=TAG).error(f"TTS 错误: {error.error_msg} ({error.error_code})")

    def tts_text_priority_thread(self):
        """双向流式 TTS 文本处理线程"""
        logger.bind(tag=TAG).info("MiniMax TTS Provider: 文本处理线程启动")
        message_count = 0
        
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                message_count += 1

                logger.bind(tag=TAG).info(
                    f"MiniMax TTS Provider: 收到消息 #{message_count} | {message.sentence_type.name} | "
                    f"{message.content_type.name} | client_abort={self.conn.client_abort}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    logger.bind(tag=TAG).info(f"MiniMax TTS Provider: FIRST 消息，重置 client_abort (原值={self.conn.client_abort})")
                    self.conn.client_abort = False
                    # 重要：重置 callbacks_enabled，确保打断后新的 TTS 任务能正常触发回调
                    if self.ws_client:
                        self.ws_client.callbacks_enabled = True
                        self.ws_client.discarding = False
                        logger.bind(tag=TAG).info("MiniMax TTS Provider: FIRST 消息，重置 ws_client.callbacks_enabled=True")

                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("MiniMax TTS Provider: 收到打断信息，取消 TTS")
                    if self.ws_client:
                        asyncio.run_coroutine_threadsafe(
                            self.ws_client.cancel(), self.conn.loop
                        )
                    continue

                if message.sentence_type == SentenceType.FIRST:
                    # 初始化参数
                    logger.bind(tag=TAG).info("MiniMax TTS Provider: FIRST 消息，初始化参数")
                    self.tts_stop_request = False
                    self.processed_chars = 0
                    self.tts_text_buff = []
                    self.is_first_sentence = True
                    self.before_stop_play_files.clear()
                    self.transcription_results.clear()
                    self.pcm_buffer.clear()
                    # 注意：不在这里发送 FIRST 到 tts_audio_queue，而是等到有实际文本时再发送
                    logger.bind(tag=TAG).info("MiniMax TTS Provider: FIRST 消息处理完成")

                elif ContentType.TEXT == message.content_type:
                    if message.content_detail:
                        # 使用文本缓冲，等待完整句子后再发送
                        self.tts_text_buff.append(message.content_detail)
                        # 保存首句状态（_get_segment_text 会修改 is_first_sentence）
                        was_first_sentence = self.is_first_sentence
                        segment_text = self._get_segment_text()
                        if segment_text and self.ws_client:
                            logger.bind(tag=TAG).info(f"MiniMax TTS Provider: 发送文本段: {segment_text[:30]}...")
                            # 记录首句 TTS 请求时间
                            if was_first_sentence:
                                if hasattr(self.conn, 'latency_metrics') and self.conn.latency_metrics:
                                    self.conn.latency_metrics.mark_tts_request(segment_text)
                            text = MarkdownCleaner.clean_markdown(segment_text)
                            # 发送 FIRST 消息到 tts_audio_queue，包含文本（用于 WebSocket sentence_start 消息）
                            self.tts_audio_queue.put((SentenceType.FIRST, [], text))
                            asyncio.run_coroutine_threadsafe(
                                self.ws_client.get(text, is_end=False), self.conn.loop
                            )

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"添加音频文件到待播放列表: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        self._process_audio_file_stream(
                            message.content_file,
                            callback=lambda audio_data: self.handle_audio_file(
                                audio_data, message.content_detail
                            ),
                        )

                if message.sentence_type == SentenceType.LAST:
                    logger.bind(tag=TAG).info("MiniMax TTS Provider: LAST 消息，处理剩余文本")
                    # 先处理剩余的文本缓冲
                    self.tts_stop_request = True
                    remaining_text = self._get_segment_text()
                    if remaining_text and self.ws_client:
                        logger.bind(tag=TAG).info(f"MiniMax TTS Provider: 发送剩余文本: {remaining_text[:30]}...")
                        text = MarkdownCleaner.clean_markdown(remaining_text)
                        asyncio.run_coroutine_threadsafe(
                            self.ws_client.get(text, is_end=False), self.conn.loop
                        )
                    # 发送空文本标记结束
                    if self.ws_client:
                        logger.bind(tag=TAG).info("MiniMax TTS Provider: 发送结束标记")
                        asyncio.run_coroutine_threadsafe(
                            self.ws_client.get("", is_end=True), self.conn.loop
                        )
                    logger.bind(tag=TAG).info("MiniMax TTS Provider: LAST 消息处理完成")

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"MiniMax TTS Provider: 处理 TTS 文本失败: {str(e)}, 类型: {type(e).__name__}, "
                    f"堆栈: {traceback.format_exc()}"
                )
        
        logger.bind(tag=TAG).info(f"MiniMax TTS Provider: 文本处理线程退出 (message_count={message_count}, stop_event={self.conn.stop_event.is_set()})")

    async def text_to_speak(self, text, output_file):
        """
        非流式 TTS（用于兼容基类接口）

        注意：此方法主要用于测试场景
        实际流式处理通过 WebSocket 客户端完成
        """
        # 创建临时客户端
        audio_data = bytearray()
        finished = asyncio.Event()

        def on_audio(data: bytes, event_type: int):
            if event_type == EVENT_TTS_RESPONSE:
                audio_data.extend(data)
            elif event_type in (EVENT_TTS_SENTENCE_END, EVENT_TTS_TASK_FINISHED):
                finished.set()

        client = MinimaxWebSocketClient(
            config=self.config, on_audio_data=on_audio
        )

        try:
            await client.start()
            await asyncio.sleep(0.5)  # 等待连接建立
            await client.get(text, is_end=True)

            # 等待完成
            await asyncio.wait_for(finished.wait(), timeout=30)

            if output_file:
                with open(output_file, "wb") as f:
                    f.write(audio_data)
            else:
                return bytes(audio_data)

        finally:
            await client.stop()

    async def close(self):
        """资源清理"""
        logger.bind(tag=TAG).info(f"MiniMax TTS Provider: close 开始 (ws_client={self.ws_client is not None})")
        await super().close()

        if self.ws_client:
            logger.bind(tag=TAG).info("MiniMax TTS Provider: 停止 WebSocket 客户端")
            await self.ws_client.stop()
            self.ws_client = None

        if hasattr(self, "opus_encoder"):
            self.opus_encoder.close()
        
        logger.bind(tag=TAG).info("MiniMax TTS Provider: close 完成")

    def to_tts(self, text: str) -> list:
        """
        非流式 TTS 处理，用于测试场景

        Args:
            text: 要转换的文本

        Returns:
            list: Opus 编码后的音频数据列表
        """
        text = MarkdownCleaner.clean_markdown(text)
        opus_datas = []
        pcm_buffer = bytearray()

        async def _generate():
            nonlocal pcm_buffer
            audio_data = bytearray()
            finished = asyncio.Event()

            def on_audio(data: bytes, event_type: int):
                if event_type == EVENT_TTS_RESPONSE:
                    audio_data.extend(data)
                elif event_type in (EVENT_TTS_SENTENCE_END, EVENT_TTS_TASK_FINISHED):
                    finished.set()

            client = MinimaxWebSocketClient(
                config=self.config, on_audio_data=on_audio
            )

            try:
                await client.start()
                await asyncio.sleep(0.5)
                await client.get(text, is_end=True)
                await asyncio.wait_for(finished.wait(), timeout=30)

                # 编码为 Opus
                for i in range(0, len(audio_data), self.frame_bytes):
                    frame = bytes(audio_data[i: i + self.frame_bytes])
                    if len(frame) < self.frame_bytes:
                        frame = frame + b"\x00" * (self.frame_bytes - len(frame))

                    self.opus_encoder.encode_pcm_to_opus_stream(
                        frame,
                        end_of_stream=(i + self.frame_bytes >= len(audio_data)),
                        callback=lambda opus: opus_datas.append(opus),
                    )

            finally:
                await client.stop()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_generate())
            loop.close()
        except Exception as e:
            logger.bind(tag=TAG).error(f"to_tts 失败: {e}")

        return opus_datas

    def get_transcription_results(self) -> list[TTSTextResult]:
        """获取字幕结果"""
        return self.transcription_results


# -*- coding: utf-8 -*-
"""
Fish Audio TTS 流式实现
使用官方 fish_audio_sdk 的 WebSocket 接口实现流式 TTS

特点：
- 使用 WebSocket 单向流式通信
- 非阻塞提交 + 异步队列处理，优化延迟
- 支持预取模式（Prefetch）：在处理当前句子时提前发起下一个句子的 TTS 请求
- 支持声音克隆（reference_id）
- 支持打断取消

配置选项：
- prefetch_enabled: 是否启用预取模式（默认 True）
- max_prefetch: 最大预取数量（默认 3）
- latency: Fish Audio 延迟模式（"balanced" 或 "low"）
"""

import os
import uuid
import queue
import asyncio
import traceback
from typing import AsyncIterator, Optional
from dataclasses import dataclass

from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.utils import opus_encoder_utils, textUtils
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()

# TTS 事件类型
EVENT_TTS_RESPONSE = 1
EVENT_TTS_END = 2
EVENT_TTS_ERROR = 3
EVENT_TTS_FLUSH = 5


@dataclass
class TTSQueueRequest:
    """TTS 队列请求数据类（用于内部队列管理）"""
    text: str
    is_last: bool = False
    # None 表示正常请求，"STOP" 表示停止信号
    signal: Optional[str] = None
    # 请求序号，用于有序输出
    sequence: int = 0


@dataclass
class PrefetchedAudio:
    """预取的音频数据"""
    sequence: int
    pcm_data: bytearray  # 缓存的 PCM 数据
    is_complete: bool = False
    is_last: bool = False
    text: str = ""
    has_error: bool = False  # 预取是否出错（用于回退到同步处理）


class FishAudioClient:
    """Fish Audio WebSocket 客户端封装"""

    def __init__(self, config: dict, ten_env=None):
        self.config = config
        self.ten_env = ten_env
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "")
        self.backend = config.get("backend", "speech-1.5")
        self.sample_rate = int(config.get("sample_rate", 16000))
        self.format = config.get("format", "pcm")

        # 构建请求参数
        self.params = {
            "format": self.format,
            "sample_rate": self.sample_rate,
            "latency": config.get("latency", "normal"),  # 改为 normal 以降低首字延迟
        }

        # 参考音频/声音克隆 - 优先使用 private_voice（用户选择的音色）
        if config.get("private_voice"):
            self.params["reference_id"] = config.get("private_voice")
            logger.bind(tag=TAG).info(f"Fish Audio TTS: 使用用户音色 reference_id={config.get('private_voice')}")
        elif config.get("reference_id"):
            self.params["reference_id"] = config.get("reference_id")
            logger.bind(tag=TAG).info(f"Fish Audio TTS: 使用默认音色 reference_id={config.get('reference_id')}")

        # 生成参数
        if config.get("top_p"):
            self.params["top_p"] = float(config.get("top_p"))
        if config.get("temperature"):
            self.params["temperature"] = float(config.get("temperature"))
        if config.get("repetition_penalty"):
            self.params["repetition_penalty"] = float(config.get("repetition_penalty"))

        self.client = None
        self._is_cancelled = False

    def _init_client(self):
        """延迟初始化客户端"""
        if self.client is None:
            try:
                from fish_audio_sdk import AsyncWebSocketSession
                if self.base_url.strip():
                    self.client = AsyncWebSocketSession(
                        self.api_key, base_url=self.base_url
                    )
                else:
                    self.client = AsyncWebSocketSession(self.api_key)
            except ImportError:
                logger.bind(tag=TAG).error(
                    "fish_audio_sdk 未安装，请运行: pip install fish-audio-sdk"
                )
                raise

    async def _text_stream(self, text: str) -> AsyncIterator[str]:
        """文本流生成器"""
        yield text

    async def get(self, text: str) -> AsyncIterator[tuple[bytes | None, int]]:
        """
        流式获取 TTS 音频

        Args:
            text: 要合成的文本

        Yields:
            (audio_bytes, event_type): 音频数据和事件类型
        """
        self._is_cancelled = False
        self._init_client()

        if not self.client:
            yield None, EVENT_TTS_ERROR
            return

        try:
            from fish_audio_sdk import TTSRequest

            logger.bind(tag=TAG).info(f"Fish Audio 请求参数: {self.params}")
            tts_request = TTSRequest(text="", chunk_length=200, **self.params)

            gen: AsyncIterator[bytes] | None = None

            try:
                gen = self.client.tts(
                    request=tts_request,
                    text_stream=self._text_stream(text),
                    backend=self.backend,
                )

                async for chunk in gen:
                    if self._is_cancelled:
                        logger.bind(tag=TAG).debug(
                            "Fish Audio TTS: 检测到取消标志，停止流"
                        )
                        yield None, EVENT_TTS_FLUSH
                        await gen.aclose()
                        return

                    if len(chunk) > 0:
                        yield chunk, EVENT_TTS_RESPONSE

                # 正常结束
                if not self._is_cancelled:
                    yield None, EVENT_TTS_END

            except Exception as e:
                error_message = str(e)
                logger.bind(tag=TAG).error(f"Fish Audio TTS 错误: {error_message}")

                # 检查是否是认证错误
                if "402" in error_message or "Payment Required" in error_message:
                    logger.bind(tag=TAG).error("Fish Audio API Key 无效或余额不足")

                yield error_message.encode("utf-8"), EVENT_TTS_ERROR

            finally:
                if gen is not None:
                    try:
                        # 使用 shield 保护 aclose()，避免被外部取消打断
                        # 这可以减少 anyio cancel scope 跨任务退出的问题
                        await asyncio.shield(gen.aclose())
                    except asyncio.CancelledError:
                        # shield 会将 CancelledError 转换为普通异常，忽略即可
                        pass
                    except Exception as close_error:
                        # anyio cancel scope 异常属于预期行为，降级为 debug 级别
                        if "cancel scope" in str(close_error).lower():
                            logger.bind(tag=TAG).debug(
                                f"Fish Audio TTS: 关闭生成器时 cancel scope 异常（预期）"
                            )
                        else:
                            logger.bind(tag=TAG).warning(
                                f"Fish Audio TTS: 关闭生成器失败: {close_error}"
                            )

        except ImportError:
            logger.bind(tag=TAG).error("fish_audio_sdk 未安装")
            yield b"fish_audio_sdk not installed", EVENT_TTS_ERROR

    def cancel(self):
        """取消当前 TTS 请求"""
        logger.bind(tag=TAG).debug("Fish Audio TTS: cancel() 被调用")
        self._is_cancelled = True

    def clean(self):
        """清理资源"""
        logger.bind(tag=TAG).debug("Fish Audio TTS: clean() 被调用")
        self._is_cancelled = False

    async def warm_up(self):
        """
        预热连接 - 提前建立 WebSocket 连接
        
        在用户连接时调用，避免首次 TTS 请求时的连接建立延迟
        预期收益：50-150ms
        """
        import time
        start_time = time.time()
        
        try:
            self._init_client()
            
            if not self.client:
                logger.bind(tag=TAG).warning("Fish Audio TTS: 预热失败，客户端未初始化")
                return False
            
            # 尝试建立连接（发送一个极短的预热请求）
            # Fish Audio SDK 的 WebSocket 连接在首次 tts() 调用时建立
            from fish_audio_sdk import TTSRequest
            
            # 使用空格作为预热文本，不会产生实际音频但会建立连接
            tts_request = TTSRequest(text="", chunk_length=200, **self.params)
            
            try:
                gen = self.client.tts(
                    request=tts_request,
                    text_stream=self._text_stream(" "),  # 发送一个空格
                    backend=self.backend,
                )
                
                # 只读取第一个响应即可（建立连接）
                async for _ in gen:
                    await gen.aclose()
                    break
                    
            except Exception as e:
                # 预热失败不影响正常流程，可能是空文本被拒绝
                logger.bind(tag=TAG).debug(f"Fish Audio TTS: 预热请求完成（可能无音频输出）: {e}")
            
            elapsed = (time.time() - start_time) * 1000
            logger.bind(tag=TAG).info(f"Fish Audio TTS: 连接预热完成，耗时 {elapsed:.0f}ms")
            return True
            
        except ImportError:
            logger.bind(tag=TAG).error("Fish Audio TTS: 预热失败，fish_audio_sdk 未安装")
            return False
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Fish Audio TTS: 预热失败: {e}")
            return False


class TTSProvider(TTSProviderBase):
    """Fish Audio TTS 流式提供者"""

    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        # 保存配置（用于预取时创建独立客户端）
        self.config = config

        # 设置接口类型为单向流式
        self.interface_type = InterfaceType.SINGLE_STREAM

        # 初始化 Fish Audio 客户端
        self.fish_client = FishAudioClient(config)

        # 音频参数
        self.sample_rate = int(config.get("sample_rate", 16000))
        self.audio_format = config.get("format", "pcm")

        # 创建 Opus 编码器
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=self.sample_rate, channels=1, frame_size_ms=60
        )

        # PCM 缓冲区
        self.pcm_buffer = bytearray()

        # 计算每帧字节数
        self.frame_bytes = int(
            self.sample_rate * 1 * 60 / 1000 * 2  # 16-bit = 2 bytes
        )

        # 异步 TTS 请求队列（用于非阻塞提交）
        self._tts_request_queue: Optional[asyncio.Queue] = None
        self._tts_worker_task: Optional[asyncio.Task] = None
        
        # 预取机制相关
        self._prefetch_enabled = config.get("prefetch_enabled", True)  # 是否启用预取
        self._max_prefetch = config.get("max_prefetch", 3)  # 最大预取数量
        self._prefetch_tasks: dict = {}  # 预取任务 {sequence: asyncio.Task}
        self._prefetch_buffers: dict = {}  # 预取缓冲区 {sequence: PrefetchedAudio}
        self._current_output_sequence = 0  # 当前应该输出的序号
        self._request_sequence = 0  # 请求序号计数器

    async def open_audio_channels(self, conn):
        """打开音频通道，初始化异步队列和工作协程"""
        await super().open_audio_channels(conn)

        # 初始化 TTS 请求队列
        self._tts_request_queue = asyncio.Queue()
        
        # 重置预取状态
        self._prefetch_tasks = {}
        self._prefetch_buffers = {}
        self._current_output_sequence = 0
        self._request_sequence = 0

        # 预热 TTS 连接（提前建立 WebSocket 连接，降低首次请求延迟）
        try:
            await self.fish_client.warm_up()
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Fish Audio TTS 预热失败，将在首次请求时建立连接: {e}")

        # 启动 TTS 工作协程
        self._tts_worker_task = asyncio.create_task(self._tts_worker())
        logger.bind(tag=TAG).info(
            f"Fish Audio TTS 工作协程已启动 (prefetch={self._prefetch_enabled}, max_prefetch={self._max_prefetch})"
        )

    async def _tts_worker(self):
        """
        TTS 请求处理工作协程
        
        支持预取模式：在处理当前句子的同时，提前发起下一个句子的 TTS 请求
        """
        logger.bind(tag=TAG).info("TTS worker 开始运行")
        loop_count = 0
        last_log_time = 0
        import time as time_module
        
        while not self.conn.stop_event.is_set():
            loop_count += 1
            current_time = time_module.time()
            try:
                # 检查队列状态
                if self._tts_request_queue is None:
                    logger.bind(tag=TAG).error("TTS worker: 队列为 None，退出")
                    break
                    
                queue_size = self._tts_request_queue.qsize()
                
                # 每5秒记录一次 worker 存活状态
                if current_time - last_log_time >= 5:
                    logger.bind(tag=TAG).info(f"TTS worker 存活: loop={loop_count}, queue_size={queue_size}, client_abort={self.conn.client_abort}")
                    last_log_time = current_time
                
                # 等待队列中的请求
                try:
                    request: TTSQueueRequest = await asyncio.wait_for(
                        self._tts_request_queue.get(), timeout=1.0
                    )
                    logger.bind(tag=TAG).info(f"TTS worker: 从队列获取请求 seq={request.sequence}, text={request.text[:20] if request.text else '[empty]'}, queue_size_after={self._tts_request_queue.qsize()}")
                except asyncio.TimeoutError:
                    continue

                # 检查停止信号
                if request.signal == "STOP":
                    logger.bind(tag=TAG).info("TTS worker 收到停止信号，退出")
                    await self._cancel_all_prefetch()
                    break

                # 检查打断
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info(f"TTS worker: 检测到打断，跳过请求 seq={request.sequence}, client_abort={self.conn.client_abort}")
                    try:
                        logger.bind(tag=TAG).info("TTS worker: 开始取消预取任务...")
                        await self._cancel_all_prefetch()
                        logger.bind(tag=TAG).info("TTS worker: 取消预取完成，继续循环")
                    except Exception as e:
                        logger.bind(tag=TAG).warning(f"TTS worker: 取消预取任务异常: {e}, traceback: {traceback.format_exc()}")
                    continue

                # 处理 TTS 请求
                if request.text:
                    seq = request.sequence
                    logger.bind(tag=TAG).info(
                        f"TTS worker 处理请求 seq={seq}: {request.text[:30]}..."
                    )
                    
                    # 检查是否已经预取过这个序号
                    if seq in self._prefetch_buffers:
                        # 已预取，直接输出缓冲区的数据
                        logger.bind(tag=TAG).info(f"TTS worker: 使用预取数据 seq={seq}")
                        await self._output_prefetched_audio(seq, request.is_last)
                    else:
                        # 未预取，同时启动预取下一个并处理当前请求
                        logger.bind(tag=TAG).info(f"TTS worker: 开始处理（无预取）seq={seq}")
                        await self._process_with_prefetch(request)
                    logger.bind(tag=TAG).info(f"TTS worker: 请求处理完成 seq={seq}")
                        
                elif request.is_last:
                    # 空文本但标记为 last，处理待播放文件
                    logger.bind(tag=TAG).info("TTS worker: 处理 is_last 空请求")
                    self._process_before_stop_play_files()

            except asyncio.CancelledError:
                # CancelledError 可能来自：
                # 1. close() 主动取消 worker（应该退出）
                # 2. 内部 await 被取消后传播上来（不应该退出）
                # 通过检查 stop_event 来区分这两种情况
                if self.conn.stop_event.is_set():
                    logger.bind(tag=TAG).info(f"TTS worker 被 CancelledError 取消，stop_event 已设置，退出 (loop={loop_count})")
                    try:
                        await self._cancel_all_prefetch()
                    except Exception as e:
                        logger.bind(tag=TAG).warning(f"TTS worker: CancelledError 后取消预取异常: {e}")
                    break
                else:
                    # stop_event 未设置，说明不是 close() 导致的取消
                    # 尝试清除取消状态（Python 3.11+）以避免死循环
                    current_task = asyncio.current_task()
                    if current_task and hasattr(current_task, 'uncancel'):
                        uncancel_count = current_task.uncancel()
                        logger.bind(tag=TAG).warning(f"TTS worker 收到意外的 CancelledError，已清除取消状态 (loop={loop_count}, uncancel_count={uncancel_count})")
                    else:
                        # Python < 3.11 没有 uncancel 方法，退出 worker 让重启机制生效
                        logger.bind(tag=TAG).warning(f"TTS worker 收到意外的 CancelledError，无法清除取消状态，退出并等待重启 (loop={loop_count})")
                        try:
                            await self._cancel_all_prefetch()
                        except Exception as e:
                            logger.bind(tag=TAG).warning(f"TTS worker: 处理意外 CancelledError 时取消预取异常: {e}")
                        break
                    try:
                        await self._cancel_all_prefetch()
                    except Exception as e:
                        logger.bind(tag=TAG).warning(f"TTS worker: 处理意外 CancelledError 时取消预取异常: {e}")
                    continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"TTS worker 处理失败: {str(e)}, 堆栈: {traceback.format_exc()}"
                )

        logger.bind(tag=TAG).info(f"TTS worker 退出: loop_count={loop_count}, stop_event={self.conn.stop_event.is_set()}, queue_is_none={self._tts_request_queue is None}")

    async def _restart_worker(self):
        """
        重新启动 TTS worker
        
        当 worker 因为 CancelledError 或其他原因退出后，重新创建并启动
        """
        logger.bind(tag=TAG).info("_restart_worker: 开始重启 TTS worker")
        
        # 确保旧任务已经结束
        if self._tts_worker_task and not self._tts_worker_task.done():
            logger.bind(tag=TAG).warning("_restart_worker: 旧 worker 仍在运行，先取消")
            self._tts_worker_task.cancel()
            try:
                await self._tts_worker_task
            except asyncio.CancelledError:
                pass
        
        # 重置相关状态
        self._prefetch_tasks.clear()
        self._prefetch_buffers.clear()
        self._request_sequence = 0
        self._current_output_sequence = 0
        
        # 确保队列存在
        if self._tts_request_queue is None:
            self._tts_request_queue = asyncio.Queue()
            logger.bind(tag=TAG).info("_restart_worker: 重新创建请求队列")
        
        # 创建新的 worker 任务
        self._tts_worker_task = asyncio.create_task(self._tts_worker())
        logger.bind(tag=TAG).info("_restart_worker: TTS worker 重启完成")

    async def _process_with_prefetch(self, request: TTSQueueRequest):
        """
        处理当前请求，同时预取下一个
        
        Args:
            request: 当前要处理的请求
        """
        seq = request.sequence
        logger.bind(tag=TAG).info(f"_process_with_prefetch 开始: seq={seq}, text={request.text[:20] if request.text else '[empty]'}...")
        
        # 启动预取任务（如果启用且队列中有更多请求）
        if self._prefetch_enabled:
            await self._start_prefetch_tasks()
        
        # 处理当前请求（直接输出）
        logger.bind(tag=TAG).info(f"_process_with_prefetch: 开始 _text_to_speak_stream seq={seq}")
        await self._text_to_speak_stream(request.text, request.is_last)
        logger.bind(tag=TAG).info(f"_process_with_prefetch: _text_to_speak_stream 完成 seq={seq}")
        
        # 更新输出序号
        self._current_output_sequence = seq + 1
        
        # 处理后续已预取完成的请求
        await self._flush_prefetch_buffers()
        logger.bind(tag=TAG).info(f"_process_with_prefetch 完成: seq={seq}")

    async def _start_prefetch_tasks(self):
        """
        启动预取任务
        
        检查队列中的请求，启动多个预取任务（最多 max_prefetch 个）
        """
        # 计算可启动的预取数量
        active_prefetch = len([t for t in self._prefetch_tasks.values() if not t.done()])
        available_slots = self._max_prefetch - active_prefetch
        
        if available_slots <= 0:
            return
        
        # 尝试从队列中获取多个请求进行预取
        requests_to_prefetch = []
        requests_to_return = []
        
        try:
            while len(requests_to_prefetch) < available_slots:
                if self._tts_request_queue.empty():
                    break
                
                next_request: TTSQueueRequest = self._tts_request_queue.get_nowait()
                
                # 跳过停止信号和打断
                if next_request.signal == "STOP" or self.conn.client_abort:
                    requests_to_return.append(next_request)
                    break
                
                seq = next_request.sequence
                
                # 如果已经在预取或已完成，跳过
                if seq in self._prefetch_tasks or seq in self._prefetch_buffers:
                    requests_to_return.append(next_request)
                    continue
                
                requests_to_prefetch.append(next_request)
                
        except asyncio.QueueEmpty:
            pass
        
        # 将需要放回的请求放回队列（按原顺序）
        for req in requests_to_return:
            await self._tts_request_queue.put(req)
        
        # 启动预取任务
        for request in requests_to_prefetch:
            seq = request.sequence
            logger.bind(tag=TAG).info(f"启动预取 seq={seq}: {request.text[:30]}...")
            task = asyncio.create_task(self._prefetch_audio(request))
            self._prefetch_tasks[seq] = task

    async def _prefetch_audio(self, request: TTSQueueRequest):
        """
        预取音频数据（缓存 PCM 到 buffer，不立即编码输出）
        
        Args:
            request: 要预取的请求
        """
        seq = request.sequence
        buffer = PrefetchedAudio(
            sequence=seq,
            pcm_data=bytearray(),
            is_last=request.is_last,
            text=request.text
        )
        self._prefetch_buffers[seq] = buffer
        
        # 为预取创建独立的 FishAudioClient 实例，避免取消时的任务上下文问题
        prefetch_client = FishAudioClient(self.config)
        
        try:
            async for audio_data, event_type in prefetch_client.get(request.text):
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info(f"预取 seq={seq} 被打断")
                    prefetch_client.cancel()
                    break
                
                if event_type == EVENT_TTS_RESPONSE and audio_data:
                    # 缓存 PCM 数据
                    buffer.pcm_data.extend(audio_data)
                
                elif event_type == EVENT_TTS_END:
                    logger.bind(tag=TAG).info(
                        f"预取 seq={seq} 完成，缓存 {len(buffer.pcm_data)} bytes PCM"
                    )
                
                elif event_type == EVENT_TTS_ERROR:
                    logger.bind(tag=TAG).error(f"预取 seq={seq} 错误: {audio_data}")
                    buffer.has_error = True
                    break
            
            buffer.is_complete = True
            
        except asyncio.CancelledError:
            logger.bind(tag=TAG).info(f"预取 seq={seq} 任务被取消")
            prefetch_client.cancel()
            buffer.has_error = True
            buffer.is_complete = True
            raise  # 重新抛出以正确处理取消
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"预取 seq={seq} 异常: {e}")
            buffer.has_error = True
            buffer.is_complete = True
        
        finally:
            prefetch_client.clean()

    async def _output_prefetched_audio(self, seq: int, is_last: bool):
        """
        输出已预取的音频数据
        
        如果预取失败，会回退到同步处理模式重新请求
        
        Args:
            seq: 序号
            is_last: 是否是最后一段
        """
        buffer = self._prefetch_buffers.get(seq)
        if not buffer:
            logger.bind(tag=TAG).warning(f"预取缓冲区 seq={seq} 不存在")
            return
        
        # 等待预取完成
        task = self._prefetch_tasks.get(seq)
        if task and not task.done():
            logger.bind(tag=TAG).debug(f"等待预取 seq={seq} 完成...")
            await task
        
        text = buffer.text
        
        # 检查预取是否失败（有错误或数据为空）
        if buffer.has_error or (not buffer.pcm_data and text):
            logger.bind(tag=TAG).warning(
                f"预取 seq={seq} 失败 (error={buffer.has_error}, data_empty={not buffer.pcm_data})，回退到同步处理"
            )
            # 清理失败的预取
            self._prefetch_buffers.pop(seq, None)
            self._prefetch_tasks.pop(seq, None)
            
            # 回退到同步处理
            await self._text_to_speak_stream(text, is_last)
            
            # 更新输出序号
            self._current_output_sequence = seq + 1
            return
        
        # 输出音频（编码 PCM 为 Opus）
        if buffer.pcm_data:
            # 记录 TTS 首音频时间（预取模式）
            if hasattr(self.conn, 'latency_metrics') and self.conn.latency_metrics:
                self.conn.latency_metrics.mark_tts_first_audio()
            
            self.tts_audio_queue.put((SentenceType.FIRST, [], text))
            
            # 分帧编码输出
            pcm_data = buffer.pcm_data
            offset = 0
            while offset + self.frame_bytes <= len(pcm_data):
                frame = bytes(pcm_data[offset:offset + self.frame_bytes])
                offset += self.frame_bytes
                self.opus_encoder.encode_pcm_to_opus_stream(
                    frame, end_of_stream=False, callback=self.handle_opus
                )
            
            # 处理剩余数据
            if offset < len(pcm_data):
                remaining = bytes(pcm_data[offset:])
                self.opus_encoder.encode_pcm_to_opus_stream(
                    remaining, end_of_stream=True, callback=self.handle_opus
                )
            
            logger.bind(tag=TAG).info(f"已输出预取 seq={seq} 的音频")
        
        # 清理
        self._prefetch_buffers.pop(seq, None)
        self._prefetch_tasks.pop(seq, None)
        
        # 更新输出序号
        self._current_output_sequence = seq + 1
        
        if is_last:
            self._process_before_stop_play_files()

    async def _flush_prefetch_buffers(self):
        """
        刷新已完成的预取缓冲区
        
        按顺序输出所有已预取完成的音频
        """
        while True:
            next_seq = self._current_output_sequence
            buffer = self._prefetch_buffers.get(next_seq)
            
            if not buffer or not buffer.is_complete:
                break
            
            logger.bind(tag=TAG).debug(f"刷新预取缓冲区 seq={next_seq}")
            await self._output_prefetched_audio(next_seq, buffer.is_last)

    async def _cancel_all_prefetch(self):
        """
        取消所有预取任务
        
        采用两阶段取消策略，避免 anyio cancel scope 跨任务退出问题：
        1. 第一阶段：设置 client_abort 标志，让生成器优雅退出（协作式取消）
        2. 第二阶段：如果超时，强制取消任务（非协作式取消）
        """
        pending_tasks = [(seq, task) for seq, task in self._prefetch_tasks.items() if not task.done()]
        logger.bind(tag=TAG).info(f"_cancel_all_prefetch 开始: pending_tasks={len(pending_tasks)}, buffers={len(self._prefetch_buffers)}")
        
        if not pending_tasks:
            self._prefetch_tasks.clear()
            self._prefetch_buffers.clear()
            logger.bind(tag=TAG).info("_cancel_all_prefetch: 无待取消任务，直接返回")
            return
        
        # 第一阶段：等待协作式取消（client_abort 已被设置）
        # 给生成器 500ms 时间优雅退出
        logger.bind(tag=TAG).info(f"_cancel_all_prefetch: 第一阶段，等待 {len(pending_tasks)} 个任务优雅退出...")
        try:
            done, pending = await asyncio.wait(
                [task for _, task in pending_tasks],
                timeout=0.5,
                return_when=asyncio.ALL_COMPLETED
            )
            logger.bind(tag=TAG).info(f"_cancel_all_prefetch: 第一阶段完成，done={len(done)}, pending={len(pending)}")
        except Exception as e:
            logger.bind(tag=TAG).warning(f"_cancel_all_prefetch: 等待预取任务优雅退出异常: {e}")
            pending = [task for _, task in pending_tasks]
        
        # 第二阶段：强制取消仍在运行的任务
        force_cancel_count = 0
        for seq, task in pending_tasks:
            if not task.done():
                force_cancel_count += 1
                logger.bind(tag=TAG).info(f"_cancel_all_prefetch: 预取任务 seq={seq} 未能优雅退出，强制取消")
                task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=1.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
                except Exception as e:
                    # 这里可能会收到 anyio cancel scope 异常，属于预期行为
                    logger.bind(tag=TAG).info(f"_cancel_all_prefetch: 预取任务 seq={seq} 强制取消时异常（预期）: {e}")
        
        self._prefetch_tasks.clear()
        self._prefetch_buffers.clear()
        logger.bind(tag=TAG).info(f"_cancel_all_prefetch 完成: force_cancel_count={force_cancel_count}")

    def _submit_tts_request(self, text: str, is_last: bool = False):
        """
        非阻塞提交 TTS 请求到异步队列
        
        Args:
            text: 要合成的文本
            is_last: 是否是最后一段
        """
        if self._tts_request_queue is None:
            logger.bind(tag=TAG).error("TTS 请求队列为 None，无法提交请求")
            return

        # 分配序号
        seq = self._request_sequence
        self._request_sequence += 1
        
        request = TTSQueueRequest(
            text=MarkdownCleaner.clean_markdown(text) if text else "",
            is_last=is_last,
            sequence=seq
        )

        # 记录提交前的队列大小
        queue_size_before = self._tts_request_queue.qsize() if self._tts_request_queue else -1

        # 非阻塞提交到队列
        future = asyncio.run_coroutine_threadsafe(
            self._tts_request_queue.put(request),
            self.conn.loop
        )
        logger.bind(tag=TAG).info(f"TTS 请求已提交 seq={seq}, is_last={is_last}, queue_size_before={queue_size_before}: {text[:30] if text else '[empty]'}...")

    def tts_text_priority_thread(self):
        """
        流式文本处理线程
        
        非阻塞提交 TTS 请求，由 _tts_worker 协程串行处理
        """
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).info(f"TTS 文本线程收到消息: type={message.sentence_type}, content_type={message.content_type}, client_abort={self.conn.client_abort}")

                if message.sentence_type == SentenceType.FIRST:
                    # 初始化参数
                    worker_done = self._tts_worker_task.done() if self._tts_worker_task else True
                    logger.bind(tag=TAG).info(f"TTS FIRST: 开始处理，重置状态 (当前 client_abort={self.conn.client_abort}, queue_size={self._tts_request_queue.qsize() if self._tts_request_queue else -1}, worker_done={worker_done})")
                    
                    # 检查 worker 是否退出，如果退出则重新启动
                    if worker_done:
                        logger.bind(tag=TAG).warning("TTS FIRST: worker 已退出，正在重新启动...")
                        try:
                            # 清空队列
                            if self._tts_request_queue:
                                while not self._tts_request_queue.empty():
                                    try:
                                        self._tts_request_queue.get_nowait()
                                    except:
                                        break
                            # 重新创建 worker 任务
                            future = asyncio.run_coroutine_threadsafe(
                                self._restart_worker(),
                                self.conn.loop
                            )
                            future.result(timeout=2.0)
                            logger.bind(tag=TAG).info("TTS FIRST: worker 重启成功")
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"TTS FIRST: worker 重启失败: {e}, traceback: {traceback.format_exc()}")
                    
                    self.conn.client_abort = False
                    self.tts_stop_request = False
                    self.processed_chars = 0
                    self.tts_text_buff = []
                    self.is_first_sentence = True  # 重置首句标志，用于延迟监控
                    self.before_stop_play_files.clear()
                    self.fish_client.clean()
                    self.tts_audio_first_sentence = True
                    
                    # 重置预取状态（新的一轮对话）
                    self._request_sequence = 0
                    self._current_output_sequence = 0
                    # 取消所有pending的预取任务（同步等待完成，避免影响新请求）
                    logger.bind(tag=TAG).info("TTS FIRST: 开始取消预取任务（同步等待）...")
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self._cancel_all_prefetch(),
                            self.conn.loop
                        )
                        # 等待取消完成，最多 2 秒
                        future.result(timeout=2.0)
                        logger.bind(tag=TAG).info(f"TTS FIRST: 取消预取任务完成 (queue_size={self._tts_request_queue.qsize() if self._tts_request_queue else -1})")
                    except TimeoutError as e:
                        logger.bind(tag=TAG).error(f"TTS FIRST: 取消预取任务超时: {e}")
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"TTS FIRST: 取消预取任务异常: {e}, traceback: {traceback.format_exc()}")

                if self.conn.client_abort:
                    logger.bind(tag=TAG).info(f"收到打断信息，取消 TTS，跳过消息: type={message.sentence_type}")
                    self.fish_client.cancel()
                    continue

                if ContentType.TEXT == message.content_type:
                    self.tts_text_buff.append(message.content_detail)
                    # 保存首句状态（_get_segment_text 会修改 is_first_sentence）
                    was_first_sentence = self.is_first_sentence
                    segment_text = self._get_segment_text()
                    if segment_text:
                        # 记录首句 TTS 请求时间
                        if was_first_sentence:
                            if hasattr(self.conn, 'latency_metrics') and self.conn.latency_metrics:
                                self.conn.latency_metrics.mark_tts_request(segment_text)
                        # 非阻塞提交 TTS 请求
                        self._submit_tts_request(segment_text, is_last=False)

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
                    # 处理剩余的文本（非阻塞）
                    self._process_remaining_text_nonblocking()

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"处理 TTS 文本失败: {str(e)}, 类型: {type(e).__name__}, "
                    f"堆栈: {traceback.format_exc()}"
                )

    def _process_remaining_text_nonblocking(self):
        """
        非阻塞处理剩余的文本
        
        提交剩余文本到 TTS 队列，标记为 is_last=True
        """
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars:]
        logger.bind(tag=TAG).info(f"处理剩余文本: full_text长度={len(full_text)}, processed_chars={self.processed_chars}, remaining长度={len(remaining_text)}")

        if remaining_text:
            segment_text = textUtils.get_string_no_punctuation_or_emoji(remaining_text)
            if segment_text:
                # 非阻塞提交最后一段文本
                self._submit_tts_request(segment_text, is_last=True)
                self.processed_chars += len(full_text)
            else:
                # 没有有效文本，直接提交空请求标记结束
                self._submit_tts_request("", is_last=True)
        else:
            # 没有剩余文本，直接提交空请求标记结束
            self._submit_tts_request("", is_last=True)

    async def _text_to_speak_stream(self, text: str, is_last: bool):
        """异步流式 TTS"""
        try:
            self.pcm_buffer.clear()
            self.tts_audio_queue.put((SentenceType.FIRST, [], text))

            async for audio_data, event_type in self.fish_client.get(text):
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("检测到打断，停止接收音频")
                    self.fish_client.cancel()
                    break

                if event_type == EVENT_TTS_RESPONSE and audio_data:
                    # 累积 PCM 数据
                    if len(self.pcm_buffer) == 0:
                        # 首次收到数据，打印详细信息
                        first_bytes = audio_data[:16].hex() if len(audio_data) >= 16 else audio_data.hex()
                        logger.bind(tag=TAG).info(f"Fish Audio PCM: {len(audio_data)} bytes, 前16字节: {first_bytes}")
                        # 记录 TTS 首音频时间
                        if hasattr(self.conn, 'latency_metrics') and self.conn.latency_metrics:
                            self.conn.latency_metrics.mark_tts_first_audio()
                    self.pcm_buffer.extend(audio_data)

                    # 当缓冲区有足够数据时，编码并发送
                    while len(self.pcm_buffer) >= self.frame_bytes:
                        frame = bytes(self.pcm_buffer[: self.frame_bytes])
                        del self.pcm_buffer[: self.frame_bytes]

                        self.opus_encoder.encode_pcm_to_opus_stream(
                            frame, end_of_stream=False, callback=self.handle_opus
                        )

                elif event_type == EVENT_TTS_END:
                    logger.bind(tag=TAG).info(f"TTS 完成: {text}")

                elif event_type == EVENT_TTS_ERROR:
                    logger.bind(tag=TAG).error(f"TTS 错误: {audio_data}")

                elif event_type == EVENT_TTS_FLUSH:
                    logger.bind(tag=TAG).debug("TTS 被取消")
                    break

            # 处理剩余的 PCM 数据
            if self.pcm_buffer:
                self.opus_encoder.encode_pcm_to_opus_stream(
                    bytes(self.pcm_buffer),
                    end_of_stream=True,
                    callback=self.handle_opus,
                )
                self.pcm_buffer.clear()

            # 如果是最后一段，处理待播放文件
            if is_last:
                self._process_before_stop_play_files()

        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS 请求异常: {e}")
            self.tts_audio_queue.put((SentenceType.LAST, [], None))

    async def text_to_speak(self, text, output_file):
        """
        非流式 TTS（用于兼容基类接口）

        注意：此方法主要用于测试或需要保存文件的场景
        实际流式处理使用 _text_to_speak_stream
        """
        audio_bytes = bytearray()

        async for audio_data, event_type in self.fish_client.get(text):
            if event_type == EVENT_TTS_RESPONSE and audio_data:
                audio_bytes.extend(audio_data)
            elif event_type == EVENT_TTS_END:
                break
            elif event_type == EVENT_TTS_ERROR:
                raise Exception(f"TTS 错误: {audio_data}")

        if output_file:
            with open(output_file, "wb") as f:
                f.write(audio_bytes)
        else:
            return bytes(audio_bytes)

    async def close(self):
        """资源清理"""
        logger.bind(tag=TAG).info(f"TTS close 开始: worker_task_done={self._tts_worker_task.done() if self._tts_worker_task else 'None'}, queue_is_none={self._tts_request_queue is None}")
        
        # 停止 TTS 工作协程
        if self._tts_worker_task and not self._tts_worker_task.done():
            # 发送停止信号
            if self._tts_request_queue:
                try:
                    logger.bind(tag=TAG).info("TTS close: 发送 STOP 信号")
                    await self._tts_request_queue.put(TTSQueueRequest(text="", signal="STOP"))
                except Exception as e:
                    logger.bind(tag=TAG).warning(f"TTS close: 发送 STOP 信号失败: {e}")

            # 取消任务
            logger.bind(tag=TAG).info("TTS close: 取消 worker 任务")
            self._tts_worker_task.cancel()
            try:
                await self._tts_worker_task
            except asyncio.CancelledError:
                pass
            self._tts_worker_task = None
            logger.bind(tag=TAG).info("TTS 工作协程已停止")
        else:
            logger.bind(tag=TAG).info(f"TTS close: worker 任务已完成或为 None")

        # 清空请求队列
        if self._tts_request_queue:
            queue_size = self._tts_request_queue.qsize()
            while not self._tts_request_queue.empty():
                try:
                    self._tts_request_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            logger.bind(tag=TAG).info(f"TTS close: 清空队列完成，原大小={queue_size}")
            self._tts_request_queue = None

        await super().close()
        if hasattr(self, "opus_encoder"):
            self.opus_encoder.close()
        if hasattr(self, "fish_client"):
            self.fish_client.clean()

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

        async def _generate():
            async for audio_data, event_type in self.fish_client.get(text):
                if event_type == EVENT_TTS_RESPONSE and audio_data:
                    # 分帧处理
                    for i in range(0, len(audio_data), self.frame_bytes):
                        frame = audio_data[i: i + self.frame_bytes]
                        if len(frame) < self.frame_bytes:
                            frame = frame + b"\x00" * (self.frame_bytes - len(frame))

                        self.opus_encoder.encode_pcm_to_opus_stream(
                            frame,
                            end_of_stream=False,
                            callback=lambda opus: opus_datas.append(opus),
                        )
                elif event_type == EVENT_TTS_END:
                    break
                elif event_type == EVENT_TTS_ERROR:
                    logger.bind(tag=TAG).error(f"TTS 错误: {audio_data}")
                    break

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_generate())
            loop.close()
        except Exception as e:
            logger.bind(tag=TAG).error(f"to_tts 失败: {e}")

        return opus_datas


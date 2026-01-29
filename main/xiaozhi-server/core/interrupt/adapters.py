"""
打断模块适配器

提供与现有组件集成的适配器类，降低接入成本。
适配器将现有组件的接口转换为打断模块所需的协议。
"""

import json
import asyncio
import queue
import logging
import traceback
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

from .types import (
    InterruptTarget,
    InterruptEvent,
    FlushRequest,
    RequestContext,
)
from .protocol import (
    Interruptible,
    QueueFlushable,
    TaskCancellable,
    InterruptNotifier,
    InterruptCallback,
)

if TYPE_CHECKING:
    # 避免循环导入，仅用于类型检查
    pass

# 模块级日志
_logger = logging.getLogger(__name__)
TAG = "InterruptAdapter"


def _log_debug(adapter_name: str, message: str) -> None:
    """适配器调试日志"""
    _logger.debug(f"[{TAG}][{adapter_name}] {message}")


def _log_info(adapter_name: str, message: str) -> None:
    """适配器信息日志"""
    _logger.info(f"[{TAG}][{adapter_name}] {message}")


def _log_warning(adapter_name: str, message: str) -> None:
    """适配器警告日志"""
    _logger.warning(f"[{TAG}][{adapter_name}] {message}")


def _log_error(adapter_name: str, message: str) -> None:
    """适配器错误日志"""
    _logger.error(f"[{TAG}][{adapter_name}] {message}")


class TTSAdapter(Interruptible, QueueFlushable):
    """
    TTS 组件适配器
    
    将现有的 TTS Provider 适配为 Interruptible 协议。
    
    使用示例:
        from core.providers.tts.base import TTSProviderBase
        
        tts_provider = MyTTSProvider(config)
        adapter = TTSAdapter(tts_provider)
        
        manager.register_target(
            InterruptTarget.TTS,
            adapter,
            queue=adapter,  # 同时作为队列组件
        )
    """
    
    def __init__(self, tts_provider: Any, debug: bool = False):
        """
        初始化 TTS 适配器
        
        Args:
            tts_provider: TTS Provider 实例（如 TTSProviderBase 的子类）
            debug: 是否启用调试日志
        """
        self._provider = tts_provider
        self._current_request_id: Optional[str] = None
        self._flush_request_id: Optional[str] = None
        self._debug = debug
        
        provider_type = type(tts_provider).__name__
        _log_info("TTSAdapter", f"初始化: provider={provider_type}")
    
    async def on_interrupt(self, flush_request: FlushRequest) -> bool:
        """处理打断请求"""
        _log_info("TTSAdapter", f"收到打断请求: flush_id={flush_request.flush_id[:16]}...")
        
        try:
            # 记录被 flush 的请求 ID
            if self._current_request_id:
                self._flush_request_id = self._current_request_id
                _log_debug("TTSAdapter", f"记录被打断的请求: {self._current_request_id[:16]}...")
            
            # 设置停止标志（如果 provider 支持）
            if hasattr(self._provider, 'tts_stop_request'):
                self._provider.tts_stop_request = True
                _log_debug("TTSAdapter", "设置 tts_stop_request = True")
            
            # 清空队列
            count = self.flush_queue()
            _log_info("TTSAdapter", f"清空队列完成，共清空 {count} 项")
            
            return True
        except Exception as e:
            _log_error("TTSAdapter", f"打断处理失败: {e}\n{traceback.format_exc()}")
            return False
    
    def get_current_request_id(self) -> Optional[str]:
        """获取当前请求 ID"""
        if hasattr(self._provider, 'sentence_id'):
            request_id = self._provider.sentence_id
            if request_id and self._debug:
                _log_debug("TTSAdapter", f"当前请求 ID: {request_id[:16]}...")
            return request_id
        return self._current_request_id
    
    def get_interrupt_target(self) -> InterruptTarget:
        """获取目标类型"""
        return InterruptTarget.TTS
    
    def flush_queue(self) -> int:
        """清空 TTS 队列"""
        count = 0
        text_count = 0
        audio_count = 0
        
        # 清空文本队列
        if hasattr(self._provider, 'tts_text_queue'):
            while True:
                try:
                    self._provider.tts_text_queue.get_nowait()
                    text_count += 1
                    count += 1
                except queue.Empty:
                    break
            _log_debug("TTSAdapter", f"清空文本队列: {text_count} 项")
        
        # 清空音频队列
        if hasattr(self._provider, 'tts_audio_queue'):
            while True:
                try:
                    self._provider.tts_audio_queue.get_nowait()
                    audio_count += 1
                    count += 1
                except queue.Empty:
                    break
            _log_debug("TTSAdapter", f"清空音频队列: {audio_count} 项")
        
        # 清空文本缓冲
        if hasattr(self._provider, 'tts_text_buff'):
            buff_size = len(self._provider.tts_text_buff)
            self._provider.tts_text_buff = []
            self._provider.processed_chars = 0
            _log_debug("TTSAdapter", f"清空文本缓冲: {buff_size} 项")
        
        return count
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        size = 0
        if hasattr(self._provider, 'tts_text_queue'):
            size += self._provider.tts_text_queue.qsize()
        if hasattr(self._provider, 'tts_audio_queue'):
            size += self._provider.tts_audio_queue.qsize()
        return size
    
    def set_current_request_id(self, request_id: str) -> None:
        """设置当前请求 ID"""
        self._current_request_id = request_id
        _log_debug("TTSAdapter", f"设置当前请求 ID: {request_id[:16]}...")
    
    def is_flushed(self, request_id: str) -> bool:
        """检查请求是否已被 flush"""
        is_flushed = request_id == self._flush_request_id
        if is_flushed:
            _log_debug("TTSAdapter", f"请求已被 flush: {request_id[:16]}...")
        return is_flushed


class LLMAdapter(Interruptible, TaskCancellable):
    """
    LLM 组件适配器
    
    将现有的 LLM 处理逻辑适配为 Interruptible 协议。
    """
    
    def __init__(
        self,
        abort_flag_getter: Callable[[], bool],
        abort_flag_setter: Callable[[bool], None],
        dialogue_getter: Optional[Callable[[], Any]] = None,
        debug: bool = False,
    ):
        """
        初始化 LLM 适配器
        
        Args:
            abort_flag_getter: 获取 abort 标志的函数
            abort_flag_setter: 设置 abort 标志的函数
            dialogue_getter: 获取对话对象的函数（可选）
            debug: 是否启用调试日志
        """
        self._get_abort = abort_flag_getter
        self._set_abort = abort_flag_setter
        self._get_dialogue = dialogue_getter
        self._current_request_id: Optional[str] = None
        self._active_task: Optional[asyncio.Task] = None
        self._debug = debug
        
        _log_info("LLMAdapter", "初始化完成")
    
    async def on_interrupt(self, flush_request: FlushRequest) -> bool:
        """处理打断请求"""
        _log_info("LLMAdapter", f"收到打断请求: flush_id={flush_request.flush_id[:16]}...")
        
        try:
            # 获取当前 abort 状态
            current_abort = self._get_abort()
            _log_debug("LLMAdapter", f"当前 abort 状态: {current_abort}")
            
            # 设置 abort 标志
            self._set_abort(True)
            _log_info("LLMAdapter", "设置 client_abort = True")
            
            # 取消活动任务
            if self._active_task and not self._active_task.done():
                task_name = self._active_task.get_name() if hasattr(self._active_task, 'get_name') else 'unknown'
                _log_info("LLMAdapter", f"取消活动任务: {task_name}")
                self._active_task.cancel()
                try:
                    await self._active_task
                except asyncio.CancelledError:
                    _log_debug("LLMAdapter", "任务已取消")
            else:
                _log_debug("LLMAdapter", "无活动任务需要取消")
            
            return True
        except Exception as e:
            _log_error("LLMAdapter", f"打断处理失败: {e}\n{traceback.format_exc()}")
            return False
    
    def get_current_request_id(self) -> Optional[str]:
        """获取当前请求 ID"""
        return self._current_request_id
    
    def get_interrupt_target(self) -> InterruptTarget:
        """获取目标类型"""
        return InterruptTarget.LLM
    
    async def cancel_current_task(self) -> bool:
        """取消当前任务"""
        if self._active_task and not self._active_task.done():
            _log_info("LLMAdapter", "取消当前任务")
            self._active_task.cancel()
            try:
                await self._active_task
            except asyncio.CancelledError:
                pass
            _log_debug("LLMAdapter", "任务取消完成")
            return True
        _log_debug("LLMAdapter", "无任务需要取消")
        return False
    
    def has_active_task(self) -> bool:
        """检查是否有活动任务"""
        has_task = self._active_task is not None and not self._active_task.done()
        if self._debug:
            _log_debug("LLMAdapter", f"has_active_task: {has_task}")
        return has_task
    
    def set_active_task(self, task: asyncio.Task) -> None:
        """设置活动任务"""
        self._active_task = task
        task_name = task.get_name() if hasattr(task, 'get_name') else 'unknown'
        _log_debug("LLMAdapter", f"设置活动任务: {task_name}")
    
    def set_current_request_id(self, request_id: str) -> None:
        """设置当前请求 ID"""
        self._current_request_id = request_id
        _log_debug("LLMAdapter", f"设置当前请求 ID: {request_id[:16]}...")


class ASRAdapter(Interruptible, QueueFlushable):
    """
    ASR 组件适配器
    
    将现有的 ASR Provider 适配为 Interruptible 协议。
    """
    
    def __init__(self, asr_provider: Any, audio_buffer_getter: Callable[[], Any]):
        """
        初始化 ASR 适配器
        
        Args:
            asr_provider: ASR Provider 实例
            audio_buffer_getter: 获取音频缓冲区的函数
        """
        self._provider = asr_provider
        self._get_buffer = audio_buffer_getter
        self._current_request_id: Optional[str] = None
    
    async def on_interrupt(self, flush_request: FlushRequest) -> bool:
        """处理打断请求"""
        try:
            # 清空音频缓冲
            buffer = self._get_buffer()
            if buffer is not None:
                if hasattr(buffer, 'clear'):
                    buffer.clear()
                elif isinstance(buffer, list):
                    buffer.clear()
            
            return True
        except Exception:
            return False
    
    def get_current_request_id(self) -> Optional[str]:
        """获取当前请求 ID"""
        return self._current_request_id
    
    def get_interrupt_target(self) -> InterruptTarget:
        """获取目标类型"""
        return InterruptTarget.ASR
    
    def flush_queue(self) -> int:
        """清空 ASR 相关队列"""
        count = 0
        buffer = self._get_buffer()
        if buffer is not None:
            if hasattr(buffer, '__len__'):
                count = len(buffer)
            if hasattr(buffer, 'clear'):
                buffer.clear()
        return count
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        buffer = self._get_buffer()
        if buffer is not None and hasattr(buffer, '__len__'):
            return len(buffer)
        return 0


class AudioOutputAdapter(Interruptible, QueueFlushable):
    """
    音频输出适配器
    
    用于控制音频播放/发送。
    """
    
    def __init__(
        self,
        speaking_flag_getter: Callable[[], bool],
        speaking_flag_setter: Callable[[bool], None],
        audio_controller: Optional[Any] = None,
        debug: bool = False,
    ):
        """
        初始化音频输出适配器
        
        Args:
            speaking_flag_getter: 获取说话状态的函数
            speaking_flag_setter: 设置说话状态的函数
            audio_controller: 音频流控制器（可选）
            debug: 是否启用调试日志
        """
        self._get_speaking = speaking_flag_getter
        self._set_speaking = speaking_flag_setter
        self._controller = audio_controller
        self._debug = debug
        
        controller_type = type(audio_controller).__name__ if audio_controller else "None"
        _log_info("AudioOutputAdapter", f"初始化: controller={controller_type}")
    
    async def on_interrupt(self, flush_request: FlushRequest) -> bool:
        """处理打断请求"""
        _log_info("AudioOutputAdapter", f"收到打断请求: flush_id={flush_request.flush_id[:16]}...")
        
        try:
            # 获取当前说话状态
            was_speaking = self._get_speaking()
            _log_debug("AudioOutputAdapter", f"当前说话状态: {was_speaking}")
            
            # 清除说话状态
            self._set_speaking(False)
            _log_info("AudioOutputAdapter", "设置 client_is_speaking = False")
            
            # 重置音频控制器
            if self._controller and hasattr(self._controller, 'reset'):
                _log_debug("AudioOutputAdapter", "重置音频控制器")
                self._controller.reset()
                _log_info("AudioOutputAdapter", "音频控制器已重置")
            
            return True
        except Exception as e:
            _log_error("AudioOutputAdapter", f"打断处理失败: {e}\n{traceback.format_exc()}")
            return False
    
    def get_current_request_id(self) -> Optional[str]:
        """获取当前请求 ID"""
        return None
    
    def get_interrupt_target(self) -> InterruptTarget:
        """获取目标类型"""
        return InterruptTarget.AUDIO_OUTPUT
    
    def flush_queue(self) -> int:
        """清空音频队列"""
        if self._controller and hasattr(self._controller, 'reset'):
            _log_debug("AudioOutputAdapter", "通过 reset 清空音频队列")
            self._controller.reset()
            return 1
        return 0
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return 0


class WebSocketNotifier(InterruptNotifier):
    """
    WebSocket 通知器
    
    通过 WebSocket 向客户端发送打断通知。
    兼容现有的 xiaozhi-server 消息格式。
    """
    
    def __init__(
        self,
        websocket_getter: Callable[[], Any],
        session_id_getter: Callable[[], str],
        debug: bool = False,
    ):
        """
        初始化 WebSocket 通知器
        
        Args:
            websocket_getter: 获取 WebSocket 连接的函数
            session_id_getter: 获取会话 ID 的函数
            debug: 是否启用调试日志
        """
        self._get_ws = websocket_getter
        self._get_session_id = session_id_getter
        self._debug = debug
        
        _log_info("WebSocketNotifier", "初始化完成")
    
    async def notify_interrupt(
        self,
        event: InterruptEvent,
        notification_type: str = "tts",
        state: str = "stop",
    ) -> bool:
        """发送打断通知"""
        _log_debug("WebSocketNotifier", f"发送通知: type={notification_type}, state={state}")
        
        try:
            ws = self._get_ws()
            if ws is None:
                _log_warning("WebSocketNotifier", "WebSocket 连接不存在，跳过通知")
                return False
            
            # 构建消息（兼容现有格式）
            session_id = self._get_session_id()
            message = {
                "type": notification_type,
                "state": state,
                "session_id": session_id,
            }
            
            # 添加额外信息
            if event.flush_request:
                message["flush_id"] = event.flush_request.flush_id
            
            message_json = json.dumps(message)
            _log_debug("WebSocketNotifier", f"发送消息: {message_json}")
            
            await ws.send(message_json)
            _log_info("WebSocketNotifier", f"通知发送成功: session_id={session_id[:8]}...")
            return True
            
        except Exception as e:
            _log_error("WebSocketNotifier", f"通知发送失败: {e}\n{traceback.format_exc()}")
            return False


class LoggingCallback(InterruptCallback):
    """
    日志回调
    
    记录打断事件到日志，便于调试和监控。
    """
    
    def __init__(self, logger: Any, tag: str = "InterruptCallback"):
        """
        初始化日志回调
        
        Args:
            logger: 日志记录器
            tag: 日志标签
        """
        self._logger = logger
        self._tag = tag
    
    async def on_interrupt_start(self, event: InterruptEvent) -> None:
        """打断开始时记录"""
        self._logger.bind(tag=self._tag).info(
            f"Interrupt started: source={event.source.value}, "
            f"targets={[t.value for t in event.targets]}, "
            f"flush_id={event.flush_request.flush_id if event.flush_request else None}"
        )
    
    async def on_interrupt_complete(self, event: InterruptEvent) -> None:
        """打断完成时记录"""
        self._logger.bind(tag=self._tag).info(
            f"Interrupt completed: success={event.success}, "
            f"interrupted_requests={len(event.interrupted_request_ids)}"
        )
    
    async def on_interrupt_error(self, event: InterruptEvent, error: Exception) -> None:
        """打断出错时记录"""
        self._logger.bind(tag=self._tag).error(
            f"Interrupt error: {error}, event={event.to_dict()}"
        )


class MetricsCallback(InterruptCallback):
    """
    指标回调
    
    收集打断相关的指标数据。
    """
    
    def __init__(self):
        self.total_interrupts = 0
        self.successful_interrupts = 0
        self.failed_interrupts = 0
        self.interrupts_by_source: Dict[str, int] = {}
        self.interrupts_by_target: Dict[str, int] = {}
        self.total_latency_ms = 0
    
    async def on_interrupt_start(self, event: InterruptEvent) -> None:
        """打断开始时记录"""
        pass
    
    async def on_interrupt_complete(self, event: InterruptEvent) -> None:
        """打断完成时记录"""
        self.total_interrupts += 1
        
        if event.success:
            self.successful_interrupts += 1
        else:
            self.failed_interrupts += 1
        
        # 按来源统计
        source_key = event.source.value
        self.interrupts_by_source[source_key] = \
            self.interrupts_by_source.get(source_key, 0) + 1
        
        # 按目标统计
        for target in event.targets:
            target_key = target.value
            self.interrupts_by_target[target_key] = \
                self.interrupts_by_target.get(target_key, 0) + 1
    
    async def on_interrupt_error(self, event: InterruptEvent, error: Exception) -> None:
        """打断出错时记录"""
        self.failed_interrupts += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        return {
            "total": self.total_interrupts,
            "successful": self.successful_interrupts,
            "failed": self.failed_interrupts,
            "by_source": self.interrupts_by_source,
            "by_target": self.interrupts_by_target,
        }


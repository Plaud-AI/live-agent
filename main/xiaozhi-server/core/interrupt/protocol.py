"""
打断模块的协议/接口定义

定义了可中断组件需要实现的接口，以及打断回调的协议。
使用 Protocol（结构化子类型）而非 ABC（名义子类型），
便于与现有代码集成，无需修改继承关系。
"""

from typing import Protocol, Callable, Awaitable, Optional, List, Any, runtime_checkable
from .types import (
    InterruptEvent,
    InterruptReason,
    InterruptTarget,
    FlushRequest,
    RequestContext,
)


@runtime_checkable
class Interruptible(Protocol):
    """
    可中断组件协议
    
    任何需要支持打断功能的组件都应该实现此协议。
    参考 ten-framework 的设计，每个组件需要：
    1. 响应 flush/cancel 请求
    2. 追踪当前请求状态
    3. 支持优雅取消
    
    使用示例:
        class MyTTSProvider:
            async def on_interrupt(self, flush_request: FlushRequest) -> bool:
                # 取消当前 TTS 请求
                self.cancel_current_request()
                return True
            
            def get_current_request_id(self) -> Optional[str]:
                return self._current_request_id
            
            def get_interrupt_target(self) -> InterruptTarget:
                return InterruptTarget.TTS
    """
    
    async def on_interrupt(self, flush_request: FlushRequest) -> bool:
        """
        处理打断请求
        
        Args:
            flush_request: 打断请求信息，包含 flush_id 和元数据
            
        Returns:
            bool: 打断是否成功
            
        注意:
            - 实现时应该尽快返回，避免阻塞
            - 如果有异步清理工作，可以启动后台任务
            - 返回 False 表示打断失败（如组件已停止）
        """
        ...
    
    def get_current_request_id(self) -> Optional[str]:
        """
        获取当前正在处理的请求 ID
        
        Returns:
            当前请求 ID，如果没有正在处理的请求则返回 None
        """
        ...
    
    def get_interrupt_target(self) -> InterruptTarget:
        """
        获取组件对应的打断目标类型
        
        Returns:
            InterruptTarget 枚举值
        """
        ...


@runtime_checkable
class InterruptibleWithState(Interruptible, Protocol):
    """
    带状态追踪的可中断组件协议（扩展）
    
    在基础 Interruptible 协议上增加状态追踪能力，
    用于需要精细控制的场景。
    """
    
    def get_request_context(self) -> Optional[RequestContext]:
        """
        获取当前请求的完整上下文
        
        Returns:
            RequestContext 或 None
        """
        ...
    
    def is_processing(self) -> bool:
        """
        检查是否正在处理请求
        
        Returns:
            bool: 是否有正在处理的请求
        """
        ...


# 回调类型定义
InterruptCallbackFunc = Callable[[InterruptEvent], Awaitable[None]]
InterruptCallbackSync = Callable[[InterruptEvent], None]


class InterruptCallback(Protocol):
    """
    打断回调协议
    
    用于在打断事件发生时通知外部组件。
    支持异步和同步两种回调方式。
    """
    
    async def on_interrupt_start(self, event: InterruptEvent) -> None:
        """
        打断开始时的回调
        
        Args:
            event: 打断事件信息
        """
        ...
    
    async def on_interrupt_complete(self, event: InterruptEvent) -> None:
        """
        打断完成时的回调
        
        Args:
            event: 打断事件信息（包含结果）
        """
        ...
    
    async def on_interrupt_error(self, event: InterruptEvent, error: Exception) -> None:
        """
        打断出错时的回调
        
        Args:
            event: 打断事件信息
            error: 错误信息
        """
        ...


class QueueFlushable(Protocol):
    """
    可清空队列的组件协议
    
    用于需要清空内部队列的组件（如 TTS 文本队列、音频队列）。
    """
    
    def flush_queue(self) -> int:
        """
        清空队列
        
        Returns:
            int: 被清空的项目数量
        """
        ...
    
    def get_queue_size(self) -> int:
        """
        获取队列当前大小
        
        Returns:
            int: 队列中的项目数量
        """
        ...


class TaskCancellable(Protocol):
    """
    可取消任务的组件协议
    
    用于需要取消异步任务的组件。
    """
    
    async def cancel_current_task(self) -> bool:
        """
        取消当前正在执行的任务
        
        Returns:
            bool: 取消是否成功
        """
        ...
    
    def has_active_task(self) -> bool:
        """
        检查是否有活动的任务
        
        Returns:
            bool: 是否有正在执行的任务
        """
        ...


class InterruptNotifier(Protocol):
    """
    打断通知器协议
    
    用于向客户端或其他系统发送打断通知。
    参考 xiaozhi-server 中的 WebSocket 通知机制。
    """
    
    async def notify_interrupt(
        self,
        event: InterruptEvent,
        notification_type: str = "tts",
        state: str = "stop",
    ) -> bool:
        """
        发送打断通知
        
        Args:
            event: 打断事件
            notification_type: 通知类型（如 "tts", "llm"）
            state: 状态（如 "stop", "interrupted"）
            
        Returns:
            bool: 通知是否成功发送
        """
        ...


class InterruptMetricsCollector(Protocol):
    """
    打断指标收集器协议
    
    用于收集打断相关的指标数据，便于监控和分析。
    """
    
    def record_interrupt(self, event: InterruptEvent) -> None:
        """
        记录打断事件
        
        Args:
            event: 打断事件
        """
        ...
    
    def get_interrupt_count(self, target: Optional[InterruptTarget] = None) -> int:
        """
        获取打断次数
        
        Args:
            target: 可选的目标过滤
            
        Returns:
            int: 打断次数
        """
        ...



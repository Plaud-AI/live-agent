"""
打断机制模块 (Interrupt Module)

参考 ten-framework 设计，提供独立、内聚的打断管理功能。
支持分层打断（ASR、LLM、TTS），易于迁移到其他项目。

核心组件：
- InterruptManager: 打断管理器，协调各组件的打断操作
- InterruptSource: 打断触发源枚举
- InterruptTarget: 打断目标枚举  
- InterruptEvent: 打断事件数据结构
- Interruptible: 可中断组件协议

使用示例:
    from core.interrupt import InterruptManager, InterruptSource, InterruptTarget
    
    # 创建管理器
    manager = InterruptManager(session_id="xxx")
    
    # 注册可中断组件
    manager.register_target(InterruptTarget.TTS, tts_component)
    manager.register_target(InterruptTarget.LLM, llm_component)
    
    # 触发打断
    await manager.interrupt(
        source=InterruptSource.VAD,
        targets=[InterruptTarget.TTS, InterruptTarget.LLM]
    )
"""

from .types import (
    InterruptSource,
    InterruptTarget,
    InterruptReason,
    InterruptState,
    InterruptEvent,
    FlushRequest,
    RequestContext,
)
from .protocol import (
    Interruptible,
    InterruptCallback,
    InterruptibleWithState,
    QueueFlushable,
    TaskCancellable,
    InterruptNotifier,
)
from .manager import InterruptManager
from .adapters import (
    TTSAdapter,
    LLMAdapter,
    ASRAdapter,
    AudioOutputAdapter,
    WebSocketNotifier,
    LoggingCallback,
    MetricsCallback,
)
from .utils import (
    setup_interrupt_logging,
    create_interrupt_manager_for_connection,
    format_interrupt_event,
    get_interrupt_stats,
)

__all__ = [
    # 枚举和类型
    "InterruptSource",
    "InterruptTarget", 
    "InterruptReason",
    "InterruptState",
    "InterruptEvent",
    "FlushRequest",
    "RequestContext",
    # 协议
    "Interruptible",
    "InterruptCallback",
    "InterruptibleWithState",
    "QueueFlushable",
    "TaskCancellable",
    "InterruptNotifier",
    # 管理器
    "InterruptManager",
    # 适配器
    "TTSAdapter",
    "LLMAdapter",
    "ASRAdapter",
    "AudioOutputAdapter",
    "WebSocketNotifier",
    "LoggingCallback",
    "MetricsCallback",
    # 工具函数
    "setup_interrupt_logging",
    "create_interrupt_manager_for_connection",
    "format_interrupt_event",
    "get_interrupt_stats",
]


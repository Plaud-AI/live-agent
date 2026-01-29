"""
打断模块工具函数

提供日志配置、调试辅助等工具函数。
"""

import logging
from typing import Optional, Any


def setup_interrupt_logging(
    logger: Optional[Any] = None,
    level: str = "INFO",
    debug: bool = False,
) -> None:
    """
    配置打断模块的日志
    
    Args:
        logger: 日志记录器（可选，如果不提供则使用标准 logging）
        level: 日志级别 ("DEBUG", "INFO", "WARNING", "ERROR")
        debug: 是否启用调试模式（等同于 level="DEBUG"）
    """
    if debug:
        level = "DEBUG"
    
    # 设置模块日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 配置打断模块的日志器
    interrupt_logger = logging.getLogger("core.interrupt")
    interrupt_logger.setLevel(log_level)
    
    # 如果没有处理器，添加一个默认的
    if not interrupt_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        interrupt_logger.addHandler(handler)
    
    interrupt_logger.info(f"打断模块日志已配置: level={level}, debug={debug}")


def create_interrupt_manager_for_connection(conn: Any, debug: bool = False):
    """
    为连接创建配置好的 InterruptManager
    
    这是一个便捷函数，自动创建管理器并注册所有适配器。
    
    Args:
        conn: ConnectionHandler 实例
        debug: 是否启用调试日志
        
    Returns:
        InterruptManager: 配置好的打断管理器
        
    使用示例:
        from core.interrupt.utils import create_interrupt_manager_for_connection
        
        class ConnectionHandler:
            def _initialize_components(self):
                # ... 其他初始化 ...
                self.interrupt_manager = create_interrupt_manager_for_connection(self, debug=True)
    """
    from .manager import InterruptManager
    from .types import InterruptTarget
    from .adapters import (
        TTSAdapter,
        LLMAdapter,
        AudioOutputAdapter,
        WebSocketNotifier,
        LoggingCallback,
    )
    
    # 获取会话 ID
    session_id = getattr(conn, 'session_id', '')
    
    # 获取日志记录器
    logger = getattr(conn, 'logger', None)
    
    # 创建管理器
    manager = InterruptManager(
        session_id=session_id,
        logger=logger,
        debug=debug,
    )
    
    # 注册 TTS 适配器
    tts = getattr(conn, 'tts', None)
    if tts:
        tts_adapter = TTSAdapter(tts, debug=debug)
        manager.register_target(
            InterruptTarget.TTS,
            tts_adapter,
            queue=tts_adapter,
        )
    
    # 注册 LLM 适配器
    llm_adapter = LLMAdapter(
        abort_flag_getter=lambda: getattr(conn, 'client_abort', False),
        abort_flag_setter=lambda v: setattr(conn, 'client_abort', v),
        debug=debug,
    )
    manager.register_target(
        InterruptTarget.LLM,
        llm_adapter,
        task=llm_adapter,
    )
    
    # 注册音频输出适配器
    audio_adapter = AudioOutputAdapter(
        speaking_flag_getter=lambda: getattr(conn, 'client_is_speaking', False),
        speaking_flag_setter=lambda v: setattr(conn, 'client_is_speaking', v),
        audio_controller=getattr(conn, 'audio_rate_controller', None),
        debug=debug,
    )
    manager.register_target(
        InterruptTarget.AUDIO_OUTPUT,
        audio_adapter,
        queue=audio_adapter,
    )
    
    # 设置 WebSocket 通知器
    websocket = getattr(conn, 'websocket', None)
    if websocket:
        notifier = WebSocketNotifier(
            websocket_getter=lambda: getattr(conn, 'websocket', None),
            session_id_getter=lambda: getattr(conn, 'session_id', ''),
            debug=debug,
        )
        manager.set_notifier(notifier)
    
    # 添加日志回调
    if logger:
        manager.add_callback(LoggingCallback(logger, tag="Interrupt"))
    
    return manager


def format_interrupt_event(event: Any) -> str:
    """
    格式化打断事件为可读字符串
    
    Args:
        event: InterruptEvent 实例
        
    Returns:
        str: 格式化的字符串
    """
    lines = [
        "=" * 50,
        "打断事件详情",
        "=" * 50,
        f"事件 ID: {event.event_id}",
        f"会话 ID: {event.session_id}",
        f"触发源: {event.source.value}",
        f"目标: {[t.value for t in event.targets]}",
        f"原因: {event.reason.name}",
        f"成功: {event.success}",
    ]
    
    if event.flush_request:
        lines.append(f"Flush ID: {event.flush_request.flush_id}")
    
    if event.interrupted_request_ids:
        lines.append(f"被打断请求: {event.interrupted_request_ids}")
    
    if event.error_message:
        lines.append(f"错误信息: {event.error_message}")
    
    lines.append(f"时间戳: {event.timestamp.isoformat()}")
    lines.append("=" * 50)
    
    return "\n".join(lines)


def get_interrupt_stats(manager: Any) -> dict:
    """
    获取打断统计信息
    
    Args:
        manager: InterruptManager 实例
        
    Returns:
        dict: 统计信息字典
    """
    from .types import InterruptTarget
    
    stats = {
        "total_interrupts": manager.get_interrupt_count(),
        "by_target": {},
        "registered_targets": [t.value for t in manager.get_registered_targets()],
        "is_interrupting": manager.is_interrupting,
        "is_closed": manager.is_closed,
    }
    
    for target in InterruptTarget:
        if target != InterruptTarget.ALL:
            count = manager.get_interrupt_count(target)
            if count > 0:
                stats["by_target"][target.value] = count
    
    return stats



"""
打断模块使用示例

提供完整的集成示例，展示如何在 xiaozhi-server 中使用打断模块。
"""

import asyncio
from typing import Optional, Any

# 示例 1: 基本使用
# ==================

async def example_basic_usage():
    """基本使用示例"""
    from core.interrupt import (
        InterruptManager,
        InterruptSource,
        InterruptTarget,
    )
    
    # 1. 创建管理器
    manager = InterruptManager(session_id="example_session")
    
    # 2. 触发打断
    event = await manager.interrupt(
        source=InterruptSource.VAD,
        targets=[InterruptTarget.TTS, InterruptTarget.LLM],
    )
    
    # 3. 检查结果
    print(f"打断成功: {event.success}")
    print(f"打断的请求: {event.interrupted_request_ids}")
    
    # 4. 清理
    await manager.cleanup()


# 示例 2: 与 ConnectionHandler 集成
# ==================================

class InterruptIntegrationMixin:
    """
    打断集成 Mixin
    
    可以混入到 ConnectionHandler 中，提供打断管理功能。
    """
    
    def init_interrupt_manager(self):
        """初始化打断管理器"""
        from core.interrupt import (
            InterruptManager,
            InterruptTarget,
            TTSAdapter,
            LLMAdapter,
            AudioOutputAdapter,
            WebSocketNotifier,
            LoggingCallback,
        )
        
        # 创建管理器
        self.interrupt_manager = InterruptManager(
            session_id=getattr(self, 'session_id', ''),
            logger=getattr(self, 'logger', None),
        )
        
        # 注册 TTS（如果存在）
        tts = getattr(self, 'tts', None)
        if tts:
            tts_adapter = TTSAdapter(tts)
            self.interrupt_manager.register_target(
                InterruptTarget.TTS,
                tts_adapter,
                queue=tts_adapter,
            )
        
        # 注册 LLM
        llm_adapter = LLMAdapter(
            abort_flag_getter=lambda: getattr(self, 'client_abort', False),
            abort_flag_setter=lambda v: setattr(self, 'client_abort', v),
        )
        self.interrupt_manager.register_target(
            InterruptTarget.LLM,
            llm_adapter,
            task=llm_adapter,
        )
        
        # 注册音频输出
        audio_adapter = AudioOutputAdapter(
            speaking_flag_getter=lambda: getattr(self, 'client_is_speaking', False),
            speaking_flag_setter=lambda v: setattr(self, 'client_is_speaking', v),
            audio_controller=getattr(self, 'audio_rate_controller', None),
        )
        self.interrupt_manager.register_target(
            InterruptTarget.AUDIO_OUTPUT,
            audio_adapter,
            queue=audio_adapter,
        )
        
        # 设置 WebSocket 通知
        ws = getattr(self, 'websocket', None)
        if ws:
            self.interrupt_manager.set_notifier(
                WebSocketNotifier(
                    websocket_getter=lambda: getattr(self, 'websocket', None),
                    session_id_getter=lambda: getattr(self, 'session_id', ''),
                )
            )
        
        # 添加日志回调
        logger = getattr(self, 'logger', None)
        if logger:
            self.interrupt_manager.add_callback(
                LoggingCallback(logger, tag="Interrupt")
            )
    
    async def do_interrupt(
        self,
        source: str = "vad",
        targets: Optional[list] = None,
    ):
        """
        执行打断操作
        
        Args:
            source: 打断来源 ("vad", "user", "system")
            targets: 打断目标列表 (None 表示全部)
        """
        from core.interrupt import InterruptSource, InterruptTarget
        
        if not hasattr(self, 'interrupt_manager') or not self.interrupt_manager:
            # 降级到原有逻辑
            self.client_abort = True
            if hasattr(self, 'clear_queues'):
                self.clear_queues()
            return
        
        # 映射来源
        source_map = {
            "vad": InterruptSource.VAD,
            "user": InterruptSource.USER_ACTION,
            "system": InterruptSource.SYSTEM,
            "api": InterruptSource.API,
        }
        interrupt_source = source_map.get(source, InterruptSource.UNKNOWN)
        
        # 映射目标
        target_list = None
        if targets:
            target_map = {
                "tts": InterruptTarget.TTS,
                "llm": InterruptTarget.LLM,
                "asr": InterruptTarget.ASR,
                "audio": InterruptTarget.AUDIO_OUTPUT,
            }
            target_list = [target_map[t] for t in targets if t in target_map]
        
        # 执行打断
        await self.interrupt_manager.interrupt(
            source=interrupt_source,
            targets=target_list,
        )
    
    async def cleanup_interrupt_manager(self):
        """清理打断管理器"""
        if hasattr(self, 'interrupt_manager') and self.interrupt_manager:
            await self.interrupt_manager.cleanup()


# 示例 3: 修改现有的 abortHandle.py
# ==================================

async def handleAbortMessage_v2(conn):
    """
    改进版的打断处理函数
    
    使用打断管理器替代直接操作。
    """
    from core.interrupt import InterruptSource
    
    TAG = "abortHandle"
    
    if hasattr(conn, 'logger'):
        conn.logger.bind(tag=TAG).info("Abort message received")
    
    # 使用打断管理器
    if hasattr(conn, 'interrupt_manager') and conn.interrupt_manager:
        await conn.interrupt_manager.interrupt_all(
            source=InterruptSource.USER_ACTION
        )
    else:
        # 降级到原来的逻辑
        conn.client_abort = True
        if hasattr(conn, 'clear_queues'):
            conn.clear_queues()
        
        # 通知客户端（优先使用通道）
        import json
        stop_msg = json.dumps({
            "type": "tts",
            "state": "stop",
            "session_id": getattr(conn, 'session_id', ''),
        })
        await conn.channel.send_text(stop_msg)
        
        if hasattr(conn, 'clearSpeakStatus'):
            conn.clearSpeakStatus()
    
    if hasattr(conn, 'logger'):
        conn.logger.bind(tag=TAG).info("Abort message received-end")


# 示例 4: 修改 VAD 打断逻辑
# ==========================

async def handle_vad_interrupt(conn, have_voice: bool):
    """
    VAD 打断处理
    
    当检测到用户说话且系统正在播放时触发打断。
    """
    from core.interrupt import InterruptSource
    
    # 检查是否需要打断
    if not have_voice:
        return False
    
    if not getattr(conn, 'client_is_speaking', False):
        return False
    
    if getattr(conn, 'client_listen_mode', 'auto') == 'manual':
        return False
    
    # 执行打断
    if hasattr(conn, 'interrupt_manager') and conn.interrupt_manager:
        await conn.interrupt_manager.interrupt_llm_and_tts(
            source=InterruptSource.VAD,
            metadata={"trigger": "user_speech_detected"},
        )
    else:
        await handleAbortMessage_v2(conn)
    
    return True


# 示例 5: 自定义打断回调
# ======================

class CustomInterruptCallback:
    """
    自定义打断回调示例
    
    可以用于：
    - 记录打断事件到数据库
    - 发送打断通知到外部系统
    - 更新 UI 状态
    """
    
    def __init__(self, conn):
        self.conn = conn
    
    async def on_interrupt_start(self, event):
        """打断开始"""
        # 可以在这里更新 UI 状态
        pass
    
    async def on_interrupt_complete(self, event):
        """打断完成"""
        # 记录打断事件
        if hasattr(self.conn, 'report_queue'):
            self.conn.report_queue.put((
                "interrupt",
                event.to_dict(),
                None,
                event.timestamp,
            ))
    
    async def on_interrupt_error(self, event, error):
        """打断出错"""
        if hasattr(self.conn, 'logger'):
            self.conn.logger.error(f"Interrupt error: {error}")


# 示例 6: 流式 TTS 中检查打断
# ===========================

async def stream_tts_with_interrupt_check(
    manager,  # InterruptManager
    request_id: str,
    text_generator,  # 文本生成器
    audio_sender,  # 音频发送函数
):
    """
    在流式 TTS 中检查打断
    
    参考 ten-framework 的设计，在发送每个音频块之前检查是否被打断。
    """
    from core.interrupt import InterruptTarget, InterruptReason
    
    # 追踪请求
    context = manager.track_request(
        request_id=request_id,
        target=InterruptTarget.TTS,
    )
    context.mark_processing()
    
    try:
        for text_chunk in text_generator:
            # 检查是否被打断
            if manager.is_flushed(request_id):
                context.mark_completed(InterruptReason.INTERRUPTED)
                return
            
            # 生成和发送音频
            audio_data = await generate_audio(text_chunk)
            
            # 再次检查（因为生成音频可能耗时）
            if manager.is_flushed(request_id):
                context.mark_completed(InterruptReason.INTERRUPTED)
                return
            
            await audio_sender(audio_data)
        
        # 正常完成
        context.mark_completed(InterruptReason.REQUEST_END)
        
    except Exception as e:
        context.mark_completed(InterruptReason.ERROR)
        raise


async def generate_audio(text: str) -> bytes:
    """模拟音频生成"""
    await asyncio.sleep(0.1)
    return b"audio_data"


# 示例 7: 使用上下文管理器
# ========================

async def example_with_context_manager():
    """使用上下文管理器进行打断"""
    from core.interrupt import InterruptManager, InterruptSource
    
    manager = InterruptManager(session_id="example")
    
    # 使用 interrupt_scope 上下文管理器
    async with manager.interrupt_scope(source=InterruptSource.VAD) as event:
        # 打断已完成，在这里处理新的输入
        print(f"打断完成: {event.success}")
        # ... 处理新输入 ...
    
    await manager.cleanup()


# 示例 8: WebRTC 适配
# ===================

class WebRTCInterruptNotifier:
    """
    WebRTC DataChannel 通知器示例
    
    用于 WebRTC 项目的打断通知。
    """
    
    def __init__(self, data_channel_getter):
        self._get_channel = data_channel_getter
    
    async def notify_interrupt(self, event, notification_type="tts", state="stop"):
        import json
        
        channel = self._get_channel()
        if channel is None:
            return False
        
        message = {
            "type": "interrupt",
            "notification_type": notification_type,
            "state": state,
            "flush_id": event.flush_request.flush_id if event.flush_request else None,
            "session_id": event.session_id,
        }
        
        try:
            # WebRTC DataChannel 发送
            channel.send(json.dumps(message))
            return True
        except Exception:
            return False


# 运行示例
if __name__ == "__main__":
    asyncio.run(example_basic_usage())



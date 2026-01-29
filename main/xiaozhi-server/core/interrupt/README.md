# 打断机制模块 (Interrupt Module)

参考 [ten-framework](https://github.com/TEN-framework/TEN-Agent) 设计的独立、内聚的打断管理模块。

## 设计目标

1. **独立内聚**：模块自包含，最小化外部依赖，便于迁移到其他项目
2. **分层打断**：支持独立打断 ASR、LLM、TTS 等组件
3. **可扩展**：通过协议和回调机制支持扩展
4. **线程安全**：支持多用户并发场景

## 核心概念

### 打断目标 (InterruptTarget)

```
ASR -> LLM -> TTS -> AUDIO_OUTPUT
```

打断时按照从下游到上游的顺序执行：先停止输出，再停止处理。

### 打断触发源 (InterruptSource)

- `VAD`: 语音活动检测（用户开始说话）
- `USER_ACTION`: 用户主动打断
- `SYSTEM`: 系统打断
- `API`: API 远程打断
- `SESSION_END`: 会话结束

### Flush 机制

参考 ten-framework 的 `tts_flush` 设计：

```python
FlushRequest(
    flush_id="unique-id",           # 唯一标识符
    target_request_id="request-1",  # 目标请求 ID
    metadata={...}                  # 元数据
)
```

## 快速开始

### 1. 创建管理器

```python
from core.interrupt import InterruptManager, InterruptSource, InterruptTarget

# 每个连接创建一个管理器
manager = InterruptManager(session_id="session_123")
```

### 2. 注册组件

使用适配器将现有组件接入打断系统：

```python
from core.interrupt import (
    TTSAdapter, 
    LLMAdapter, 
    AudioOutputAdapter,
    WebSocketNotifier,
)

# TTS 适配器
tts_adapter = TTSAdapter(tts_provider)
manager.register_target(InterruptTarget.TTS, tts_adapter, queue=tts_adapter)

# LLM 适配器
llm_adapter = LLMAdapter(
    abort_flag_getter=lambda: conn.client_abort,
    abort_flag_setter=lambda v: setattr(conn, 'client_abort', v),
)
manager.register_target(InterruptTarget.LLM, llm_adapter, task=llm_adapter)

# 音频输出适配器
audio_adapter = AudioOutputAdapter(
    speaking_flag_getter=lambda: conn.client_is_speaking,
    speaking_flag_setter=lambda v: setattr(conn, 'client_is_speaking', v),
)
manager.register_target(InterruptTarget.AUDIO_OUTPUT, audio_adapter)

# 设置通知器
notifier = WebSocketNotifier(
    websocket_getter=lambda: conn.websocket,
    session_id_getter=lambda: conn.session_id,
)
manager.set_notifier(notifier)
```

### 3. 触发打断

```python
# 打断所有组件
event = await manager.interrupt_all(source=InterruptSource.VAD)

# 只打断 TTS
event = await manager.interrupt_tts(source=InterruptSource.USER_ACTION)

# 打断 LLM 和 TTS（最常见场景）
event = await manager.interrupt_llm_and_tts(source=InterruptSource.VAD)

# 自定义打断
event = await manager.interrupt(
    source=InterruptSource.VAD,
    targets=[InterruptTarget.TTS, InterruptTarget.AUDIO_OUTPUT],
    metadata={"reason": "user_speaking"},
)
```

### 4. 添加回调

```python
from core.interrupt import LoggingCallback, MetricsCallback

# 日志回调
manager.add_callback(LoggingCallback(logger, tag="Interrupt"))

# 指标回调
metrics = MetricsCallback()
manager.add_callback(metrics)

# 自定义回调
async def my_callback(event: InterruptEvent):
    print(f"Interrupt: {event.source.value}")

manager.add_callback(my_callback)
```

### 5. 检查请求状态

```python
# 检查请求是否已被打断
if manager.is_flushed(request_id):
    return  # 跳过已打断的请求

# 追踪请求
context = manager.track_request(
    request_id="req_123",
    target=InterruptTarget.TTS,
)
context.mark_processing()
# ... 处理请求 ...
context.mark_completed()
```

### 6. 清理资源

```python
# 连接关闭时清理
await manager.cleanup()
```

## 与 xiaozhi-server 集成

### 在 ConnectionHandler 中初始化

```python
class ConnectionHandler:
    def __init__(self, ...):
        # ... 现有代码 ...
        
        # 初始化打断管理器
        self.interrupt_manager = None
    
    def _initialize_components(self):
        # ... 现有代码 ...
        
        # 初始化打断管理器
        from core.interrupt import (
            InterruptManager,
            TTSAdapter,
            LLMAdapter,
            AudioOutputAdapter,
            WebSocketNotifier,
            LoggingCallback,
        )
        
        self.interrupt_manager = InterruptManager(
            session_id=self.session_id,
            logger=self.logger,
        )
        
        # 注册 TTS
        if self.tts:
            tts_adapter = TTSAdapter(self.tts)
            self.interrupt_manager.register_target(
                InterruptTarget.TTS, 
                tts_adapter, 
                queue=tts_adapter,
            )
        
        # 注册 LLM
        llm_adapter = LLMAdapter(
            abort_flag_getter=lambda: self.client_abort,
            abort_flag_setter=lambda v: setattr(self, 'client_abort', v),
        )
        self.interrupt_manager.register_target(
            InterruptTarget.LLM, 
            llm_adapter, 
            task=llm_adapter,
        )
        
        # 注册音频输出
        audio_adapter = AudioOutputAdapter(
            speaking_flag_getter=lambda: self.client_is_speaking,
            speaking_flag_setter=lambda v: setattr(self, 'client_is_speaking', v),
            audio_controller=getattr(self, 'audio_rate_controller', None),
        )
        self.interrupt_manager.register_target(
            InterruptTarget.AUDIO_OUTPUT, 
            audio_adapter, 
            queue=audio_adapter,
        )
        
        # 设置通知器
        self.interrupt_manager.set_notifier(
            WebSocketNotifier(
                websocket_getter=lambda: self.websocket,
                session_id_getter=lambda: self.session_id,
            )
        )
        
        # 添加日志回调
        self.interrupt_manager.add_callback(
            LoggingCallback(self.logger, tag="Interrupt")
        )
```

### 修改打断处理

```python
# 原来的 abortHandle.py
async def handleAbortMessage(conn):
    # 使用打断管理器
    if conn.interrupt_manager:
        await conn.interrupt_manager.interrupt_all(
            source=InterruptSource.USER_ACTION
        )
    else:
        # 降级到原来的逻辑
        conn.client_abort = True
        conn.clear_queues()
        await conn.websocket.send(...)
        conn.clearSpeakStatus()
```

### 修改 VAD 打断

```python
# 在 receiveAudioHandle.py 中
async def handleAudioMessage(conn, audio):
    have_voice = conn.vad.is_vad(conn, audio)
    
    if have_voice:
        if conn.client_is_speaking and conn.client_listen_mode != "manual":
            # 使用打断管理器
            if conn.interrupt_manager:
                await conn.interrupt_manager.interrupt_llm_and_tts(
                    source=InterruptSource.VAD
                )
            else:
                await handleAbortMessage(conn)
    # ...
```

## 自定义组件

### 实现 Interruptible 协议

```python
from core.interrupt import Interruptible, InterruptTarget, FlushRequest

class MyCustomComponent(Interruptible):
    async def on_interrupt(self, flush_request: FlushRequest) -> bool:
        """处理打断请求"""
        # 1. 停止当前操作
        # 2. 清理资源
        # 3. 返回是否成功
        return True
    
    def get_current_request_id(self) -> Optional[str]:
        """返回当前请求 ID"""
        return self._current_request_id
    
    def get_interrupt_target(self) -> InterruptTarget:
        """返回组件类型"""
        return InterruptTarget.TTS  # 或其他类型
```

### 实现 QueueFlushable 协议

```python
from core.interrupt import QueueFlushable

class MyQueueComponent(QueueFlushable):
    def flush_queue(self) -> int:
        """清空队列，返回清空的数量"""
        count = len(self._queue)
        self._queue.clear()
        return count
    
    def get_queue_size(self) -> int:
        """返回队列大小"""
        return len(self._queue)
```

## 迁移到其他项目

### 最小依赖

打断模块仅依赖 Python 标准库：
- `asyncio`
- `threading`
- `logging`
- `dataclasses`
- `typing`
- `enum`
- `uuid`
- `datetime`

### 迁移步骤

1. 复制 `core/interrupt/` 目录到目标项目
2. 根据目标项目的组件实现适配器
3. 在连接/会话初始化时创建 `InterruptManager`
4. 注册组件并设置通知器
5. 在需要打断的地方调用 `manager.interrupt()`

### WebRTC 项目适配

对于 WebRTC 项目，主要需要修改：

1. **通知器**：将 WebSocket 通知改为 WebRTC DataChannel
2. **音频输出**：适配 WebRTC 的音频发送机制

```python
class WebRTCNotifier(InterruptNotifier):
    def __init__(self, data_channel_getter):
        self._get_channel = data_channel_getter
    
    async def notify_interrupt(self, event, ...):
        channel = self._get_channel()
        if channel:
            channel.send(json.dumps({
                "type": "interrupt",
                "flush_id": event.flush_request.flush_id,
            }))
```

## API 参考

### InterruptManager

| 方法 | 描述 |
|------|------|
| `register_target(target, component, queue, task)` | 注册可中断组件 |
| `unregister_target(target)` | 注销组件 |
| `set_notifier(notifier)` | 设置通知器 |
| `add_callback(callback)` | 添加回调 |
| `interrupt(source, targets, metadata)` | 触发打断 |
| `interrupt_all(source)` | 打断所有组件 |
| `interrupt_tts(source)` | 只打断 TTS |
| `interrupt_llm_and_tts(source)` | 打断 LLM 和 TTS |
| `is_flushed(request_id)` | 检查请求是否被打断 |
| `track_request(request_id, target)` | 追踪请求 |
| `cleanup()` | 清理资源 |

### InterruptEvent

| 字段 | 类型 | 描述 |
|------|------|------|
| `event_id` | str | 事件 ID |
| `session_id` | str | 会话 ID |
| `source` | InterruptSource | 触发源 |
| `targets` | List[InterruptTarget] | 目标列表 |
| `flush_request` | FlushRequest | Flush 请求 |
| `interrupted_request_ids` | List[str] | 被打断的请求 |
| `success` | bool | 是否成功 |
| `error_message` | str | 错误信息 |

## 设计参考

- [TEN Framework - AI Agents](https://github.com/TEN-framework/TEN-Agent)
- [ten_ai_base/tts2.py](https://github.com/TEN-framework/TEN-Agent/blob/main/agents/ten_packages/extension/ten_ai_base/tts2.py)
- [voice-assistant extension](https://github.com/TEN-framework/TEN-Agent/tree/main/agents/examples/voice-assistant)



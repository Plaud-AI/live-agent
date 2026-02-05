# MiniMax TTS 音频数据丢失问题分析

## 问题现象

客户端 APP 在语音通话过程中，界面卡在 "thinking" 状态，无法继续对话。服务端正常接收 TTS 音频数据，但客户端没有收到任何 opus 音频二进制数据。

## 直接原因

### 1. 问题触发场景

当 LLM 返回**长文本**时，文本会被分割成多个文本段（MIDDLE 消息），每个文本段都会调用 MiniMax TTS 服务：

```python
# 每个 MIDDLE 文本段
self.ws_client.get(text, is_end=False)  # 中间任务，is_end=False
```

### 2. PCM 缓冲区编码机制

MiniMax TTS 返回的音频数据是 PCM 格式，需要按帧编码为 Opus：

```python
# 计算每帧字节数（16-bit, 16kHz, 单声道, 60ms 帧）
frame_bytes = sample_rate * channels * 60 / 1000 * 2
# = 16000 * 1 * 60 / 1000 * 2 = 1920 bytes
```

编码逻辑：
- 只有当 `pcm_buffer` 长度 >= `frame_bytes` 时，才会编码并发送
- 不足一帧的数据会累积在 `pcm_buffer` 中等待

### 3. 关键 Bug

**修复前的代码逻辑**：

```python
if response.get("is_final", False):
    # 只有当 is_end=True 时，才触发 SENTENCE_END 事件
    if is_end and self.on_audio_data and self.callbacks_enabled:
        self.on_audio_data(b"", EVENT_TTS_SENTENCE_END)
    break
```

**问题**：
- 当中间任务（`is_end=False`）收到 `is_final` 时，**不会**触发 `SENTENCE_END` 事件
- `pcm_buffer` 中不足一帧的剩余数据（< 1920 bytes）不会被编码和发送
- 这些数据会一直累积在缓冲区中，直到下一个任务或会话结束

### 4. 数据丢失流程

```
1. LLM 返回长文本 → 分割成多个 MIDDLE 消息
2. 每个 MIDDLE 消息调用 TTS (is_end=False)
3. TTS 返回音频块（每个 2048 bytes）
4. PCM 数据累积到 pcm_buffer
5. 当 pcm_buffer >= 1920 bytes 时，编码并发送
6. 最后一个音频块可能不足一帧（例如剩余 500 bytes）
7. 收到 is_final，但 is_end=False
8. ❌ 不触发 SENTENCE_END，剩余 500 bytes 留在 pcm_buffer
9. 客户端没有收到这 500 bytes 的音频数据
10. 如果后续没有更多音频数据，这 500 bytes 就永远丢失了
```

## 复现方法

### 条件

1. **LLM 返回长文本**：确保文本会被分割成多个 MIDDLE 消息
2. **最后一个音频块不足一帧**：最后一个音频块的 PCM 数据 < `frame_bytes` (1920 bytes)
3. **中间任务完成**：`is_end=False` 的任务收到 `is_final`

### 复现步骤

1. 启动语音通话
2. 发送一个会触发 LLM 返回**长文本**的问题（例如："请详细介绍一下你自己"）
3. 观察日志，应该能看到：
   - 多个 `MiniMax TTS: 收到 is_final` 日志（`is_end=False`）
   - 没有 `MiniMax TTS Provider: 收到 SENTENCE_END` 日志
   - 没有 `WebSocket发送Opus包` 日志（在问题时间段）
4. 客户端会卡在 "thinking" 状态，没有音频输出

### 验证方法

查看服务端日志，搜索以下关键信息：

```bash
# 检查是否有 is_final 但 is_end=False 的情况
grep "收到 is_final" logs | grep -v "SENTENCE_END"

# 检查 PCM 缓冲区状态
grep "PCM缓冲区累积中" logs

# 检查是否有音频发送
grep "WebSocket发送Opus包" logs
```

## 修复方案

### 修复后的代码

```python
if response.get("is_final", False):
    # 无论 is_end 是否为 True，都需要 flush 剩余的 PCM 数据
    if self.on_audio_data and self.callbacks_enabled:
        if is_end:
            # 最后一个任务，发送 SENTENCE_END 事件
            self.on_audio_data(b"", EVENT_TTS_SENTENCE_END)
        else:
            # 中间任务，发送 FLUSH 事件处理剩余数据
            self.on_audio_data(b"", EVENT_TTS_FLUSH)
    break
```

### FLUSH 事件处理

```python
elif event_type == EVENT_TTS_FLUSH:
    # 处理剩余数据（中间任务完成时 flush 剩余 PCM 数据）
    if self.pcm_buffer:
        self.opus_encoder.encode_pcm_to_opus_stream(
            bytes(self.pcm_buffer),
            end_of_stream=False,  # 中间任务，不是流结束
            callback=self.handle_opus,
        )
        self.pcm_buffer.clear()
```

## 影响范围

- **影响场景**：所有使用 MiniMax TTS WebSocket 的语音通话
- **触发频率**：当 LLM 返回长文本且最后一个音频块不足一帧时
- **严重程度**：高 - 导致客户端完全卡住，无法继续对话

## 预防措施

1. **添加详细日志**：追踪 PCM 缓冲区状态和编码过程
2. **监控指标**：监控音频发送成功率
3. **测试覆盖**：添加长文本 TTS 测试用例


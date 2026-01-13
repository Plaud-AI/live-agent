# 移动端接入指南

## 问题描述

移动客户端连接服务器后，无法进行语音对话。日志显示：

```
wait_agent_ready timeout after 5.0s
Agent 初始化失败，无法开始对话
```

**根本原因**：移动端直接发送音频数据，但没有按照协议发送必要的初始化消息，导致 Agent 无法初始化。

---

## 正确的连接流程

### 流程图

```
┌──────────────┐                              ┌──────────────┐
│   移动端      │                              │    服务器     │
└──────┬───────┘                              └──────┬───────┘
       │                                              │
       │  1. WebSocket 连接                           │
       │  ws://server/xiaozhi/v1/?device-id=xxx       │
       │─────────────────────────────────────────────>│
       │                                              │
       │  2. 发送 hello 消息                          │
       │  {"type": "hello", "audio_params": {...}}    │
       │─────────────────────────────────────────────>│
       │                                              │
       │  3. 服务器返回 hello 响应                     │
       │  {"type": "hello", "session_id": "xxx", ...} │
       │<─────────────────────────────────────────────│
       │                                              │
       │  4. 发送唤醒词/listen 消息（触发 Agent 初始化）│
       │  {"type": "listen", "mode": "auto", ...}     │
       │─────────────────────────────────────────────>│
       │                                              │
       │  5. 服务器返回唤醒回复（Agent 已就绪）        │
       │  tts/start + audio + tts/stop                │
       │<─────────────────────────────────────────────│
       │                                              │
       │  6. 现在可以发送音频数据了                    │
       │  [opus/pcm binary data]                      │
       │─────────────────────────────────────────────>│
       │                                              │
       │  7. 服务器返回语音回复                        │
       │  stt/start + tts/start + audio + tts/stop    │
       │<─────────────────────────────────────────────│
       │                                              │
```

---

## 消息格式详解

### 1. WebSocket 连接

**URL 格式**：
```
wss://<server-host>/xiaozhi/v1/?device-id=<device_id>&authorization=<token>&timezone=<timezone>
```

**必需参数**：
| 参数 | 说明 | 示例 |
|------|------|------|
| `device-id` | 设备唯一标识 | `mobile_001` 或 MAC 地址格式 `AA:BB:CC:DD:EE:FF` |

**可选参数**：
| 参数 | 说明 | 示例 |
|------|------|------|
| `authorization` | JWT Token（用于用户身份识别） | `Bearer eyJhbG...` |
| `agent-id` | 指定 Agent ID（跳过唤醒词流程） | `agent_xxx` |
| `timezone` | 时区 | `Asia/Shanghai` 或 `UTC+8` |

---

### 2. Hello 消息（必需）

连接建立后，**必须首先发送 hello 消息**。

**请求**：
```json
{
  "type": "hello",
  "audio_params": {
    "format": "opus"
  },
  "features": {
    "mcp": false
  }
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值 `"hello"` |
| `audio_params.format` | string | ✅ | 音频格式：`"opus"` 或 `"pcm"` |
| `features.mcp` | boolean | ❌ | 是否支持 MCP 协议，默认 `false` |

**响应**：
```json
{
  "type": "hello",
  "session_id": "abc123-def456-...",
  "transport": "websocket",
  "audio_params": {
    "format": "opus",
    "sample_rate": 16000,
    "channels": 1,
    "frame_duration": 60
  }
}
```

---

### 3. Listen 消息（触发 Agent 初始化）

有两种方式触发 Agent 初始化：

#### 方式 A：发送唤醒词（推荐）

```json
{
  "type": "listen",
  "mode": "auto",
  "state": "detect",
  "text": "小智小智"
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值 `"listen"` |
| `mode` | string | ✅ | 监听模式：`"auto"` 或 `"manual"` |
| `state` | string | ✅ | **状态字段（必需！）**：`"detect"` 表示检测到文本 |
| `text` | string | ✅ | 唤醒词文本，如 `"小智小智"` |

> ⚠️ **重要**：`state` 字段是必需的！缺少此字段会导致服务器报错 `KeyError: 'state'`

**state 字段可选值**：
| 值 | 说明 |
|------|------|
| `"detect"` | 检测到文本（配合 `text` 字段发送唤醒词或用户输入） |
| `"start"` | 开始录音（用于手动模式） |
| `"stop"` | 停止录音（用于手动模式） |

服务器收到唤醒词后会：
1. 初始化 Agent（加载配置、语音音色等）
2. 返回唤醒回复音频
3. 此后可以正常进行语音对话

#### 方式 B：在连接 URL 中提供 agent-id

如果在连接时提供了 `agent-id` 参数，服务器会自动初始化 Agent，无需发送唤醒词。

```
wss://server/xiaozhi/v1/?device-id=xxx&agent-id=your_agent_id
```

此时可以直接发送 hello 消息后开始语音对话。

---

### 4. 发送音频数据

**格式**：WebSocket 二进制消息

**Opus 格式要求**：
- 采样率：16000 Hz
- 声道：单声道
- 帧长：60ms（960 samples）

**PCM 格式要求**：
- 采样率：16000 Hz
- 位深：16-bit
- 声道：单声道

---

### 5. 接收服务器消息

#### TTS 控制消息

```json
{"type": "tts", "state": "start"}      // 开始播放语音
{"type": "tts", "state": "stop"}       // 停止播放语音
{"type": "tts", "state": "sentence_start", "text": "你好"}  // 句子开始
{"type": "tts", "state": "sentence_end"}    // 句子结束
```

#### STT 消息

```json
{"type": "stt", "text": "用户说的话"}   // 语音识别结果
```

#### 音频数据

接收到的二进制数据为服务器返回的语音音频（格式与 hello 消息中协商的一致）。

---

## 完整代码示例（伪代码）

```javascript
// 1. 建立 WebSocket 连接
const ws = new WebSocket('wss://server/xiaozhi/v1/?device-id=mobile_001');

ws.onopen = function() {
  // 2. 发送 hello 消息（必需！）
  ws.send(JSON.stringify({
    type: 'hello',
    audio_params: { format: 'opus' }
  }));
};

ws.onmessage = function(event) {
  if (typeof event.data === 'string') {
    const msg = JSON.parse(event.data);
    
    if (msg.type === 'hello') {
      // 3. 收到 hello 响应，发送唤醒词初始化 Agent
      ws.send(JSON.stringify({
        type: 'listen',
        mode: 'auto',
        state: 'detect',  // ⚠️ 必需字段！
        text: '小智小智'
      }));
    }
    
    if (msg.type === 'tts' && msg.state === 'stop') {
      // 4. 唤醒回复播放完毕，现在可以开始发送音频了
      startRecordingAndSendAudio();
    }
    
    if (msg.type === 'stt') {
      console.log('识别结果:', msg.text);
    }
  } else {
    // 二进制数据 = 服务器返回的语音
    playAudio(event.data);
  }
};

function startRecordingAndSendAudio() {
  // 开始录音，将 opus 编码后的音频数据发送到 WebSocket
  recorder.ondata = function(opusData) {
    ws.send(opusData);  // 发送二进制音频数据
  };
  recorder.start();
}
```

---

## 常见错误排查

### 错误 1：`KeyError: 'state'`

**日志示例**：
```
异常=KeyError: 'state'
File "listenMessageHandler.py", line 77, in handle
    if msg_json["state"] == "start":
```

**原因**：listen 消息缺少 `state` 字段。

**错误的消息格式**：
```json
{"type": "listen", "mode": "auto", "text": "小智小智"}
```

**正确的消息格式**：
```json
{"type": "listen", "mode": "auto", "state": "detect", "text": "小智小智"}
```

**解决**：在 listen 消息中添加 `"state": "detect"` 字段。

---

### 错误 2：`wait_agent_ready timeout after 5.0s`

**原因**：没有发送唤醒词或 listen 消息，Agent 未初始化。

**解决**：
1. 确保在发送音频前发送了正确格式的 listen 消息：
   ```json
   {"type": "listen", "mode": "auto", "state": "detect", "text": "小智小智"}
   ```
2. 或在连接 URL 中添加 `agent-id` 参数

---

### 错误 3：收不到服务器语音回复

**原因**：可能没有发送 hello 消息，导致音频格式不匹配。

**解决**：确保连接后第一个消息是 hello 消息。

---

### 错误 4：连接被拒绝 `缺少device-id`

**原因**：WebSocket URL 中没有 `device-id` 参数。

**解决**：确保 URL 中包含 `device-id` 参数。

---

## 检查清单

在集成测试时，请确认以下步骤：

- [ ] WebSocket URL 包含 `device-id` 参数
- [ ] 连接成功后立即发送 `hello` 消息
- [ ] 收到 `hello` 响应后发送 `listen` 消息
- [ ] ⚠️ **listen 消息必须包含 `state` 字段**（值为 `"detect"`）
- [ ] listen 消息格式：`{"type": "listen", "mode": "auto", "state": "detect", "text": "唤醒词"}`
- [ ] 等待服务器返回 `tts/stop` 后再开始发送音频
- [ ] 音频格式与 `hello` 消息中声明的一致（opus 或 pcm）
- [ ] Opus 编码参数正确：16kHz, 单声道, 60ms 帧长

---

## 联系方式

如有问题，请联系后端开发团队。


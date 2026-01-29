# 小智协议测试页面 - Agora RTC 集成设计文档

## 1. 概述

### 1.1 目标

在现有的小智协议测试页面（`test_page.html`）中增加 Agora RTC 连接模式，使其能够：

1. **保持 WebSocket 模式**：继续支持直连 xiaozhi-server 的测试
2. **新增 Agora RTC 模式**：支持连接基于 TEN Framework 的远端 RTC 服务
3. **协议验证**：验证两种模式下小智协议实现的正确性

### 1.2 范围

- 前端测试页面改造（纯 HTML/JS，无框架依赖）
- 不涉及后端服务改动
- 参考实现：`/Users/shuo/workspace/plaud-agent-platform/ai_agents/agents/examples/xiaozhi-voice-assistant/frontend`

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        test_page.html                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  ConnectionManager (抽象层)               │    │
│  │  - connect(config)                                       │    │
│  │  - disconnect()                                          │    │
│  │  - sendText(text)                                        │    │
│  │  - sendAudio(data)  [仅 WebSocket]                       │    │
│  │  - onMessage(callback)                                   │    │
│  │  - isConnected()                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│            ┌─────────────┴─────────────┐                        │
│            ▼                           ▼                        │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │  WebSocketManager   │    │   AgoraRtcManager   │            │
│  │  (现有逻辑重构)      │    │   (新增实现)         │            │
│  ├─────────────────────┤    ├─────────────────────┤            │
│  │  - OTA 获取 WS URL  │    │  - API 获取 Token   │            │
│  │  - WebSocket 连接   │    │  - RTC 频道连接     │            │
│  │  - Opus 编解码      │    │  - 音频轨道管理     │            │
│  │  - 二进制音频传输   │    │  - Data Channel     │            │
│  │  - JSON 消息        │    │  - 分块消息传输     │            │
│  └─────────────────────┘    └─────────────────────┘            │
│            │                           │                        │
│            ▼                           ▼                        │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │   xiaozhi-server    │    │  TEN Framework RTC  │            │
│  │   (本地/远端)        │    │  (远端服务)          │            │
│  └─────────────────────┘    └─────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 文件结构

```
test/
├── test_page.html              # 主页面 (修改)
├── test_page.css               # 样式 (修改，新增 RTC 配置区域样式)
├── js/
│   ├── ConnectionManager.js    # [新增] 抽象连接管理器
│   ├── WebSocketManager.js     # [新增] WebSocket 实现 (从现有代码重构)
│   ├── AgoraRtcManager.js      # [新增] Agora RTC 实现
│   ├── ProtocolLogger.js       # [新增] 协议日志工具
│   ├── xiaoZhiConnect.js       # 保留：OTA 逻辑
│   ├── StreamingContext.js     # 保留：WebSocket 音频播放
│   ├── opus.js                 # 保留：Opus 编解码
│   ├── document.js             # 保留：DOM 操作
│   └── utils/
│       ├── BlockingQueue.js    # 保留
│       └── logger.js           # 保留
├── libopus.js                  # 保留：Opus 库
└── docs/
    └── agora-rtc-integration.md  # 本文档
```

---

## 3. 连接模式详细设计

### 3.1 WebSocket 模式（保持现有逻辑）

#### 连接流程

```
1. 用户输入 OTA URL
2. POST OTA 请求，获取 WebSocket URL + Token
3. 建立 WebSocket 连接
4. 发送 hello 握手消息
5. 等待 hello 响应
6. 连接就绪
```

#### 消息格式

| 方向 | 格式 |
|------|------|
| 发送文本消息 | `{"type":"listen","state":"detect","text":"..."}` |
| 发送语音开始 | `{"type":"listen","mode":"auto","state":"start"}` |
| 发送音频数据 | 二进制 Opus 帧 |
| 发送语音结束 | `{"type":"listen","mode":"auto","state":"stop"}` |
| 接收 TTS 状态 | `{"type":"tts","state":"start/sentence_start/..."}` |
| 接收音频数据 | 16 字节头部 + Opus 数据 |

### 3.2 Agora RTC 模式（新增）

#### 连接流程

```
1. 用户输入远端服务地址
2. 生成 Channel Name 和 User ID
3. POST /api/token/generate 获取 Agora Token
4. AgoraRTC.createClient() 创建客户端
5. client.join() 加入频道
6. POST /api/agents/start 启动远端 Agent
7. 创建并发布麦克风音频轨道
8. 监听远端音频轨道并播放
9. 发送 hello 消息（via Data Channel）
10. 连接就绪
```

#### 消息格式

**发送消息（分块传输）：**
```
原始消息: {"type":"listen","state":"detect","text":"你好"}
    ↓
Base64 编码: eyJ0eXBlIjoibGlzdGVuIiwic3RhdGUiOiJkZXRlY3QiLCJ0ZXh0Ijoi5L2g5aW9In0=
    ↓
分块格式: {msg_id}|{part_index}|{total_parts}|{base64_content}
    ↓
示例: abc123|1|1|eyJ0eXBlIjoibGlzdGVuIiwic3RhdGUiOiJkZXRlY3QiLCJ0ZXh0Ijoi5L2g5aW9In0=
```

**接收消息（分块重组）：**
```
接收分块: abc456|1|2|eyJ0eXBlIjoidHRzIiwic3R...
接收分块: abc456|2|2|hdGUiOiJzdGFydCIsInNh...
    ↓
重组 Base64: eyJ0eXBlIjoidHRzIiwic3RhdGUiOiJzdGFydCIsInNh...
    ↓
解码: {"type":"tts","state":"start","sample_rate":24000}
```

---

## 4. 核心模块设计

### 4.1 ConnectionManager.js

```javascript
/**
 * 连接管理器抽象接口
 */
class ConnectionManager {
    /**
     * 连接到服务器
     * @param {Object} config - 连接配置
     * @returns {Promise<boolean>} - 连接是否成功
     */
    async connect(config) {}

    /**
     * 断开连接
     */
    async disconnect() {}

    /**
     * 发送文本消息 (listen.detect)
     * @param {string} text - 文本内容
     */
    async sendText(text) {}

    /**
     * 发送 hello 消息
     * @param {Object} helloData - hello 消息数据
     */
    async sendHello(helloData) {}

    /**
     * 发送 abort 消息
     */
    async sendAbort() {}

    /**
     * 发送 MCP 响应
     * @param {Object} payload - MCP 响应数据
     */
    async sendMcpResponse(payload) {}

    /**
     * 注册消息回调
     * @param {string} type - 消息类型 ('hello'|'tts'|'stt'|'llm'|'mcp')
     * @param {Function} callback - 回调函数
     */
    onMessage(type, callback) {}

    /**
     * 获取连接状态
     * @returns {boolean}
     */
    isConnected() {}

    /**
     * 获取连接模式
     * @returns {string} - 'websocket' | 'agora-rtc'
     */
    getMode() {}
}
```

### 4.2 WebSocketManager.js

从现有 `test_page.html` 中提取 WebSocket 相关逻辑，实现 `ConnectionManager` 接口。

**关键功能：**
- OTA 请求获取 WebSocket URL
- WebSocket 连接管理
- Opus 编码器初始化
- PCM 录音 + Opus 编码 + 发送
- Opus 接收 + 解码 + 播放

### 4.3 AgoraRtcManager.js

参考 `rtc.ts` 实现，提供 Agora RTC 功能。

```javascript
/**
 * Agora RTC 连接管理器
 */
class AgoraRtcManager extends ConnectionManager {
    constructor() {
        super();
        this._client = null;           // IAgoraRTCClient
        this._localAudioTrack = null;  // IMicrophoneAudioTrack
        this._remoteAudioTrack = null; // IRemoteAudioTrack
        this._joined = false;
        this._messageCache = {};       // 分块消息缓存
        this._callbacks = {};          // 消息回调
    }

    // === 连接管理 ===
    async connect(config) {
        // 1. 获取 Agora Token
        const tokenData = await this._fetchToken(config);
        
        // 2. 创建 RTC Client
        this._client = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' });
        this._setupEventListeners();
        
        // 3. 加入频道
        await this._client.join(tokenData.appId, config.channel, tokenData.token, config.userId);
        
        // 4. 启动远端 Agent
        await this._startAgent(config);
        
        // 5. 创建并发布音频轨道
        await this._setupAudioTrack();
        
        this._joined = true;
        return true;
    }

    // === 消息发送 ===
    async sendText(text) {
        const payload = JSON.stringify({
            type: 'listen',
            state: 'detect',
            text: text
        });
        await this._sendStreamMessage(payload);
    }

    // === 分块传输 ===
    _chunkPayload(payloadUtf8) {
        const base64 = this._utf8ToBase64(payloadUtf8);
        const messageId = this._genMessageId();
        const maxPartLen = 800;
        const totalParts = Math.ceil(base64.length / maxPartLen) || 1;
        
        const chunks = [];
        for (let i = 0; i < totalParts; i++) {
            const content = base64.slice(i * maxPartLen, (i + 1) * maxPartLen);
            chunks.push(`${messageId}|${i + 1}|${totalParts}|${content}`);
        }
        return chunks;
    }

    async _sendStreamMessage(payload) {
        const chunks = this._chunkPayload(payload);
        for (const chunk of chunks) {
            const bytes = new TextEncoder().encode(chunk);
            await this._client.sendStreamMessage(bytes);
        }
    }

    // === 分块接收重组 ===
    _handleStreamMessage(uid, data) {
        const chunk = String.fromCharCode(...new Uint8Array(data));
        const [msgId, partIdx, totalParts, content] = chunk.split('|', 4);
        
        if (!this._messageCache[msgId]) {
            this._messageCache[msgId] = { parts: {}, total: parseInt(totalParts) };
            // 设置超时清理
            setTimeout(() => delete this._messageCache[msgId], 5000);
        }
        
        this._messageCache[msgId].parts[parseInt(partIdx)] = content;
        
        // 检查是否收齐
        if (Object.keys(this._messageCache[msgId].parts).length === this._messageCache[msgId].total) {
            const base64 = Object.keys(this._messageCache[msgId].parts)
                .sort((a, b) => a - b)
                .map(k => this._messageCache[msgId].parts[k])
                .join('');
            
            const json = this._base64ToUtf8(base64);
            const msg = JSON.parse(json);
            this._dispatchMessage(msg);
            
            delete this._messageCache[msgId];
        }
    }
}
```

### 4.4 ProtocolLogger.js

协议日志工具，用于验证协议正确性。

```javascript
/**
 * 协议日志记录器
 */
class ProtocolLogger {
    constructor() {
        this._logs = [];
        this._listeners = [];
    }

    /**
     * 记录发送的消息
     */
    logSend(type, data) {
        this._log('SEND', type, data);
    }

    /**
     * 记录接收的消息
     */
    logReceive(type, data) {
        this._log('RECV', type, data);
    }

    /**
     * 验证 TTS 状态机时序
     * @returns {Object} - { valid: boolean, errors: string[] }
     */
    validateTtsStateMachine() {
        const ttsLogs = this._logs.filter(l => l.type === 'tts');
        const errors = [];
        
        let state = 'idle'; // idle -> started -> sentence -> stopped
        for (const log of ttsLogs) {
            const ttsState = log.data.state;
            
            if (ttsState === 'start') {
                if (state !== 'idle' && state !== 'stopped') {
                    errors.push(`Invalid state transition: ${state} -> start`);
                }
                state = 'started';
            } else if (ttsState === 'sentence_start') {
                if (state !== 'started' && state !== 'sentence_end') {
                    errors.push(`sentence_start without prior start or sentence_end`);
                }
                state = 'sentence_start';
            } else if (ttsState === 'sentence_end') {
                if (state !== 'sentence_start') {
                    errors.push(`sentence_end without sentence_start`);
                }
                state = 'sentence_end';
            } else if (ttsState === 'stop') {
                state = 'stopped';
            }
        }
        
        return { valid: errors.length === 0, errors };
    }

    /**
     * 导出日志为 JSON
     */
    export() {
        return JSON.stringify(this._logs, null, 2);
    }
}
```

---

## 5. UI 设计

### 5.1 连接模式选择区域

在现有「设备配置」section 下方新增：

```html
<div class="section">
    <h2>
        连接模式
        <span class="connection-status">
            <span id="modeStatus">未选择</span>
        </span>
    </h2>
    <div class="mode-selector">
        <label class="mode-option">
            <input type="radio" name="connectionMode" value="websocket" checked>
            <span class="mode-label">
                <strong>WebSocket</strong>
                <small>直连 xiaozhi-server（本地/远端）</small>
            </span>
        </label>
        <label class="mode-option">
            <input type="radio" name="connectionMode" value="agora-rtc">
            <span class="mode-label">
                <strong>Agora RTC</strong>
                <small>TEN Framework 远端服务</small>
            </span>
        </label>
    </div>
    
    <!-- WebSocket 配置（现有的 OTA URL 输入） -->
    <div id="wsConfig" class="mode-config">
        <div class="config-item">
            <label>OTA 服务器地址:</label>
            <input type="text" id="otaUrl" value="http://127.0.0.1:8002/xiaozhi/ota/">
        </div>
    </div>
    
    <!-- Agora RTC 配置（新增） -->
    <div id="rtcConfig" class="mode-config" style="display: none;">
        <div class="config-item">
            <label>远端服务地址:</label>
            <input type="text" id="rtcServerUrl" placeholder="http://your-ten-server:8080">
        </div>
        <div class="config-item">
            <label>Channel Name:</label>
            <input type="text" id="rtcChannel" placeholder="留空自动生成">
        </div>
        <div class="config-item">
            <label>Graph Name:</label>
            <input type="text" id="rtcGraphName" value="xiaozhi_voice_assistant">
        </div>
    </div>
</div>
```

### 5.2 协议日志面板

在「会话记录」section 中增加协议日志标签页：

```html
<div class="tabs">
    <button class="tab active" data-tab="conversation">会话记录</button>
    <button class="tab" data-tab="protocol">协议日志</button>
</div>

<div class="tab-content" id="protocolTab" style="display: none;">
    <div class="protocol-toolbar">
        <button id="clearProtocolLog">清空日志</button>
        <button id="exportProtocolLog">导出 JSON</button>
        <button id="validateTts">验证 TTS 状态机</button>
    </div>
    <div id="protocolLog" class="protocol-log">
        <!-- 协议日志条目 -->
    </div>
</div>
```

协议日志条目样式：

```css
.protocol-log-entry {
    padding: 8px 12px;
    margin-bottom: 4px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
}

.protocol-log-entry.send {
    background-color: #e3f2fd;
    border-left: 3px solid #2196f3;
}

.protocol-log-entry.recv {
    background-color: #e8f5e9;
    border-left: 3px solid #4caf50;
}

.protocol-log-entry .timestamp {
    color: #999;
    margin-right: 8px;
}

.protocol-log-entry .direction {
    font-weight: bold;
    margin-right: 8px;
}

.protocol-log-entry .type {
    color: #9c27b0;
    margin-right: 8px;
}
```

---

## 6. API 接口规范

### 6.1 远端服务 API（Agora RTC 模式）

#### 获取 Agora Token

```
POST /api/token/generate

Request:
{
    "request_id": "uuid",
    "uid": 12345,
    "channel_name": "test-channel-001"
}

Response:
{
    "code": "0",
    "data": {
        "appId": "xxxxxxxxxxxxxxxx",
        "token": "006xxxxxxxxx..."
    }
}
```

#### 启动 Agent

```
POST /api/agents/start

Request:
{
    "request_id": "uuid",
    "channel_name": "test-channel-001",
    "user_uid": 12345,
    "graph_name": "xiaozhi_voice_assistant",
    "language": "zh-CN",
    "voice_type": "female"
}

Response:
{
    "code": "0",
    "data": {
        "channel_name": "test-channel-001"
    }
}
```

#### 停止 Agent

```
POST /api/agents/stop

Request:
{
    "request_id": "uuid",
    "channel_name": "test-channel-001"
}

Response:
{
    "code": "0"
}
```

---

## 7. 实现计划

### Phase 1: 代码重构（保持现有功能）

1. 创建 `ConnectionManager.js` 抽象接口
2. 从 `test_page.html` 提取代码，创建 `WebSocketManager.js`
3. 重构 `test_page.html`，使用 `ConnectionManager` 接口
4. 测试验证 WebSocket 模式功能不变

### Phase 2: Agora RTC 实现

1. 创建 `AgoraRtcManager.js`
2. 实现分块消息传输（发送/接收）
3. 实现音频轨道管理
4. 实现远端服务 API 调用

### Phase 3: UI 集成

1. 添加连接模式选择 UI
2. 添加 RTC 配置表单
3. 根据模式切换显示配置项
4. 根据模式实例化对应的 Manager

### Phase 4: 协议验证工具

1. 创建 `ProtocolLogger.js`
2. 添加协议日志面板 UI
3. 实现 TTS 状态机验证
4. 实现日志导出功能

### Phase 5: 测试与优化

1. WebSocket 模式回归测试
2. Agora RTC 模式功能测试
3. 协议正确性验证
4. 错误处理与边界情况

---

## 8. 测试用例

### 8.1 基础连接测试

| 用例 | WebSocket | Agora RTC |
|------|-----------|-----------|
| 正常连接 | ✓ | ✓ |
| 连接超时 | ✓ | ✓ |
| 连接失败重试 | ✓ | ✓ |
| 主动断开 | ✓ | ✓ |
| 异常断开恢复 | ✓ | ✓ |

### 8.2 小智协议测试

| 用例 | 描述 |
|------|------|
| Hello 握手 | 发送 hello，验证收到正确的 hello response |
| 文本输入 | 发送 listen.detect，验证收到 stt + tts 状态序列 |
| TTS 状态机 | 验证 start → sentence_start → sentence_end → stop 时序 |
| 打断 | 在 TTS 播放中发送 abort，验证正确停止 |
| MCP 工具 | 发送 tools/list，验证工具调用流程 |

### 8.3 音频测试

| 用例 | WebSocket | Agora RTC |
|------|-----------|-----------|
| 录音采集 | PCM → Opus 编码 | 麦克风轨道 |
| 音频发送 | 二进制 WS 帧 | 音频轨道发布 |
| 音频接收 | Opus 解码播放 | 远端轨道订阅播放 |
| 打断时音频停止 | ✓ | ✓ |

---

## 9. 注意事项

### 9.1 Agora SDK 版本

使用 Agora RTC SDK NG 4.x 版本：

```html
<script src="https://download.agora.io/sdk/release/AgoraRTC_N-4.22.0.js"></script>
```

### 9.2 安全上下文

Agora SDK 需要在安全上下文（HTTPS 或 localhost）中运行。测试时需要：

- 使用 `localhost` 而非 `127.0.0.1`
- 或者使用 HTTPS

### 9.3 CORS 配置

远端服务需要允许跨域请求：

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

### 9.4 采样率差异

- WebSocket 模式：16kHz（设备端原生 Opus）
- Agora RTC 模式：24kHz（TEN Framework TTS 输出）

设备端需要正确处理采样率切换。

---

## 10. 附录

### 10.1 小智协议消息类型一览

| 类型 | 方向 | 说明 |
|------|------|------|
| `hello` | 双向 | 握手消息 |
| `listen` | Client→Server | 语音状态（start/stop/detect） |
| `abort` | Client→Server | 用户打断 |
| `tts` | Server→Client | TTS 状态（start/sentence_*/stop） |
| `stt` | Server→Client | 语音识别结果 |
| `llm` | Server→Client | LLM 表情/状态 |
| `iot` | 双向 | IoT 设备控制 |
| `mcp` | 双向 | MCP 工具调用 |

### 10.2 参考资料

- Agora RTC SDK NG 文档: https://docs.agora.io/cn/video-calling/overview/product-overview
- TEN Framework: https://github.com/TEN-framework/TEN-framework
- 小智协议规范: `docs/protocol/office.md`

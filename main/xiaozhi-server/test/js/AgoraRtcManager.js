/**
 * AgoraRtcManager - Agora RTC 连接管理器
 * 
 * 实现 ConnectionManager 接口，提供 Agora RTC 模式的连接功能。
 * 参考实现：plaud-agent-platform/ai_agents/agents/examples/xiaozhi-voice-assistant/frontend/src/manager/rtc/rtc.ts
 */

import { 
    ConnectionManager, 
    ConnectionState, 
    ConnectionMode,
    XiaozhiMessageType,
    ListenState,
    TTSState
} from './ConnectionManager.js';
import { protocolLogger, LogDirection } from './ProtocolLogger.js';
import { log } from './utils/logger.js';

/**
 * 消息分块超时时间（毫秒）
 */
const CHUNK_TIMEOUT_MS = 5000;

/**
 * 最大分块内容长度
 */
const MAX_CHUNK_CONTENT_LENGTH = 800;

/**
 * Ping 间隔时间（毫秒）- 每 3 秒发送一次，保持 worker 活跃
 */
const PING_INTERVAL_MS = 3000;

/**
 * Agora RTC 连接管理器
 */
export class AgoraRtcManager extends ConnectionManager {
    constructor() {
        super();
        
        // Agora RTC 客户端
        this._client = null;
        this._joined = false;
        this._initialized = false;
        
        // 音频轨道
        this._localAudioTrack = null;
        this._remoteAudioTrack = null;
        
        // 配置
        this._config = null;
        this._appId = null;
        this._token = null;
        this._channel = null;
        this._userId = null;
        
        // 分块消息缓存
        this._messageCache = {};
        this._messageCleanupTimers = {};
        this._seenMessageIds = {};
        
        // TTS 响应累积（用于显示完整响应）
        this._agentResponseText = '';
        this._agentResponseTime = 0;
        this._agentSessionId = 0;
        
        // Ping 定时器（保持 worker 活跃）
        this._pingInterval = null;
    }

    /**
     * @override
     */
    getMode() {
        return ConnectionMode.AGORA_RTC;
    }

    /**
     * @override
     */
    supportsLocalAudio() {
        // Agora RTC 模式不需要本地 Opus 编解码
        // 音频通过 Agora 音频轨道发送
        return false;
    }

    /**
     * 生成消息 ID
     */
    _genMessageId() {
        return `${Date.now().toString(36)}-${Math.random().toString(16).slice(2)}`;
    }

    /**
     * 生成随机 User ID
     */
    _genUserId() {
        return Math.floor(Math.random() * 100000) + 1;
    }

    /**
     * 生成 Channel Name
     */
    _genChannel() {
        return `xiaozhi-test-${Date.now().toString(36)}`;
    }

    /**
     * UTF-8 字符串转 Base64
     */
    _utf8ToBase64(text) {
        const bytes = new TextEncoder().encode(text);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    /**
     * Base64 转 UTF-8 字符串
     */
    _base64ToUtf8(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return new TextDecoder('utf-8').decode(bytes);
    }

    /**
     * 将 JSON payload 分块
     * @param {string} payloadUtf8 - JSON 字符串
     * @returns {string[]} - 分块数组
     */
    _chunkPayload(payloadUtf8) {
        const base64 = this._utf8ToBase64(payloadUtf8);
        const messageId = this._genMessageId();
        const maxPartLen = MAX_CHUNK_CONTENT_LENGTH;

        const totalParts = Math.max(1, Math.ceil(base64.length / maxPartLen));
        const chunks = [];
        
        for (let i = 0; i < totalParts; i++) {
            const partIndex = i + 1;
            const content = base64.slice(i * maxPartLen, (i + 1) * maxPartLen);
            chunks.push(`${messageId}|${partIndex}|${totalParts}|${content}`);
        }
        
        return chunks;
    }

    /**
     * 检查 Agora SDK 是否可用
     */
    _checkAgoraSDK() {
        if (typeof AgoraRTC === 'undefined') {
            throw new Error('Agora RTC SDK 未加载。请确保已引入 agora-rtc-sdk-ng');
        }
    }

    /**
     * 初始化 Agora RTC 客户端
     */
    async _initClient() {
        if (this._initialized) return;

        this._checkAgoraSDK();

        try {
            this._client = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' });
            this._setupEventListeners();
            this._initialized = true;
            log('[RTC] 客户端初始化成功', 'success');
        } catch (error) {
            log(`[RTC] 客户端初始化失败: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * 设置 RTC 事件监听
     */
    _setupEventListeners() {
        // 网络质量
        this._client.on('network-quality', (quality) => {
            this._emit('networkQuality', quality);
        });

        // 远端用户发布
        this._client.on('user-published', async (user, mediaType) => {
            await this._client.subscribe(user, mediaType);
            log(`[RTC] 订阅远端用户 ${user.uid} 的 ${mediaType}`, 'info');
            
            if (mediaType === 'audio') {
                this._remoteAudioTrack = user.audioTrack;
                if (this._remoteAudioTrack && !this._remoteAudioTrack.isPlaying) {
                    this._remoteAudioTrack.play();
                    log('[RTC] 开始播放远端音频', 'success');
                }
            }
        });

        // 远端用户取消发布（Agent 暂停发送音频）
        this._client.on('user-unpublished', async (user, mediaType) => {
            await this._client.unsubscribe(user, mediaType);
            log(`[RTC] 取消订阅远端用户 ${user.uid} 的 ${mediaType}（Agent 暂停发送）`, 'info');
            
            if (mediaType === 'audio') {
                this._remoteAudioTrack = null;
            }
        });

        // 远端用户离开频道
        this._client.on('user-left', (user, reason) => {
            log(`[RTC] ⚠️ 远端用户 ${user.uid} 离开频道，原因: ${reason}`, 'warning');
            this._remoteAudioTrack = null;
        });

        // 远端用户加入频道
        this._client.on('user-joined', (user) => {
            log(`[RTC] 远端用户 ${user.uid} 加入频道`, 'info');
        });

        // 数据通道消息
        this._client.on('stream-message', (uid, data) => {
            this._handleStreamMessage(uid, data);
        });

        // 连接状态变化
        this._client.on('connection-state-change', (curState, prevState) => {
            log(`[RTC] 连接状态: ${prevState} -> ${curState}`, 'info');
            
            if (curState === 'DISCONNECTED') {
                this._setState(ConnectionState.DISCONNECTED);
            }
        });
    }

    /**
     * 处理 Data Channel 消息
     */
    _handleStreamMessage(uid, data) {
        try {
            const chunk = String.fromCharCode(...new Uint8Array(data));
            
            // 记录原始分块
            protocolLogger.logReceive('chunk', { raw: chunk.substring(0, 100) + '...' }, this.getMode(), chunk);

            // 尝试直接解析 JSON（兼容模式）
            if (chunk.startsWith('{') && chunk.endsWith('}')) {
                const parsed = JSON.parse(chunk);
                this._dispatchXiaozhiMessage(parsed);
                return;
            }

            // 解析分块格式: msg_id|part_index|total_parts|base64_content
            const parts = chunk.split('|', 4);
            if (parts.length !== 4) {
                log(`[RTC] 无效的分块格式: ${chunk.substring(0, 50)}`, 'warning');
                return;
            }

            const [msgId, partIdxStr, totalPartsStr, content] = parts;
            
            if (totalPartsStr === '???') {
                // 等待发送方填充 total_parts
                return;
            }

            const partIndex = parseInt(partIdxStr, 10);
            const totalParts = parseInt(totalPartsStr, 10);

            if (totalParts <= 0 || partIndex <= 0) {
                return;
            }

            // 初始化缓存
            if (!this._messageCache[msgId]) {
                this._messageCache[msgId] = {
                    parts: {},
                    totalParts
                };
                
                // 设置超时清理
                this._messageCleanupTimers[msgId] = setTimeout(() => {
                    this._expireMessage(msgId);
                }, CHUNK_TIMEOUT_MS);
            }

            // 缓存分块
            this._messageCache[msgId].parts[partIndex] = content;

            // 检查是否收齐
            if (Object.keys(this._messageCache[msgId].parts).length === totalParts) {
                // 清理超时定时器
                if (this._messageCleanupTimers[msgId]) {
                    clearTimeout(this._messageCleanupTimers[msgId]);
                    delete this._messageCleanupTimers[msgId];
                }

                // 去重检查
                if (this._seenMessageIds[msgId]) {
                    delete this._messageCache[msgId];
                    return;
                }

                // 重组消息
                const base64Payload = Object.keys(this._messageCache[msgId].parts)
                    .sort((a, b) => parseInt(a) - parseInt(b))
                    .map(k => this._messageCache[msgId].parts[k])
                    .join('');

                delete this._messageCache[msgId];

                // 标记已处理
                this._seenMessageIds[msgId] = true;
                setTimeout(() => {
                    delete this._seenMessageIds[msgId];
                }, 30000);

                // 解码并分发
                const payloadText = this._base64ToUtf8(base64Payload);
                const parsed = JSON.parse(payloadText);
                this._dispatchXiaozhiMessage(parsed);
            }

        } catch (error) {
            log(`[RTC] 处理 stream-message 错误: ${error.message}`, 'error');
        }
    }

    /**
     * 过期未完成的消息
     */
    _expireMessage(msgId) {
        log(`[RTC] 消息超时: ${msgId}`, 'warning');
        delete this._messageCache[msgId];
        delete this._messageCleanupTimers[msgId];
    }

    /**
     * 分发小智协议消息
     */
    _dispatchXiaozhiMessage(message) {
        const type = message.type;
        
        protocolLogger.logReceive(type, message, this.getMode());
        log(`[RTC] 收到消息: ${type}`, 'debug');

        // 处理 TTS 消息（累积响应文本）
        if (type === XiaozhiMessageType.TTS) {
            this._handleTtsMessage(message);
        }

        // 调用父类方法分发
        this._handleXiaozhiMessage(message);
    }

    /**
     * 处理 TTS 消息（累积响应）
     */
    _handleTtsMessage(message) {
        const state = message.state;
        const text = message.text;

        switch (state) {
            case TTSState.START:
                this._agentSessionId++;
                this._agentResponseText = '';
                this._agentResponseTime = Date.now();
                break;

            case TTSState.SENTENCE_START:
                if (text) {
                    this._agentResponseText += text;
                }
                break;

            case TTSState.SENTENCE_END:
                // 确保文本不重复添加
                if (text && !this._agentResponseText.endsWith(text)) {
                    this._agentResponseText += text;
                }
                break;

            case TTSState.STOP:
                log(`[RTC] TTS 完成: ${this._agentResponseText}`, 'info');
                this._agentResponseText = '';
                break;
        }
    }

    /**
     * 发送 Data Channel 消息
     * @param {Uint8Array} bytes - 消息字节
     */
    async _sendStreamMessage(bytes) {
        if (!this._client) {
            throw new Error('RTC 客户端未初始化');
        }

        const anyClient = this._client;
        if (typeof anyClient.sendStreamMessage !== 'function') {
            throw new Error('sendStreamMessage 不支持');
        }

        try {
            await anyClient.sendStreamMessage(bytes);
            log(`[RTC] 发送 stream message: ${bytes.length} bytes`, 'debug');
        } catch (error) {
            log(`[RTC] 发送 stream message 失败: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * 发送分块消息
     * @param {string} payloadJson - JSON 字符串
     */
    async _sendChunkedMessage(payloadJson) {
        const chunks = this._chunkPayload(payloadJson);
        
        for (const chunk of chunks) {
            const bytes = new TextEncoder().encode(chunk);
            await this._sendStreamMessage(bytes);
            
            protocolLogger.logSend('chunk', { 
                raw: chunk.substring(0, 100) + '...',
                size: bytes.length 
            }, this.getMode(), chunk);
        }
    }

    /**
     * 发送 JSON 消息
     */
    async _sendJson(message) {
        const json = JSON.stringify(message);
        await this._sendChunkedMessage(json);
        
        protocolLogger.logSend(message.type, message, this.getMode());
        log(`[RTC] 发送消息: ${message.type}`, 'debug');
    }

    /**
     * 获取 Agora Token
     * @param {Object} config - 配置
     * @returns {Promise<Object>} - { appId, token }
     */
    async _fetchToken(config) {
        const url = `${config.serverUrl}/api/token/generate`;
        
        log(`[RTC] 获取 Token: ${url}`, 'info');

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_id: this._genMessageId(),
                uid: this._userId,
                channel_name: this._channel
            })
        });

        if (!response.ok) {
            throw new Error(`获取 Token 失败: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.code !== '0' && result.code !== 0) {
            throw new Error(`获取 Token 失败: ${result.msg || 'unknown error'}`);
        }

        return result.data;
    }

    /**
     * 启动远端 Agent
     * @param {Object} config - 配置
     */
    async _startAgent(config) {
        const url = `${config.serverUrl}/api/agents/start`;
        
        log(`[RTC] 启动 Agent: ${url}`, 'info');

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_id: this._genMessageId(),
                channel_name: this._channel,
                user_uid: this._userId,
                graph_name: config.graphName || 'xiaozhi_voice_assistant',
                language: config.language || 'zh-CN',
                voice_type: config.voiceType || 'female'
            })
        });

        if (!response.ok) {
            throw new Error(`启动 Agent 失败: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.code !== '0' && result.code !== 0) {
            throw new Error(`启动 Agent 失败: ${result.msg || 'unknown error'}`);
        }

        log('[RTC] Agent 启动成功', 'success');
        return result.data;
    }

    /**
     * 停止远端 Agent
     */
    async _stopAgent() {
        if (!this._config || !this._channel) return;

        const url = `${this._config.serverUrl}/api/agents/stop`;
        
        try {
            await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    request_id: this._genMessageId(),
                    channel_name: this._channel
                })
            });
            log('[RTC] Agent 已停止', 'info');
        } catch (error) {
            log(`[RTC] 停止 Agent 失败: ${error.message}`, 'warning');
        }
    }

    /**
     * 启动 Ping 定时器
     * 每隔 PING_INTERVAL_MS 毫秒发送一次 ping，保持 worker 活跃
     */
    _startPing() {
        this._stopPing();  // 确保没有重复的定时器
        
        // 立即发送第一次 ping
        this._sendPing().catch(err => {
            log(`[RTC] 首次 Ping 失败: ${err.message}`, 'warning');
        });
        
        this._pingInterval = setInterval(async () => {
            try {
                await this._sendPing();
            } catch (err) {
                log(`[RTC] Ping 定时器错误: ${err.message}`, 'error');
            }
        }, PING_INTERVAL_MS);
        
        log(`[RTC] Ping 定时器已启动 (间隔: ${PING_INTERVAL_MS}ms)`, 'info');
    }

    /**
     * 停止 Ping 定时器
     */
    _stopPing() {
        if (this._pingInterval) {
            clearInterval(this._pingInterval);
            this._pingInterval = null;
            log('[RTC] 🔴 Ping 定时器已停止', 'info');
        }
    }

    /**
     * 发送 Ping 请求
     * 使用与 start/stop 相同的 URL 模式
     */
    async _sendPing() {
        if (!this._config || !this._channel) {
            log('[RTC] ⚠️ Ping 跳过: config 或 channel 为空', 'warning');
            return;
        }

        // 使用与 _startAgent/_stopAgent 相同的 URL 模式
        const url = `${this._config.serverUrl}/api/agents/ping`;
        const requestId = this._genMessageId();
        
        try {
            log(`[RTC] 📡 发送 Ping: ${url}`, 'info');
            
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    request_id: requestId,
                    channel_name: this._channel
                })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.code === '0' || result.code === 0) {
                    log(`[RTC] ✅ Ping 成功: channel=${this._channel}`, 'success');
                } else {
                    log(`[RTC] ❌ Ping 响应错误: ${result.msg || JSON.stringify(result)}`, 'warning');
                }
            } else {
                const text = await response.text();
                log(`[RTC] ❌ Ping HTTP 错误: status=${response.status}, body=${text.substring(0, 200)}`, 'warning');
            }
        } catch (error) {
            log(`[RTC] ❌ Ping 网络失败: ${error.message}`, 'error');
        }
    }

    /**
     * @override
     */
    async connect(config) {
        if (this._state === ConnectionState.CONNECTED || this._state === ConnectionState.CONNECTING) {
            log('[RTC] 已经连接或正在连接中', 'warning');
            return false;
        }

        this._config = config;
        this._setState(ConnectionState.CONNECTING);

        try {
            // 0. 检查必要配置
            if (!config.serverUrl) {
                throw new Error('请填写远端服务地址');
            }

            // 1. 初始化客户端
            await this._initClient();

            // 2. 生成 Channel 和 User ID
            this._channel = config.channel || this._genChannel();
            this._userId = config.userId || this._genUserId();
            
            log(`[RTC] Channel: ${this._channel}, UserId: ${this._userId}`, 'info');

            // 3. 获取 Token
            const tokenData = await this._fetchToken(config);
            this._appId = tokenData.appId;
            this._token = tokenData.token;

            // 4. 加入频道
            await this._client.join(this._appId, this._channel, this._token, this._userId);
            log('[RTC] 已加入频道', 'success');

            // 5. 启动远端 Agent
            await this._startAgent(config);

            // 6. 启动 Ping 定时器（保持 worker 活跃）
            this._startPing();

            // 7. 创建并发布麦克风音频轨道
            await this._setupAudioTrack();

            this._joined = true;
            this._setState(ConnectionState.CONNECTED);
            
            return true;

        } catch (error) {
            log(`[RTC] 连接失败: ${error.message}`, 'error');
            this._setState(ConnectionState.ERROR);
            this._emit('error', error);
            await this._cleanup();
            return false;
        }
    }

    /**
     * 设置音频轨道
     */
    async _setupAudioTrack() {
        try {
            this._localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack({
                encoderConfig: 'speech_low_quality'
            });
            
            await this._client.publish([this._localAudioTrack]);
            log('[RTC] 音频轨道已发布', 'success');
            
        } catch (error) {
            log(`[RTC] 音频轨道设置失败: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * @override
     */
    async disconnect() {
        await this._cleanup();
    }

    /**
     * 清理资源
     */
    async _cleanup() {
        // 停止 Ping 定时器
        this._stopPing();

        // 停止 Agent
        await this._stopAgent();

        // 关闭本地音频轨道
        if (this._localAudioTrack) {
            this._localAudioTrack.close();
            this._localAudioTrack = null;
        }

        // 离开频道
        if (this._joined && this._client) {
            try {
                await this._client.leave();
            } catch (e) {
                log(`[RTC] 离开频道失败: ${e.message}`, 'warning');
            }
        }

        // 清理状态
        this._joined = false;
        this._sessionId = null;
        this._channel = null;
        this._userId = null;
        this._messageCache = {};
        this._seenMessageIds = {};

        // 清理超时定时器
        for (const msgId in this._messageCleanupTimers) {
            clearTimeout(this._messageCleanupTimers[msgId]);
        }
        this._messageCleanupTimers = {};

        this._setState(ConnectionState.DISCONNECTED);
        log('[RTC] 已断开连接', 'info');
    }

    /**
     * @override
     */
    async sendHello(helloData) {
        const message = {
            type: XiaozhiMessageType.HELLO,
            ...helloData
        };
        await this._sendJson(message);
    }

    /**
     * @override
     */
    async sendText(text) {
        const message = {
            type: XiaozhiMessageType.LISTEN,
            state: ListenState.DETECT,
            text
        };
        await this._sendJson(message);
    }

    /**
     * @override
     */
    async sendListenStart(mode = 'auto') {
        const message = {
            type: XiaozhiMessageType.LISTEN,
            mode,
            state: ListenState.START
        };
        await this._sendJson(message);
    }

    /**
     * @override
     */
    async sendListenStop(mode = 'auto') {
        const message = {
            type: XiaozhiMessageType.LISTEN,
            mode,
            state: ListenState.STOP
        };
        await this._sendJson(message);
    }

    /**
     * @override
     * Agora RTC 模式不需要手动发送音频
     * 音频通过 Agora 音频轨道自动发送
     */
    async sendAudio(audioData) {
        log('[RTC] Agora RTC 模式不需要手动发送音频', 'warning');
    }

    /**
     * @override
     */
    async sendAbort() {
        const message = {
            type: XiaozhiMessageType.ABORT
        };
        await this._sendJson(message);
    }

    /**
     * @override
     */
    async sendMcpResponse(sessionId, payload) {
        const message = {
            session_id: sessionId,
            type: XiaozhiMessageType.MCP,
            payload
        };
        await this._sendJson(message);
    }

    /**
     * @override
     * Agora RTC 模式的录音由 Agora SDK 自动处理
     */
    async startRecording() {
        // 发送 listen start 消息
        await this.sendListenStart('auto');
        log('[RTC] 录音开始（由 Agora SDK 自动处理）', 'info');
    }

    /**
     * @override
     */
    async stopRecording() {
        // 发送 listen stop 消息
        await this.sendListenStop('auto');
        log('[RTC] 录音停止', 'info');
    }

    /**
     * 静音/取消静音本地音频轨道
     * @param {boolean} muted 
     */
    async setMuted(muted) {
        if (this._localAudioTrack) {
            await this._localAudioTrack.setMuted(muted);
            log(`[RTC] 麦克风 ${muted ? '已静音' : '已取消静音'}`, 'info');
        }
    }

    /**
     * 获取本地音频轨道是否静音
     * @returns {boolean}
     */
    isMuted() {
        return this._localAudioTrack ? this._localAudioTrack.muted : true;
    }

    /**
     * 获取 Channel 名称
     * @returns {string|null}
     */
    getChannel() {
        return this._channel;
    }

    /**
     * 获取 User ID
     * @returns {number|null}
     */
    getUserId() {
        return this._userId;
    }
}

export default AgoraRtcManager;

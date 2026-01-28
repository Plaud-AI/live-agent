/**
 * ConnectionManager - 连接管理器抽象接口
 * 
 * 提供统一的接口来管理 WebSocket 和 Agora RTC 两种连接模式。
 * 具体实现由 WebSocketManager 和 AgoraRtcManager 提供。
 */

/**
 * 连接状态枚举
 */
export const ConnectionState = {
    DISCONNECTED: 'disconnected',
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    ERROR: 'error'
};

/**
 * 连接模式枚举
 */
export const ConnectionMode = {
    WEBSOCKET: 'websocket',
    AGORA_RTC: 'agora-rtc'
};

/**
 * 小智协议消息类型
 */
export const XiaozhiMessageType = {
    HELLO: 'hello',
    LISTEN: 'listen',
    ABORT: 'abort',
    TTS: 'tts',
    STT: 'stt',
    LLM: 'llm',
    MCP: 'mcp',
    IOT: 'iot'
};

/**
 * Listen 状态枚举
 */
export const ListenState = {
    START: 'start',
    STOP: 'stop',
    DETECT: 'detect'
};

/**
 * TTS 状态枚举
 */
export const TTSState = {
    START: 'start',
    SENTENCE_START: 'sentence_start',
    SENTENCE_END: 'sentence_end',
    STOP: 'stop'
};

/**
 * 连接管理器抽象基类
 */
export class ConnectionManager {
    constructor() {
        if (new.target === ConnectionManager) {
            throw new Error('ConnectionManager is an abstract class and cannot be instantiated directly');
        }
        
        this._state = ConnectionState.DISCONNECTED;
        this._callbacks = {
            // 消息回调
            [XiaozhiMessageType.HELLO]: [],
            [XiaozhiMessageType.TTS]: [],
            [XiaozhiMessageType.STT]: [],
            [XiaozhiMessageType.LLM]: [],
            [XiaozhiMessageType.MCP]: [],
            [XiaozhiMessageType.IOT]: [],
            // 状态回调
            'stateChange': [],
            // 音频回调（仅 WebSocket 模式）
            'audio': [],
            // 错误回调
            'error': []
        };
        this._sessionId = null;
    }

    /**
     * 获取连接模式
     * @returns {string} - 'websocket' | 'agora-rtc'
     */
    getMode() {
        throw new Error('getMode() must be implemented by subclass');
    }

    /**
     * 获取连接状态
     * @returns {string} - ConnectionState
     */
    getState() {
        return this._state;
    }

    /**
     * 设置连接状态并触发回调
     * @param {string} state - 新状态
     */
    _setState(state) {
        const oldState = this._state;
        this._state = state;
        this._emit('stateChange', { oldState, newState: state });
    }

    /**
     * 是否已连接
     * @returns {boolean}
     */
    isConnected() {
        return this._state === ConnectionState.CONNECTED;
    }

    /**
     * 获取会话 ID
     * @returns {string|null}
     */
    getSessionId() {
        return this._sessionId;
    }

    /**
     * 连接到服务器
     * @param {Object} config - 连接配置
     * @returns {Promise<boolean>} - 连接是否成功
     */
    async connect(config) {
        throw new Error('connect() must be implemented by subclass');
    }

    /**
     * 断开连接
     * @returns {Promise<void>}
     */
    async disconnect() {
        throw new Error('disconnect() must be implemented by subclass');
    }

    /**
     * 发送 hello 握手消息
     * @param {Object} helloData - hello 消息数据
     * @returns {Promise<void>}
     */
    async sendHello(helloData) {
        throw new Error('sendHello() must be implemented by subclass');
    }

    /**
     * 发送文本消息 (listen.detect)
     * @param {string} text - 文本内容
     * @returns {Promise<void>}
     */
    async sendText(text) {
        throw new Error('sendText() must be implemented by subclass');
    }

    /**
     * 发送 listen 开始录音消息
     * @param {string} mode - 录音模式 ('auto' | 'manual')
     * @returns {Promise<void>}
     */
    async sendListenStart(mode = 'auto') {
        throw new Error('sendListenStart() must be implemented by subclass');
    }

    /**
     * 发送 listen 停止录音消息
     * @param {string} mode - 录音模式 ('auto' | 'manual')
     * @returns {Promise<void>}
     */
    async sendListenStop(mode = 'auto') {
        throw new Error('sendListenStop() must be implemented by subclass');
    }

    /**
     * 发送音频数据（仅 WebSocket 模式支持）
     * @param {ArrayBuffer|Uint8Array} audioData - 音频数据
     * @returns {Promise<void>}
     */
    async sendAudio(audioData) {
        throw new Error('sendAudio() must be implemented by subclass');
    }

    /**
     * 发送 abort 打断消息
     * @returns {Promise<void>}
     */
    async sendAbort() {
        throw new Error('sendAbort() must be implemented by subclass');
    }

    /**
     * 发送 MCP 响应
     * @param {string} sessionId - 会话 ID
     * @param {Object} payload - MCP 响应 payload
     * @returns {Promise<void>}
     */
    async sendMcpResponse(sessionId, payload) {
        throw new Error('sendMcpResponse() must be implemented by subclass');
    }

    /**
     * 注册消息/事件回调
     * @param {string} type - 消息类型或事件类型
     * @param {Function} callback - 回调函数
     */
    on(type, callback) {
        if (!this._callbacks[type]) {
            this._callbacks[type] = [];
        }
        this._callbacks[type].push(callback);
    }

    /**
     * 移除消息/事件回调
     * @param {string} type - 消息类型或事件类型
     * @param {Function} callback - 回调函数
     */
    off(type, callback) {
        if (this._callbacks[type]) {
            this._callbacks[type] = this._callbacks[type].filter(cb => cb !== callback);
        }
    }

    /**
     * 触发消息/事件回调
     * @param {string} type - 消息类型或事件类型
     * @param {*} data - 回调数据
     */
    _emit(type, data) {
        if (this._callbacks[type]) {
            for (const callback of this._callbacks[type]) {
                try {
                    callback(data);
                } catch (e) {
                    console.error(`Error in ${type} callback:`, e);
                }
            }
        }
    }

    /**
     * 处理接收到的小智协议消息
     * @param {Object} message - 解析后的 JSON 消息
     */
    _handleXiaozhiMessage(message) {
        const type = message.type;
        
        if (type === XiaozhiMessageType.HELLO && message.session_id) {
            this._sessionId = message.session_id;
        }
        
        this._emit(type, message);
    }

    /**
     * 开始录音（创建音频轨道或初始化录音器）
     * @returns {Promise<void>}
     */
    async startRecording() {
        throw new Error('startRecording() must be implemented by subclass');
    }

    /**
     * 停止录音
     * @returns {Promise<void>}
     */
    async stopRecording() {
        throw new Error('stopRecording() must be implemented by subclass');
    }

    /**
     * 是否支持本地音频发送
     * WebSocket 模式：支持（需要本地 Opus 编码）
     * Agora RTC 模式：不支持（音频通过 Agora 音频轨道发送）
     * @returns {boolean}
     */
    supportsLocalAudio() {
        return false;
    }
}

export default ConnectionManager;

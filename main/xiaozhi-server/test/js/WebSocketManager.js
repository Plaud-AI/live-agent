/**
 * WebSocketManager - WebSocket 连接管理器
 * 
 * 实现 ConnectionManager 接口，提供 WebSocket 模式的连接功能。
 * 从现有 test_page.html 中提取的逻辑。
 */

import { 
    ConnectionManager, 
    ConnectionState, 
    ConnectionMode,
    XiaozhiMessageType,
    ListenState 
} from './ConnectionManager.js';
import { protocolLogger, LogDirection } from './ProtocolLogger.js';
import { log } from './utils/logger.js';

/**
 * WebSocket 连接管理器
 */
export class WebSocketManager extends ConnectionManager {
    constructor() {
        super();
        
        // WebSocket 实例
        this._websocket = null;
        
        // 配置
        this._config = null;
        
        // 音频相关
        this._audioContext = null;
        this._opusEncoder = null;
        this._opusDecoder = null;
        this._audioProcessor = null;
        this._audioSource = null;
        this._mediaStream = null;
        this._isRecording = false;
        this._pcmDataBuffer = new Int16Array();
        
        // 流式播放相关
        this._streamingContext = null;
        this._audioQueue = null;
        
        // 常量
        this.SAMPLE_RATE = 16000;
        this.CHANNELS = 1;
        this.FRAME_SIZE = 960; // 60ms @ 16kHz
    }

    /**
     * @override
     */
    getMode() {
        return ConnectionMode.WEBSOCKET;
    }

    /**
     * @override
     */
    supportsLocalAudio() {
        return true;
    }

    /**
     * 获取 AudioContext 实例（懒加载）
     */
    _getAudioContext() {
        if (!this._audioContext) {
            this._audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: this.SAMPLE_RATE,
                latencyHint: 'interactive'
            });
            log(`创建音频上下文，采样率: ${this.SAMPLE_RATE}Hz`, 'debug');
        }
        return this._audioContext;
    }

    /**
     * OTA 请求获取 WebSocket URL
     * @param {string} otaUrl - OTA 服务器地址
     * @param {Object} config - 连接配置
     * @returns {Promise<Object|null>} - OTA 响应数据
     */
    async _sendOTA(otaUrl, config) {
        try {
            const res = await fetch(otaUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Device-Id': config.deviceId,
                    'Client-Id': config.clientId,
                    'Agent-Id': config.agentId
                },
                body: JSON.stringify({
                    version: 0,
                    uuid: '',
                    application: {
                        name: 'xiaozhi-web-test',
                        version: '1.0.0',
                        compile_time: '2025-04-16 10:00:00',
                        idf_version: '4.4.3',
                        elf_sha256: '1234567890abcdef1234567890abcdef1234567890abcdef'
                    },
                    ota: { label: 'xiaozhi-web-test' },
                    board: {
                        type: 'xiaozhi-web-test',
                        ssid: 'xiaozhi-web-test',
                        rssi: 0,
                        channel: 0,
                        ip: '192.168.1.1',
                        mac: config.deviceMac
                    },
                    flash_size: 0,
                    minimum_free_heap_size: 0,
                    mac_address: config.deviceMac,
                    chip_model_name: '',
                    chip_info: { model: 0, cores: 0, revision: 0, features: 0 },
                    partition_table: [{ label: '', type: 0, subtype: 0, address: 0, size: 0 }]
                })
            });

            if (!res.ok) {
                throw new Error(`${res.status} ${res.statusText}`);
            }

            const result = await res.json();
            log('OTA 请求成功', 'success');
            return result;
        } catch (err) {
            log(`OTA 请求失败: ${err.message}`, 'error');
            return null;
        }
    }

    /**
     * @override
     */
    async connect(config) {
        if (this._state === ConnectionState.CONNECTED || this._state === ConnectionState.CONNECTING) {
            log('已经连接或正在连接中', 'warning');
            return false;
        }

        this._config = config;
        this._setState(ConnectionState.CONNECTING);

        try {
            // 1. OTA 请求获取 WebSocket URL
            log('正在检查 OTA 状态...', 'info');
            const otaResult = await this._sendOTA(config.otaUrl, config);
            
            if (!otaResult) {
                throw new Error('无法从 OTA 服务器获取信息');
            }

            const { websocket } = otaResult;
            if (!websocket || !websocket.url) {
                throw new Error('OTA 响应中缺少 websocket 信息');
            }

            // 2. 构建 WebSocket URL
            let connUrl = new URL(websocket.url);
            
            if (websocket.token) {
                const token = websocket.token.startsWith('Bearer ') 
                    ? websocket.token 
                    : `Bearer ${websocket.token}`;
                connUrl.searchParams.append('authorization', token);
            }
            
            connUrl.searchParams.append('device-id', config.deviceId);
            connUrl.searchParams.append('client-id', config.clientId);
            connUrl.searchParams.append('agent-id', config.agentId);

            const wsUrl = connUrl.toString();
            log(`正在连接: ${wsUrl}`, 'info');

            // 3. 建立 WebSocket 连接
            return new Promise((resolve, reject) => {
                this._websocket = new WebSocket(wsUrl);
                this._websocket.binaryType = 'arraybuffer';

                const connectionTimeout = setTimeout(() => {
                    this._websocket.close();
                    this._setState(ConnectionState.ERROR);
                    reject(new Error('连接超时'));
                }, 10000);

                this._websocket.onopen = () => {
                    clearTimeout(connectionTimeout);
                    log('WebSocket 已连接', 'success');
                    this._setState(ConnectionState.CONNECTED);
                    resolve(true);
                };

                this._websocket.onclose = (event) => {
                    clearTimeout(connectionTimeout);
                    log(`WebSocket 已断开: ${event.code} ${event.reason}`, 'info');
                    this._setState(ConnectionState.DISCONNECTED);
                    this._cleanup();
                };

                this._websocket.onerror = (error) => {
                    clearTimeout(connectionTimeout);
                    log(`WebSocket 错误: ${error.message || '未知错误'}`, 'error');
                    this._setState(ConnectionState.ERROR);
                    this._emit('error', error);
                };

                this._websocket.onmessage = (event) => {
                    this._handleMessage(event);
                };
            });

        } catch (error) {
            log(`连接失败: ${error.message}`, 'error');
            this._setState(ConnectionState.ERROR);
            this._emit('error', error);
            return false;
        }
    }

    /**
     * @override
     */
    async disconnect() {
        if (this._websocket) {
            this._websocket.close();
        }
        this._cleanup();
    }

    /**
     * 清理资源
     */
    _cleanup() {
        this._isRecording = false;
        
        if (this._audioProcessor) {
            this._audioProcessor.disconnect();
            this._audioProcessor = null;
        }
        
        if (this._audioSource) {
            this._audioSource.disconnect();
            this._audioSource = null;
        }
        
        if (this._mediaStream) {
            this._mediaStream.getTracks().forEach(track => track.stop());
            this._mediaStream = null;
        }
        
        this._websocket = null;
        this._sessionId = null;
    }

    /**
     * 处理 WebSocket 消息
     */
    _handleMessage(event) {
        try {
            if (typeof event.data === 'string') {
                // 文本消息（JSON）
                const message = JSON.parse(event.data);
                protocolLogger.logReceive(message.type, message, this.getMode());
                this._handleXiaozhiMessage(message);
            } else {
                // 二进制消息（音频）
                this._handleBinaryMessage(event.data);
            }
        } catch (error) {
            log(`消息处理错误: ${error.message}`, 'error');
            
            // 非 JSON 格式文本消息直接显示
            if (typeof event.data === 'string') {
                log(`收到非 JSON 消息: ${event.data}`, 'warning');
            }
        }
    }

    /**
     * 处理二进制音频消息
     */
    _handleBinaryMessage(data) {
        const HEADER_SIZE = 16;
        
        if (data.byteLength <= HEADER_SIZE) {
            log('收到空音频帧', 'warning');
            return;
        }

        const headerView = new DataView(data);
        const type = headerView.getUint8(0);
        const messageTag = headerView.getUint8(1);
        const opusLength = headerView.getUint32(2, false); // big-endian

        if (opusLength <= 0 || opusLength > data.byteLength - HEADER_SIZE) {
            log(`无效的 opus 数据长度: ${opusLength}`, 'warning');
            return;
        }

        const opusData = new Uint8Array(data, HEADER_SIZE, opusLength);
        
        protocolLogger.logAudio(LogDirection.RECV, opusData.length, this.getMode());
        
        // 触发音频回调
        this._emit('audio', {
            data: opusData,
            messageTag,
            type
        });
    }

    /**
     * 发送 JSON 消息
     */
    async _sendJson(message) {
        if (!this._websocket || this._websocket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket 未连接');
        }

        const json = JSON.stringify(message);
        this._websocket.send(json);
        
        protocolLogger.logSend(message.type, message, this.getMode());
        log(`发送消息: ${json}`, 'debug');
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
            mode: 'manual',
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
     */
    async sendAudio(audioData) {
        if (!this._websocket || this._websocket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket 未连接');
        }

        this._websocket.send(audioData);
        protocolLogger.logAudio(LogDirection.SEND, audioData.byteLength, this.getMode());
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
     * 初始化 Opus 编码器
     * @returns {Object|null} - Opus 编码器对象
     */
    initOpusEncoder() {
        if (this._opusEncoder) {
            return this._opusEncoder;
        }

        try {
            if (typeof window.ModuleInstance === 'undefined') {
                if (typeof Module !== 'undefined') {
                    window.ModuleInstance = Module;
                } else {
                    throw new Error('Opus 库未加载');
                }
            }

            const mod = window.ModuleInstance;

            // 获取编码器大小
            const encoderSize = mod._opus_encoder_get_size(this.CHANNELS);
            
            // 分配内存
            const encoderPtr = mod._malloc(encoderSize);
            if (!encoderPtr) {
                throw new Error('无法分配编码器内存');
            }

            // 初始化编码器
            const err = mod._opus_encoder_init(
                encoderPtr,
                this.SAMPLE_RATE,
                this.CHANNELS,
                2048 // OPUS_APPLICATION_VOIP
            );

            if (err < 0) {
                mod._free(encoderPtr);
                throw new Error(`Opus 编码器初始化失败: ${err}`);
            }

            this._opusEncoder = {
                ptr: encoderPtr,
                module: mod,
                frameSize: this.FRAME_SIZE,

                encode: function(pcmData) {
                    const mod = this.module;
                    
                    // 分配 PCM 输入内存
                    const pcmPtr = mod._malloc(pcmData.length * 2);
                    mod.HEAP16.set(pcmData, pcmPtr >> 1);

                    // 分配 Opus 输出内存（最大 4000 字节）
                    const maxPacketSize = 4000;
                    const opusPtr = mod._malloc(maxPacketSize);

                    // 编码
                    const encodedSize = mod._opus_encode(
                        this.ptr,
                        pcmPtr,
                        this.frameSize,
                        opusPtr,
                        maxPacketSize
                    );

                    let result = null;
                    if (encodedSize > 0) {
                        result = new Uint8Array(encodedSize);
                        for (let i = 0; i < encodedSize; i++) {
                            result[i] = mod.HEAPU8[opusPtr + i];
                        }
                    }

                    // 释放内存
                    mod._free(pcmPtr);
                    mod._free(opusPtr);

                    return result;
                },

                destroy: function() {
                    if (this.ptr) {
                        this.module._free(this.ptr);
                        this.ptr = null;
                    }
                }
            };

            log('Opus 编码器初始化成功', 'success');
            return this._opusEncoder;

        } catch (error) {
            log(`Opus 编码器初始化失败: ${error.message}`, 'error');
            return null;
        }
    }

    /**
     * 创建音频处理器
     */
    async _createAudioProcessor() {
        const audioContext = this._getAudioContext();
        
        const processorCode = `
            class AudioRecorderProcessor extends AudioWorkletProcessor {
                constructor() {
                    super();
                    this.frameSize = 960;
                    this.buffer = new Int16Array(this.frameSize);
                    this.bufferIndex = 0;
                    this.isRecording = false;

                    this.port.onmessage = (event) => {
                        if (event.data.command === 'start') {
                            this.isRecording = true;
                        } else if (event.data.command === 'stop') {
                            this.isRecording = false;
                            if (this.bufferIndex > 0) {
                                this.port.postMessage({
                                    type: 'buffer',
                                    buffer: this.buffer.slice(0, this.bufferIndex)
                                });
                                this.bufferIndex = 0;
                            }
                        }
                    };
                }

                process(inputs, outputs, parameters) {
                    if (!this.isRecording) return true;

                    const input = inputs[0][0];
                    if (!input) return true;

                    for (let i = 0; i < input.length; i++) {
                        if (this.bufferIndex >= this.frameSize) {
                            this.port.postMessage({
                                type: 'buffer',
                                buffer: this.buffer.slice(0)
                            });
                            this.bufferIndex = 0;
                        }
                        this.buffer[this.bufferIndex++] = Math.max(-32768, Math.min(32767, Math.floor(input[i] * 32767)));
                    }

                    return true;
                }
            }

            registerProcessor('audio-recorder-processor', AudioRecorderProcessor);
        `;

        try {
            const blob = new Blob([processorCode], { type: 'application/javascript' });
            const url = URL.createObjectURL(blob);
            await audioContext.audioWorklet.addModule(url);
            URL.revokeObjectURL(url);

            const processor = new AudioWorkletNode(audioContext, 'audio-recorder-processor');
            
            processor.port.onmessage = (event) => {
                if (event.data.type === 'buffer') {
                    this._processPCMBuffer(event.data.buffer);
                }
            };

            // 连接静音输出
            const silent = audioContext.createGain();
            silent.gain.value = 0;
            processor.connect(silent);
            silent.connect(audioContext.destination);

            log('AudioWorklet 处理器创建成功', 'success');
            return processor;

        } catch (error) {
            log(`AudioWorklet 创建失败，使用回退方案: ${error.message}`, 'warning');
            
            // 回退到 ScriptProcessorNode
            const processor = audioContext.createScriptProcessor(4096, 1, 1);
            
            processor.onaudioprocess = (event) => {
                if (!this._isRecording) return;

                const input = event.inputBuffer.getChannelData(0);
                const buffer = new Int16Array(input.length);

                for (let i = 0; i < input.length; i++) {
                    buffer[i] = Math.max(-32768, Math.min(32767, Math.floor(input[i] * 32767)));
                }

                this._processPCMBuffer(buffer);
            };

            const silent = audioContext.createGain();
            silent.gain.value = 0;
            processor.connect(silent);
            silent.connect(audioContext.destination);

            return processor;
        }
    }

    /**
     * 处理 PCM 缓冲数据
     */
    _processPCMBuffer(buffer) {
        if (!this._isRecording) return;

        // 追加到缓冲区
        const newBuffer = new Int16Array(this._pcmDataBuffer.length + buffer.length);
        newBuffer.set(this._pcmDataBuffer);
        newBuffer.set(buffer, this._pcmDataBuffer.length);
        this._pcmDataBuffer = newBuffer;

        // 编码并发送
        const samplesPerFrame = this.FRAME_SIZE;
        
        while (this._pcmDataBuffer.length >= samplesPerFrame) {
            const frameData = this._pcmDataBuffer.slice(0, samplesPerFrame);
            this._pcmDataBuffer = this._pcmDataBuffer.slice(samplesPerFrame);
            
            this._encodeAndSend(frameData);
        }
    }

    /**
     * 编码并发送 Opus 帧
     */
    _encodeAndSend(pcmData) {
        if (!this._opusEncoder) {
            log('Opus 编码器未初始化', 'error');
            return;
        }

        try {
            const opusData = this._opusEncoder.encode(pcmData);
            
            if (opusData && opusData.length > 0) {
                this.sendAudio(opusData.buffer);
            }
        } catch (error) {
            log(`Opus 编码错误: ${error.message}`, 'error');
        }
    }

    /**
     * @override
     */
    async startRecording() {
        if (this._isRecording) {
            log('已经在录音中', 'warning');
            return;
        }

        try {
            // 初始化编码器
            if (!this.initOpusEncoder()) {
                throw new Error('Opus 编码器初始化失败');
            }

            // 获取麦克风权限
            this._mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: this.SAMPLE_RATE,
                    channelCount: this.CHANNELS
                }
            });

            const audioContext = this._getAudioContext();
            
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
            }

            // 创建音频处理器
            this._audioProcessor = await this._createAudioProcessor();
            
            // 连接音频源
            this._audioSource = audioContext.createMediaStreamSource(this._mediaStream);
            this._audioSource.connect(this._audioProcessor);

            // 重置缓冲区
            this._pcmDataBuffer = new Int16Array();
            this._isRecording = true;

            // 发送开始录音消息
            await this.sendListenStart('auto');

            // 启动 AudioWorklet
            if (this._audioProcessor.port) {
                this._audioProcessor.port.postMessage({ command: 'start' });
            }

            log('开始录音', 'success');

        } catch (error) {
            log(`录音启动失败: ${error.message}`, 'error');
            this._isRecording = false;
            throw error;
        }
    }

    /**
     * @override
     */
    async stopRecording() {
        if (!this._isRecording) {
            return;
        }

        this._isRecording = false;

        // 停止 AudioWorklet
        if (this._audioProcessor && this._audioProcessor.port) {
            this._audioProcessor.port.postMessage({ command: 'stop' });
        }

        // 编码剩余数据
        if (this._pcmDataBuffer.length > 0) {
            const paddedBuffer = new Int16Array(this.FRAME_SIZE);
            paddedBuffer.set(this._pcmDataBuffer);
            this._encodeAndSend(paddedBuffer);
            this._pcmDataBuffer = new Int16Array();
        }

        // 发送停止录音消息
        try {
            await this.sendListenStop('auto');
        } catch (e) {
            log(`发送停止消息失败: ${e.message}`, 'warning');
        }

        // 断开音频连接
        if (this._audioProcessor) {
            this._audioProcessor.disconnect();
            this._audioProcessor = null;
        }
        
        if (this._audioSource) {
            this._audioSource.disconnect();
            this._audioSource = null;
        }

        // 停止媒体流
        if (this._mediaStream) {
            this._mediaStream.getTracks().forEach(track => track.stop());
            this._mediaStream = null;
        }

        log('停止录音', 'success');
    }

    /**
     * 获取录音状态
     * @returns {boolean}
     */
    isRecording() {
        return this._isRecording;
    }
}

export default WebSocketManager;

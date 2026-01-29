// WebSocket消息处理模块
import { log } from '../../utils/logger.js';
import { addMessage } from '../../ui/dom-helper.js';
import { webSocketConnect } from './ota-connector.js';
import { getConfig, saveConnectionUrls } from '../../config/manager.js';
import { getAudioPlayer } from '../audio/player.js';
import { getAudioRecorder } from '../audio/recorder.js';
import { getMcpTools, executeMcpTool, setWebSocket as setMcpWebSocket } from '../mcp/tools.js';

// WebSocket处理器类
export class WebSocketHandler {
    constructor() {
        this.websocket = null;
        this.onConnectionStateChange = null;
        this.onRecordButtonStateChange = null;
        this.onSessionStateChange = null;
        this.onSessionEmotionChange = null;
        this.currentSessionId = null;
        this.isRemoteSpeaking = false;
        
        // 延迟计算相关
        this.waitingForFirstAudio = false;  // 是否等待第一帧音频
        this.lastAudioSentTimeSnapshot = 0;  // 收到stt时快照的最后音频发送时间
    }

    // 发送hello握手消息
    async sendHelloMessage() {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return false;

        try {
            const config = getConfig();

            const helloMessage = {
                type: 'hello',
                device_id: config.deviceId,
                device_name: config.deviceName,
                device_mac: config.deviceMac,
                token: config.token,
                features: {
                    mcp: true
                }
            };

            log('发送hello握手消息', 'info');
            this.websocket.send(JSON.stringify(helloMessage));

            return new Promise(resolve => {
                const timeout = setTimeout(() => {
                    log('等待hello响应超时', 'error');
                    log('提示: 请尝试点击"测试认证"按钮进行连接排查', 'info');
                    resolve(false);
                }, 5000);

                const onMessageHandler = (event) => {
                    try {
                        const response = JSON.parse(event.data);
                        if (response.type === 'hello' && response.session_id) {
                            log(`服务器握手成功，会话ID: ${response.session_id}`, 'success');
                            clearTimeout(timeout);
                            this.websocket.removeEventListener('message', onMessageHandler);
                            resolve(true);
                        }
                    } catch (e) {
                        // 忽略非JSON消息
                    }
                };

                this.websocket.addEventListener('message', onMessageHandler);
            });
        } catch (error) {
            log(`发送hello消息错误: ${error.message}`, 'error');
            return false;
        }
    }

    // 处理文本消息
    handleTextMessage(message) {
        if (message.type === 'hello') {
            log(`服务器回应：${JSON.stringify(message, null, 2)}`, 'success');
        } else if (message.type === 'tts') {
            this.handleTTSMessage(message);
        } else if (message.type === 'audio') {
            log(`收到音频控制消息: ${JSON.stringify(message)}`, 'info');
        } else if (message.type === 'stt') {
            log(`识别结果: ${message.text}`, 'info');
            addMessage(`${message.text}`, true);
            // 只使用本地 VAD 检测到的最后有声音时间（精确计算）
            const audioRecorder = getAudioRecorder();
            const lastVoiceTime = audioRecorder.getLastVoiceTime();
            // 只有 VAD 时间有效时才记录，否则不计算延迟
            this.lastAudioSentTimeSnapshot = lastVoiceTime > 0 ? lastVoiceTime : 0;
            if (lastVoiceTime > 0) {
                log(`延迟计算起点: VAD=${lastVoiceTime.toFixed(0)}ms`, 'debug');
            } else {
                log(`无法精确计算延迟: VAD 未检测到有效语音`, 'debug');
            }
            // 自动模式下不停止录音，保持持续对话
        } else if (message.type === 'llm') {
            log(`大模型回复: ${message.text}`, 'info');

            // 如果包含表情，更新sessionStatus表情
            if (message.text && /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u.test(message.text)) {
                // 提取表情符号
                const emojiMatch = message.text.match(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u);
                if (emojiMatch && this.onSessionEmotionChange) {
                    this.onSessionEmotionChange(emojiMatch[0]);
                }
            }

            // 只有当文本不仅仅是表情时，才添加到对话中
            // 移除文本中的表情后检查是否还有内容
            const textWithoutEmoji = message.text ? message.text.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim() : '';
            if (textWithoutEmoji) {
                addMessage(message.text);
            }
        } else if (message.type === 'mcp') {
            this.handleMCPMessage(message);
        } else {
            log(`未知消息类型: ${message.type}`, 'info');
            addMessage(JSON.stringify(message, null, 2));
        }
    }

    // 处理TTS消息
    handleTTSMessage(message) {
        if (message.state === 'start') {
            log('服务器开始发送语音', 'info');
            this.currentSessionId = message.session_id;
            this.isRemoteSpeaking = true;
            this.waitingForFirstAudio = true;  // 等待第一帧音频来计算延迟
            if (this.onSessionStateChange) {
                this.onSessionStateChange(true);
            }
        } else if (message.state === 'sentence_start') {
            log(`服务器发送语音段: ${message.text}`, 'info');
            if (message.text) {
                addMessage(message.text);
            }
        } else if (message.state === 'sentence_end') {
            log(`语音段结束: ${message.text}`, 'info');
        } else if (message.state === 'stop') {
            log('服务器语音传输结束，清空所有音频缓冲', 'info');

            // 清空所有音频缓冲并停止播放
            const audioPlayer = getAudioPlayer();
            audioPlayer.clearAllAudio();

            this.isRemoteSpeaking = false;
            if (this.onRecordButtonStateChange) {
                this.onRecordButtonStateChange(false);
            }
            if (this.onSessionStateChange) {
                this.onSessionStateChange(false);
            }
        }
    }

    // 处理MCP消息
    handleMCPMessage(message) {
        const payload = message.payload || {};
        log(`服务器下发: ${JSON.stringify(message)}`, 'info');

        if (payload.method === 'tools/list') {
            const tools = getMcpTools();

            const replyMessage = JSON.stringify({
                "session_id": message.session_id || "",
                "type": "mcp",
                "payload": {
                    "jsonrpc": "2.0",
                    "id": payload.id,
                    "result": {
                        "tools": tools
                    }
                }
            });
            log(`客户端上报: ${replyMessage}`, 'info');
            this.websocket.send(replyMessage);
            log(`回复MCP工具列表: ${tools.length} 个工具`, 'info');

        } else if (payload.method === 'tools/call') {
            const toolName = payload.params?.name;
            const toolArgs = payload.params?.arguments;

            log(`调用工具: ${toolName} 参数: ${JSON.stringify(toolArgs)}`, 'info');

            const result = executeMcpTool(toolName, toolArgs);

            const replyMessage = JSON.stringify({
                "session_id": message.session_id || "",
                "type": "mcp",
                "payload": {
                    "jsonrpc": "2.0",
                    "id": payload.id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": JSON.stringify(result)
                            }
                        ],
                        "isError": false
                    }
                }
            });

            log(`客户端上报: ${replyMessage}`, 'info');
            this.websocket.send(replyMessage);
        } else if (payload.method === 'initialize') {
            log(`收到工具初始化请求: ${JSON.stringify(payload.params)}`, 'info');
        } else {
            log(`未知的MCP方法: ${payload.method}`, 'warning');
        }
    }

    // 处理二进制消息
    async handleBinaryMessage(data) {
        try {
            let arrayBuffer;
            if (data instanceof ArrayBuffer) {
                arrayBuffer = data;
                log(`收到ArrayBuffer音频数据，大小: ${data.byteLength}字节`, 'debug');
            } else if (data instanceof Blob) {
                arrayBuffer = await data.arrayBuffer();
                log(`收到Blob音频数据，大小: ${arrayBuffer.byteLength}字节`, 'debug');
            } else {
                log(`收到未知类型的二进制数据: ${typeof data}`, 'warning');
                return;
            }

            // 计算端到端延迟（第一帧音频到达时）
            // 延迟 = 收到第一帧回复音频的时间 - 本地VAD检测到的最后有声时间
            if (this.waitingForFirstAudio) {
                this.waitingForFirstAudio = false;
                if (this.lastAudioSentTimeSnapshot > 0) {
                    const latency = (performance.now() - this.lastAudioSentTimeSnapshot) / 1000;  // 转换为秒
                    this.updateLatencyDisplay(latency);
                    log(`端到端延迟: ${latency.toFixed(2)}秒 (用户停止说话 → 首帧回复)`, 'info');
                } else {
                    // VAD 未检测到有效语音，显示占位符
                    this.updateLatencyDisplay(null);
                    log(`端到端延迟: 无法计算（VAD未检测到有效语音）`, 'info');
                }
            }

            const opusData = new Uint8Array(arrayBuffer);
            const audioPlayer = getAudioPlayer();
            audioPlayer.enqueueAudioData(opusData);
        } catch (error) {
            log(`处理二进制消息出错: ${error.message}`, 'error');
        }
    }

    // 更新延迟显示
    updateLatencyDisplay(latency) {
        const latencyValue = document.getElementById('latencyValue');
        if (latencyValue) {
            if (latency === null) {
                // 无法计算时显示占位符
                latencyValue.textContent = '--';
                latencyValue.style.color = '#999';  // 灰色
            } else {
                latencyValue.textContent = `${latency.toFixed(2)}s`;
                // 根据延迟值改变颜色
                if (latency < 1) {
                    latencyValue.style.color = '#4caf50';  // 绿色 - 优秀
                } else if (latency < 2) {
                    latencyValue.style.color = '#ff9800';  // 橙色 - 一般
                } else {
                    latencyValue.style.color = '#f44336';  // 红色 - 较慢
                }
            }
        }
    }

    // 连接WebSocket服务器
    async connect() {
        const config = getConfig();
        log('正在检查OTA状态...', 'info');
        saveConnectionUrls();

        try {
            const otaUrl = document.getElementById('otaUrl').value.trim();
            const ws = await webSocketConnect(otaUrl, config);
            if (ws === undefined) {
                return false;
            }
            this.websocket = ws;

            // 设置接收二进制数据的类型为ArrayBuffer
            this.websocket.binaryType = 'arraybuffer';

            // 设置 MCP 模块的 WebSocket 实例
            setMcpWebSocket(this.websocket);

            // 设置录音器的WebSocket
            const audioRecorder = getAudioRecorder();
            audioRecorder.setWebSocket(this.websocket);

            this.setupEventHandlers();

            return true;
        } catch (error) {
            log(`连接错误: ${error.message}`, 'error');
            if (this.onConnectionStateChange) {
                this.onConnectionStateChange(false);
            }
            return false;
        }
    }

    // 设置事件处理器
    setupEventHandlers() {
        this.websocket.onopen = async () => {
            const url = document.getElementById('serverUrl').value;
            log(`已连接到服务器: ${url}`, 'success');

            if (this.onConnectionStateChange) {
                this.onConnectionStateChange(true);
            }

            // 连接成功后，默认状态为聆听中
            this.isRemoteSpeaking = false;
            if (this.onSessionStateChange) {
                this.onSessionStateChange(false);
            }

            await this.sendHelloMessage();
        };

        this.websocket.onclose = () => {
            log('已断开连接', 'info');

            if (this.onConnectionStateChange) {
                this.onConnectionStateChange(false);
            }

            const audioRecorder = getAudioRecorder();
            audioRecorder.stop();
        };

        this.websocket.onerror = (error) => {
            log(`WebSocket错误: ${error.message || '未知错误'}`, 'error');

            if (this.onConnectionStateChange) {
                this.onConnectionStateChange(false);
            }
        };

        this.websocket.onmessage = (event) => {
            try {
                if (typeof event.data === 'string') {
                    const message = JSON.parse(event.data);
                    this.handleTextMessage(message);
                } else {
                    this.handleBinaryMessage(event.data);
                }
            } catch (error) {
                log(`WebSocket消息处理错误: ${error.message}`, 'error');
                if (typeof event.data === 'string') {
                    addMessage(event.data);
                }
            }
        };
    }

    // 断开连接
    disconnect() {
        if (!this.websocket) return;

        this.websocket.close();
        const audioRecorder = getAudioRecorder();
        audioRecorder.stop();
    }

    // 发送文本消息
    sendTextMessage(text) {
        if (text === '' || !this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            return false;
        }

        try {
            // 如果对方正在说话，先发送打断消息
            if (this.isRemoteSpeaking && this.currentSessionId) {
                const abortMessage = {
                    session_id: this.currentSessionId,
                    type: 'abort',
                    reason: 'wake_word_detected'
                };
                this.websocket.send(JSON.stringify(abortMessage));
                log('发送打断消息', 'info');
            }

            const listenMessage = {
                type: 'listen',
                mode: 'manual',
                state: 'detect',
                text: text
            };

            this.websocket.send(JSON.stringify(listenMessage));
            log(`发送文本消息: ${text}`, 'info');

            return true;
        } catch (error) {
            log(`发送消息错误: ${error.message}`, 'error');
            return false;
        }
    }

    // 获取WebSocket实例
    getWebSocket() {
        return this.websocket;
    }

    // 检查是否已连接
    isConnected() {
        return this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }
}

// 创建单例
let wsHandlerInstance = null;

export function getWebSocketHandler() {
    if (!wsHandlerInstance) {
        wsHandlerInstance = new WebSocketHandler();
    }
    return wsHandlerInstance;
}

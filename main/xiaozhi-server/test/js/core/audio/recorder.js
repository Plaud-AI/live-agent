// 音频录制模块
import { log } from '../../utils/logger.js';
import { initOpusEncoder } from './opus-codec.js';
import { getAudioPlayer } from './player.js';

// 音频录制器类
export class AudioRecorder {
    constructor() {
        this.isRecording = false;
        this.audioContext = null;
        this.analyser = null;
        this.audioProcessor = null;
        this.audioProcessorType = null;
        this.audioSource = null;
        this.opusEncoder = null;
        this.pcmDataBuffer = new Int16Array();
        this.audioBuffers = [];
        this.totalAudioSize = 0;
        this.visualizationRequest = null;
        this.recordingTimer = null;
        this.websocket = null;
        
        // 录音模式: 'manual' 或 'auto'
        this.recordingMode = 'manual';
        
        // AudioWorklet 是否已注册
        this.workletRegistered = false;
        
        // 最后一帧音频发送时间（用于计算端到端延迟）
        this.lastAudioSentTime = 0;
        
        // 本地 VAD 检测（用于精确捕获用户停止说话时刻）
        this.vadSilenceThreshold = 500;    // 静音阈值（PCM 振幅，0-32767）
        this.vadSilenceDuration = 300;     // 静音持续时间阈值（毫秒）
        this.vadIsSpeaking = false;        // 当前是否在说话
        this.vadSilenceStartTime = 0;      // 静音开始时间
        this.vadLastVoiceTime = 0;         // 最后一次检测到有声音的时间（用于延迟计算）

        // 回调函数
        this.onRecordingStart = null;
        this.onRecordingStop = null;
        this.onVisualizerUpdate = null;
    }
    
    // 设置录音模式
    setRecordingMode(mode) {
        this.recordingMode = mode;
        log(`录音模式已切换为: ${mode === 'auto' ? '自动(VAD)' : '手动'}`, 'info');
    }
    
    // 获取当前录音模式
    getRecordingMode() {
        return this.recordingMode;
    }
    
    // 获取最后一帧音频发送时间
    getLastAudioSentTime() {
        return this.lastAudioSentTime;
    }
    
    // 获取本地 VAD 检测到的最后有声音时间
    getLastVoiceTime() {
        return this.vadLastVoiceTime;
    }
    
    // 重置延迟计时（开始新一轮对话时调用）
    resetLatencyTimer() {
        this.lastAudioSentTime = 0;
        this.vadLastVoiceTime = 0;
        this.vadIsSpeaking = false;
        this.vadSilenceStartTime = 0;
    }

    // 设置WebSocket实例
    setWebSocket(ws) {
        this.websocket = ws;
    }

    // 获取AudioContext实例
    getAudioContext() {
        const audioPlayer = getAudioPlayer();
        return audioPlayer.getAudioContext();
    }

    // 初始化编码器
    initEncoder() {
        if (!this.opusEncoder) {
            this.opusEncoder = initOpusEncoder();
        }
        return this.opusEncoder;
    }

    // PCM处理器代码
    getAudioProcessorCode() {
        return `
            class AudioRecorderProcessor extends AudioWorkletProcessor {
                constructor() {
                    super();
                    this.buffers = [];
                    this.frameSize = 960;
                    this.buffer = new Int16Array(this.frameSize);
                    this.bufferIndex = 0;
                    this.isRecording = false;

                    this.port.onmessage = (event) => {
                        if (event.data.command === 'start') {
                            this.isRecording = true;
                            this.port.postMessage({ type: 'status', status: 'started' });
                        } else if (event.data.command === 'stop') {
                            this.isRecording = false;

                            if (this.bufferIndex > 0) {
                                const finalBuffer = this.buffer.slice(0, this.bufferIndex);
                                this.port.postMessage({
                                    type: 'buffer',
                                    buffer: finalBuffer
                                });
                                this.bufferIndex = 0;
                            }

                            this.port.postMessage({ type: 'status', status: 'stopped' });
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
    }

    // 创建音频处理器
    async createAudioProcessor() {
        this.audioContext = this.getAudioContext();

        try {
            if (this.audioContext.audioWorklet) {
                // 只在第一次时注册 AudioWorklet
                if (!this.workletRegistered) {
                    const blob = new Blob([this.getAudioProcessorCode()], { type: 'application/javascript' });
                    const url = URL.createObjectURL(blob);
                    await this.audioContext.audioWorklet.addModule(url);
                    URL.revokeObjectURL(url);
                    this.workletRegistered = true;
                    log('AudioWorklet 模块已注册', 'success');
                }

                const audioProcessor = new AudioWorkletNode(this.audioContext, 'audio-recorder-processor');

                audioProcessor.port.onmessage = (event) => {
                    if (event.data.type === 'buffer') {
                        this.processPCMBuffer(event.data.buffer);
                    }
                };

                log('使用AudioWorklet处理音频', 'success');

                const silent = this.audioContext.createGain();
                silent.gain.value = 0;
                audioProcessor.connect(silent);
                silent.connect(this.audioContext.destination);
                return { node: audioProcessor, type: 'worklet' };
            } else {
                log('AudioWorklet不可用，使用ScriptProcessorNode作为回退方案', 'warning');
                return this.createScriptProcessor();
            }
        } catch (error) {
            log(`创建音频处理器失败: ${error.message}，尝试回退方案`, 'error');
            return this.createScriptProcessor();
        }
    }

    // 创建ScriptProcessor作为回退
    createScriptProcessor() {
        try {
            const frameSize = 4096;
            const scriptProcessor = this.audioContext.createScriptProcessor(frameSize, 1, 1);

            scriptProcessor.onaudioprocess = (event) => {
                if (!this.isRecording) return;

                const input = event.inputBuffer.getChannelData(0);
                const buffer = new Int16Array(input.length);

                for (let i = 0; i < input.length; i++) {
                    buffer[i] = Math.max(-32768, Math.min(32767, Math.floor(input[i] * 32767)));
                }

                this.processPCMBuffer(buffer);
            };

            const silent = this.audioContext.createGain();
            silent.gain.value = 0;
            scriptProcessor.connect(silent);
            silent.connect(this.audioContext.destination);

            log('使用ScriptProcessorNode作为回退方案成功', 'warning');
            return { node: scriptProcessor, type: 'processor' };
        } catch (fallbackError) {
            log(`回退方案也失败: ${fallbackError.message}`, 'error');
            return null;
        }
    }

    // 处理PCM缓冲数据
    processPCMBuffer(buffer) {
        if (!this.isRecording) return;

        // 本地 VAD 检测：计算当前帧的音量（取绝对值最大值）
        let maxAmplitude = 0;
        for (let i = 0; i < buffer.length; i++) {
            const abs = Math.abs(buffer[i]);
            if (abs > maxAmplitude) maxAmplitude = abs;
        }
        
        const now = performance.now();
        const hasVoice = maxAmplitude > this.vadSilenceThreshold;
        
        if (hasVoice) {
            // 检测到声音
            this.vadIsSpeaking = true;
            this.vadSilenceStartTime = 0;
            this.vadLastVoiceTime = now;  // 更新最后有声音的时间
        } else if (this.vadIsSpeaking) {
            // 之前在说话，现在静音了
            if (this.vadSilenceStartTime === 0) {
                // 静音刚开始
                this.vadSilenceStartTime = now;
            } else if (now - this.vadSilenceStartTime > this.vadSilenceDuration) {
                // 静音持续超过阈值，判定为停止说话
                this.vadIsSpeaking = false;
                log(`本地VAD: 检测到用户停止说话，最后有声时间距今 ${(now - this.vadLastVoiceTime).toFixed(0)}ms`, 'debug');
            }
        }

        const newBuffer = new Int16Array(this.pcmDataBuffer.length + buffer.length);
        newBuffer.set(this.pcmDataBuffer);
        newBuffer.set(buffer, this.pcmDataBuffer.length);
        this.pcmDataBuffer = newBuffer;

        const samplesPerFrame = 960;

        while (this.pcmDataBuffer.length >= samplesPerFrame) {
            const frameData = this.pcmDataBuffer.slice(0, samplesPerFrame);
            this.pcmDataBuffer = this.pcmDataBuffer.slice(samplesPerFrame);

            this.encodeAndSendOpus(frameData);
        }
    }

    // 编码并发送Opus数据
    encodeAndSendOpus(pcmData = null) {
        if (!this.opusEncoder) {
            log('Opus编码器未初始化', 'error');
            return;
        }

        try {
            if (pcmData) {
                const opusData = this.opusEncoder.encode(pcmData);

                if (opusData && opusData.length > 0) {
                    this.audioBuffers.push(opusData.buffer);
                    this.totalAudioSize += opusData.length;

                    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                        try {
                            this.websocket.send(opusData.buffer);
                            // 记录最后一帧发送时间（用于计算端到端延迟）
                            this.lastAudioSentTime = performance.now();
                            log(`发送Opus帧，大小：${opusData.length}字节`, 'debug');
                        } catch (error) {
                            log(`WebSocket发送错误: ${error.message}`, 'error');
                        }
                    }
                } else {
                    log('Opus编码失败，无有效数据返回', 'error');
                }
            } else {
                if (this.pcmDataBuffer.length > 0) {
                    const samplesPerFrame = 960;
                    if (this.pcmDataBuffer.length < samplesPerFrame) {
                        const paddedBuffer = new Int16Array(samplesPerFrame);
                        paddedBuffer.set(this.pcmDataBuffer);
                        this.encodeAndSendOpus(paddedBuffer);
                    } else {
                        this.encodeAndSendOpus(this.pcmDataBuffer.slice(0, samplesPerFrame));
                    }
                    this.pcmDataBuffer = new Int16Array(0);
                }
            }
        } catch (error) {
            log(`Opus编码错误: ${error.message}`, 'error');
        }
    }

    // 开始录音
    async start() {
        if (this.isRecording) return false;

        try {
            // 检查是否有WebSocketHandler实例
            const { getWebSocketHandler } = await import('../network/websocket.js');
            const wsHandler = getWebSocketHandler();

            // 如果机器正在说话，发送打断消息
            if (wsHandler && wsHandler.isRemoteSpeaking && wsHandler.currentSessionId) {
                const abortMessage = {
                    session_id: wsHandler.currentSessionId,
                    type: 'abort',
                    reason: 'wake_word_detected'
                };

                if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                    this.websocket.send(JSON.stringify(abortMessage));
                    log('发送打断消息', 'info');
                }
            }

            if (!this.initEncoder()) {
                log('无法启动录音: Opus编码器初始化失败', 'error');
                return false;
            }

            log('请至少录制1-2秒钟的音频，确保采集到足够数据', 'info');

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000,
                    channelCount: 1
                }
            });

            this.audioContext = this.getAudioContext();

            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }

            const processorResult = await this.createAudioProcessor();
            if (!processorResult) {
                log('无法创建音频处理器', 'error');
                return false;
            }

            this.audioProcessor = processorResult.node;
            this.audioProcessorType = processorResult.type;

            this.audioSource = this.audioContext.createMediaStreamSource(stream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;

            this.audioSource.connect(this.analyser);
            this.audioSource.connect(this.audioProcessor);

            this.pcmDataBuffer = new Int16Array();
            this.audioBuffers = [];
            this.totalAudioSize = 0;
            this.isRecording = true;

            if (this.audioProcessorType === 'worklet' && this.audioProcessor.port) {
                this.audioProcessor.port.postMessage({ command: 'start' });
            }

            // 发送监听开始消息
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                const listenMessage = {
                    type: 'listen',
                    mode: this.recordingMode,
                    state: 'start'
                };

                log(`发送录音开始消息: ${JSON.stringify(listenMessage)}`, 'info');
                this.websocket.send(JSON.stringify(listenMessage));
            } else {
                log('WebSocket未连接，无法发送开始消息', 'error');
                return false;
            }

            // 开始可视化
            if (this.onVisualizerUpdate) {
                const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
                this.startVisualization(dataArray);
            }

            // 启动录音计时器
            let recordingSeconds = 0;
            this.recordingTimer = setInterval(() => {
                recordingSeconds += 0.1;
                if (this.onRecordingStart) {
                    this.onRecordingStart(recordingSeconds);
                }
            }, 100);

            log('开始PCM直接录音', 'success');
            return true;
        } catch (error) {
            log(`直接录音启动错误: ${error.message}`, 'error');
            this.isRecording = false;
            return false;
        }
    }

    // 开始可视化
    startVisualization(dataArray) {
        const draw = () => {
            this.visualizationRequest = requestAnimationFrame(() => draw());

            if (!this.isRecording) return;

            this.analyser.getByteFrequencyData(dataArray);

            if (this.onVisualizerUpdate) {
                this.onVisualizerUpdate(dataArray);
            }
        };
        draw();
    }

    // 停止录音
    stop() {
        if (!this.isRecording) return false;

        try {
            this.isRecording = false;

            if (this.audioProcessor) {
                if (this.audioProcessorType === 'worklet' && this.audioProcessor.port) {
                    this.audioProcessor.port.postMessage({ command: 'stop' });
                }

                this.audioProcessor.disconnect();
                this.audioProcessor = null;
            }

            if (this.audioSource) {
                this.audioSource.disconnect();
                this.audioSource = null;
            }

            if (this.visualizationRequest) {
                cancelAnimationFrame(this.visualizationRequest);
                this.visualizationRequest = null;
            }

            if (this.recordingTimer) {
                clearInterval(this.recordingTimer);
                this.recordingTimer = null;
            }

            // 编码并发送剩余的数据
            this.encodeAndSendOpus();

            // 发送结束信号
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                const emptyOpusFrame = new Uint8Array(0);
                this.websocket.send(emptyOpusFrame);

                const stopMessage = {
                    type: 'listen',
                    mode: this.recordingMode,
                    state: 'stop'
                };

                this.websocket.send(JSON.stringify(stopMessage));
                log('已发送录音停止信号', 'info');
            }

            if (this.onRecordingStop) {
                this.onRecordingStop();
            }

            log('停止PCM直接录音', 'success');
            return true;
        } catch (error) {
            log(`直接录音停止错误: ${error.message}`, 'error');
            return false;
        }
    }

    // 获取分析器
    getAnalyser() {
        return this.analyser;
    }
}

// 创建单例
let audioRecorderInstance = null;

export function getAudioRecorder() {
    if (!audioRecorderInstance) {
        audioRecorderInstance = new AudioRecorder();
    }
    return audioRecorderInstance;
}

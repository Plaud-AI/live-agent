import BlockingQueue from './utils/BlockingQueue.js';
import { log } from './utils/logger.js';

// 音频流播放上下文类
export class StreamingContext {
    constructor(opusDecoder, audioContext, sampleRate, channels, minAudioDuration) {
        this.opusDecoder = opusDecoder;
        this.audioContext = audioContext;

        // 音频参数
        this.sampleRate = sampleRate;
        this.channels = channels;
        this.minAudioDuration = minAudioDuration;

        // 初始化队列和状态
        this.queue = [];          // 已解码的PCM队列。正在播放
        this.activeQueue = new BlockingQueue(); // 已解码的PCM队列。准备播放
        this.pendingAudioBufferQueue = [];  // 待处理的缓存队列
        this.audioBufferQueue = new BlockingQueue();  // 缓存队列
        this.playing = false;     // 是否正在播放
        this.stopped = false;     // 是否已停止（用于打断）
        this.endOfStream = false; // 是否收到结束信号
        this.source = null;       // 当前音频源
        this.totalSamples = 0;    // 累积的总样本数
        this.lastPlayTime = 0;    // 上次播放的时间戳
    }

    // 缓存音频数组
    pushAudioBuffer(item) {
        this.audioBufferQueue.enqueue(...item);
    }

    // 获取需要处理缓存队列，单线程：在audioBufferQueue一直更新的状态下不会出现安全问题
    async getPendingAudioBufferQueue() {
        // 原子交换 + 清空
        [this.pendingAudioBufferQueue, this.audioBufferQueue] = [await this.audioBufferQueue.dequeue(), new BlockingQueue()];
    }

    // 获取正在播放已解码的PCM队列，单线程：在activeQueue一直更新的状态下不会出现安全问题
    async getQueue(minSamples) {
        let TepArray = [];
        const num = minSamples - this.queue.length > 0 ? minSamples - this.queue.length : 1;
        // 原子交换 + 清空
        [TepArray, this.activeQueue] = [await this.activeQueue.dequeue(num), new BlockingQueue()];
        this.queue.push(...TepArray);
    }

    // 将Int16音频数据转换为Float32音频数据
    convertInt16ToFloat32(int16Data) {
        const float32Data = new Float32Array(int16Data.length);
        for (let i = 0; i < int16Data.length; i++) {
            // 将[-32768,32767]范围转换为[-1,1]
            float32Data[i] = int16Data[i] / (int16Data[i] < 0 ? 0x8000 : 0x7FFF);
        }
        return float32Data;
    }

    // 将Opus数据解码为PCM
    async decodeOpusFrames() {
        if (!this.opusDecoder) {
            log('Opus解码器未初始化，无法解码', 'error');
            return;
        } else {
            log('Opus解码器启动', 'info');
        }

        while (true) {
            // 检查是否已停止
            if (this.stopped) {
                log('解码已停止，退出解码循环', 'info');
                return;
            }
            
            let decodedSamples = [];
            for (const frame of this.pendingAudioBufferQueue) {
                // 在循环中也检查停止标志
                if (this.stopped) break;
                
                try {
                    // 使用Opus解码器解码
                    const frameData = this.opusDecoder.decode(frame);
                    if (frameData && frameData.length > 0) {
                        // 转换为Float32
                        const floatData = this.convertInt16ToFloat32(frameData);
                        // 使用循环替代展开运算符
                        for (let i = 0; i < floatData.length; i++) {
                            decodedSamples.push(floatData[i]);
                        }
                    }
                } catch (error) {
                    log("Opus解码失败: " + error.message, 'error');
                }
            }

            // 再次检查是否已停止
            if (this.stopped) {
                log('解码已停止，退出解码循环', 'info');
                return;
            }

            if (decodedSamples.length > 0) {
                // 使用循环替代展开运算符
                for (let i = 0; i < decodedSamples.length; i++) {
                    this.activeQueue.enqueue(decodedSamples[i]);
                }
                this.totalSamples += decodedSamples.length;
            } else {
                log('没有成功解码的样本', 'warning');
            }
            
            await this.getPendingAudioBufferQueue();
            
            // 等待后再次检查
            if (this.stopped) {
                log('解码已停止，退出解码循环', 'info');
                return;
            }
        }
    }

    // 开始播放音频
    async startPlaying() {
        while (true) {
            // 检查是否已停止
            if (this.stopped) {
                log('播放已停止，退出播放循环', 'info');
                return;
            }
            
            // 如果累积了至少0.3秒的音频，开始播放
            const minSamples = this.sampleRate * this.minAudioDuration * 3;
            if (!this.playing && this.queue.length < minSamples) {
                await this.getQueue(minSamples);
            }
            
            // 再次检查是否已停止（等待队列期间可能被停止）
            if (this.stopped) {
                log('播放已停止，退出播放循环', 'info');
                return;
            }
            
            this.playing = true;
            while (this.playing && this.queue.length && !this.stopped) {
                // 创建新的音频缓冲区
                const minPlaySamples = Math.min(this.queue.length, this.sampleRate);
                const currentSamples = this.queue.splice(0, minPlaySamples);

                const audioBuffer = this.audioContext.createBuffer(this.channels, currentSamples.length, this.sampleRate);
                audioBuffer.copyToChannel(new Float32Array(currentSamples), 0);

                // 创建音频源
                this.source = this.audioContext.createBufferSource();
                this.source.buffer = audioBuffer;

                // 创建增益节点用于平滑过渡
                const gainNode = this.audioContext.createGain();

                // 应用淡入淡出效果避免爆音
                const fadeDuration = 0.02; // 20毫秒
                gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
                gainNode.gain.linearRampToValueAtTime(1, this.audioContext.currentTime + fadeDuration);

                const duration = audioBuffer.duration;
                if (duration > fadeDuration * 2) {
                    gainNode.gain.setValueAtTime(1, this.audioContext.currentTime + duration - fadeDuration);
                    gainNode.gain.linearRampToValueAtTime(0, this.audioContext.currentTime + duration);
                }

                // 连接节点并开始播放
                this.source.connect(gainNode);
                gainNode.connect(this.audioContext.destination);

                this.lastPlayTime = this.audioContext.currentTime;
                log(`开始播放 ${currentSamples.length} 个样本，约 ${(currentSamples.length / this.sampleRate).toFixed(2)} 秒`, 'info');
                
                // 使用 Promise 等待当前片段播放完成，以便能够响应停止信号
                await new Promise((resolve) => {
                    const currentSource = this.source;
                    currentSource.onended = () => {
                        resolve();
                    };
                    currentSource.start();
                    
                    // 同时检查停止信号，如果停止则立即 resolve
                    const checkStop = setInterval(() => {
                        if (this.stopped) {
                            clearInterval(checkStop);
                            try {
                                currentSource.stop();
                                currentSource.disconnect();
                            } catch (e) {}
                            resolve();
                        }
                    }, 10); // 每 10ms 检查一次
                    
                    // 播放结束后清除检查定时器
                    currentSource.onended = () => {
                        clearInterval(checkStop);
                        resolve();
                    };
                });
                
                // 播放完成后检查是否应该停止
                if (this.stopped) {
                    log('播放被中断', 'info');
                    return;
                }
            }
            
            if (this.stopped) {
                return;
            }
            await this.getQueue(minSamples);
        }
    }

    // 停止播放并清空所有缓冲区
    stop() {
        log('停止音频播放，清空缓冲区', 'info');
        
        // 设置停止标志（必须先设置，让循环能检测到）
        this.stopped = true;
        this.playing = false;
        this.endOfStream = true;
        
        // 中止所有阻塞的队列等待（关键：让 dequeue 立即返回）
        if (this.activeQueue && typeof this.activeQueue.abort === 'function') {
            this.activeQueue.abort();
        }
        if (this.audioBufferQueue && typeof this.audioBufferQueue.abort === 'function') {
            this.audioBufferQueue.abort();
        }
        
        // 停止当前正在播放的音频源
        if (this.source) {
            try {
                this.source.stop();
                this.source.disconnect();
            } catch (e) {
                // 忽略已停止的音频源错误
            }
            this.source = null;
        }
        
        // 清空所有缓冲区
        this.queue = [];
        this.pendingAudioBufferQueue = [];
        
        // 重置统计
        this.totalSamples = 0;
        this.lastPlayTime = 0;
    }
}

// 创建streamingContext实例的工厂函数
export function createStreamingContext(opusDecoder, audioContext, sampleRate, channels, minAudioDuration) {
    return new StreamingContext(opusDecoder, audioContext, sampleRate, channels, minAudioDuration);
}
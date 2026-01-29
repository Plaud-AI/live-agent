// UI控制模块
import { loadConfig, saveConfig } from '../config/manager.js';
import { getAudioPlayer } from '../core/audio/player.js';
import { getAudioRecorder } from '../core/audio/recorder.js';
import { getWebSocketHandler } from '../core/network/websocket.js';

// UI控制器类
export class UIController {
    constructor() {
        this.isEditing = false;
        this.visualizerCanvas = null;
        this.visualizerContext = null;
        this.visualizerCanvasAuto = null;
        this.visualizerContextAuto = null;
        this.audioStatsTimer = null;
        this.currentVoiceTab = 'manual'; // 'manual' 或 'auto'
    }

    // 初始化
    init() {
        console.log('UIController 初始化开始');
        
        this.visualizerCanvas = document.getElementById('audioVisualizer');
        this.visualizerCanvasAuto = document.getElementById('audioVisualizerAuto');
        
        console.log('visualizerCanvas:', this.visualizerCanvas);
        console.log('visualizerCanvasAuto:', this.visualizerCanvasAuto);
        
        if (this.visualizerCanvas) {
            this.visualizerContext = this.visualizerCanvas.getContext('2d');
        }
        if (this.visualizerCanvasAuto) {
            this.visualizerContextAuto = this.visualizerCanvasAuto.getContext('2d');
        }

        this.initVisualizer();
        this.initVisualizerAuto();
        this.initEventListeners();
        this.startAudioStatsMonitor();
        loadConfig();
        
        console.log('UIController 初始化完成');
    }

    // 初始化可视化器（手动模式）
    initVisualizer() {
        if (!this.visualizerCanvas || !this.visualizerContext) return;
        this.visualizerCanvas.width = this.visualizerCanvas.clientWidth || 300;
        this.visualizerCanvas.height = this.visualizerCanvas.clientHeight || 60;
        this.visualizerContext.fillStyle = '#fafafa';
        this.visualizerContext.fillRect(0, 0, this.visualizerCanvas.width, this.visualizerCanvas.height);
    }

    // 初始化可视化器（自动模式）
    initVisualizerAuto() {
        if (!this.visualizerCanvasAuto || !this.visualizerContextAuto) return;
        this.visualizerCanvasAuto.width = this.visualizerCanvasAuto.clientWidth || 300;
        this.visualizerCanvasAuto.height = this.visualizerCanvasAuto.clientHeight || 60;
        this.visualizerContextAuto.fillStyle = '#fafafa';
        this.visualizerContextAuto.fillRect(0, 0, this.visualizerCanvasAuto.width, this.visualizerCanvasAuto.height);
    }

    // 更新状态显示
    updateStatusDisplay(element, text) {
        element.textContent = text;
        element.removeAttribute('style');
        element.classList.remove('connected');
        if (text.includes('已连接')) {
            element.classList.add('connected');
        }
        console.log('更新状态:', text, '类列表:', element.className, '样式属性:', element.getAttribute('style'));
    }

    // 更新连接状态UI
    updateConnectionUI(isConnected) {
        const connectionStatus = document.getElementById('connectionStatus');
        const otaStatus = document.getElementById('otaStatus');
        const connectButton = document.getElementById('connectButton');
        const messageInput = document.getElementById('messageInput');
        const sendTextButton = document.getElementById('sendTextButton');
        const recordButton = document.getElementById('recordButton');
        const recordButtonAuto = document.getElementById('recordButtonAuto');

        console.log('updateConnectionUI called, isConnected:', isConnected);
        console.log('recordButtonAuto element:', recordButtonAuto);

        if (isConnected) {
            this.updateStatusDisplay(connectionStatus, '● WS已连接');
            this.updateStatusDisplay(otaStatus, '● OTA已连接');
            connectButton.textContent = '断开';
            messageInput.disabled = false;
            sendTextButton.disabled = false;
            recordButton.disabled = false;
            if (recordButtonAuto) {
                recordButtonAuto.disabled = false;
                console.log('recordButtonAuto enabled');
            } else {
                console.error('recordButtonAuto not found!');
            }
        } else {
            this.updateStatusDisplay(connectionStatus, '● WS未连接');
            this.updateStatusDisplay(otaStatus, '● OTA未连接');
            connectButton.textContent = '连接';
            messageInput.disabled = true;
            sendTextButton.disabled = true;
            recordButton.disabled = true;
            if (recordButtonAuto) {
                recordButtonAuto.disabled = true;
            }
            // 断开连接时，会话状态变为离线
            this.updateSessionStatus(null);
        }
    }

    // 更新录音按钮状态
    updateRecordButtonState(isRecording, seconds = 0) {
        const recordButton = document.getElementById('recordButton');
        const recordButtonAuto = document.getElementById('recordButtonAuto');
        const audioRecorder = getAudioRecorder();
        const isAutoMode = audioRecorder.getRecordingMode() === 'auto';
        
        // 根据当前模式更新对应的按钮
        const activeButton = isAutoMode ? recordButtonAuto : recordButton;
        const inactiveButton = isAutoMode ? recordButton : recordButtonAuto;
        
        if (isRecording) {
            if (isAutoMode) {
                activeButton.textContent = `对话中 ${seconds.toFixed(1)}秒`;
            } else {
                activeButton.textContent = `停止录音 ${seconds.toFixed(1)}秒`;
            }
            activeButton.classList.add('recording');
            inactiveButton.disabled = true;
        } else {
            // 根据模式显示不同的按钮文本
            if (isAutoMode) {
                activeButton.textContent = '开始对话';
            } else {
                activeButton.textContent = '开始录音';
            }
            // 恢复非活动按钮的文本
            recordButton.textContent = '开始录音';
            recordButtonAuto.textContent = '开始对话';
            
            activeButton.classList.remove('recording');
            inactiveButton.disabled = false;
        }
        activeButton.disabled = false;
    }

    // 更新会话状态UI
    updateSessionStatus(isSpeaking) {
        const sessionStatus = document.getElementById('sessionStatus');
        if (!sessionStatus) return;

        // 保留背景元素
        const bgHtml = '<span id="sessionStatusBg" style="position: absolute; left: 0; top: 0; bottom: 0; width: 0%; background: linear-gradient(90deg, rgba(76, 175, 80, 0.2), rgba(33, 150, 243, 0.2)); transition: width 0.15s ease-out, background 0.3s ease; z-index: 0; border-radius: 20px;"></span>';

        if (isSpeaking === null) {
            // 离线状态
            sessionStatus.innerHTML = bgHtml + '<span style="position: relative; z-index: 1;"><span class="emoji-large">😶</span> 小智离线中</span>';
            sessionStatus.className = 'status offline';
        } else if (isSpeaking) {
            // 说话中
            sessionStatus.innerHTML = bgHtml + '<span style="position: relative; z-index: 1;"><span class="emoji-large">😶</span> 小智说话中</span>';
            sessionStatus.className = 'status speaking';
        } else {
            // 聆听中
            sessionStatus.innerHTML = bgHtml + '<span style="position: relative; z-index: 1;"><span class="emoji-large">😶</span> 小智聆听中</span>';
            sessionStatus.className = 'status listening';
        }
    }

    // 更新会话表情
    updateSessionEmotion(emoji) {
        const sessionStatus = document.getElementById('sessionStatus');
        if (!sessionStatus) return;

        // 获取当前文本内容，提取非表情部分
        let currentText = sessionStatus.textContent;
        // 移除现有的表情符号
        currentText = currentText.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim();

        // 保留背景元素
        const bgHtml = '<span id="sessionStatusBg" style="position: absolute; left: 0; top: 0; bottom: 0; width: 0%; background: linear-gradient(90deg, rgba(76, 175, 80, 0.2), rgba(33, 150, 243, 0.2)); transition: width 0.15s ease-out, background 0.3s ease; z-index: 0; border-radius: 20px;"></span>';

        // 使用 innerHTML 添加带样式的表情
        sessionStatus.innerHTML = bgHtml + `<span style="position: relative; z-index: 1;"><span class="emoji-large">${emoji}</span> ${currentText}</span>`;
    }

    // 更新音频统计信息
    updateAudioStats() {
        const audioPlayer = getAudioPlayer();
        const stats = audioPlayer.getAudioStats();

        const sessionStatus = document.getElementById('sessionStatus');
        const sessionStatusBg = document.getElementById('sessionStatusBg');

        // 只在说话状态下显示背景进度
        if (sessionStatus && sessionStatus.classList.contains('speaking') && sessionStatusBg) {
            if (stats.pendingPlay > 0) {
                // 计算进度：5包=50%，10包及以上=100%
                let percentage;
                if (stats.pendingPlay >= 10) {
                    percentage = 100;
                } else {
                    percentage = (stats.pendingPlay / 10) * 100;
                }

                sessionStatusBg.style.width = `${percentage}%`;

                // 根据缓冲量改变背景颜色
                if (stats.pendingPlay < 5) {
                    // 缓冲不足：橙红色半透明
                    sessionStatusBg.style.background = 'linear-gradient(90deg, rgba(255, 152, 0, 0.25), rgba(255, 87, 34, 0.25))';
                } else if (stats.pendingPlay < 10) {
                    // 一般：黄绿色半透明
                    sessionStatusBg.style.background = 'linear-gradient(90deg, rgba(205, 220, 57, 0.25), rgba(76, 175, 80, 0.25))';
                } else {
                    // 充足：绿蓝色半透明
                    sessionStatusBg.style.background = 'linear-gradient(90deg, rgba(76, 175, 80, 0.25), rgba(33, 150, 243, 0.25))';
                }
            } else {
                // 没有缓冲，隐藏背景
                sessionStatusBg.style.width = '0%';
            }
        } else {
            // 非说话状态，隐藏背景
            if (sessionStatusBg) {
                sessionStatusBg.style.width = '0%';
            }
        }
    }

    // 启动音频统计监控
    startAudioStatsMonitor() {
        // 每100ms更新一次音频统计
        this.audioStatsTimer = setInterval(() => {
            this.updateAudioStats();
        }, 100);
    }

    // 停止音频统计监控
    stopAudioStatsMonitor() {
        if (this.audioStatsTimer) {
            clearInterval(this.audioStatsTimer);
            this.audioStatsTimer = null;
        }
    }

    // 绘制音频可视化效果
    drawVisualizer(dataArray) {
        // 根据当前模式选择对应的 canvas
        const canvas = this.currentVoiceTab === 'auto' ? this.visualizerCanvasAuto : this.visualizerCanvas;
        const context = this.currentVoiceTab === 'auto' ? this.visualizerContextAuto : this.visualizerContext;
        
        context.fillStyle = '#fafafa';
        context.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / dataArray.length) * 2.5;
        let barHeight;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
            barHeight = dataArray[i] / 2;

            // 创建渐变色：从紫色到蓝色到青色
            const hue = 200 + (barHeight / canvas.height) * 60; // 200-260度，从青色到紫色
            const saturation = 80 + (barHeight / canvas.height) * 20; // 饱和度 80-100%
            const lightness = 45 + (barHeight / canvas.height) * 15; // 亮度 45-60%

            context.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            context.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

            x += barWidth + 1;
        }
    }

    // 初始化事件监听器
    initEventListeners() {
        console.log('initEventListeners 开始');
        const wsHandler = getWebSocketHandler();
        const audioRecorder = getAudioRecorder();

        // 设置WebSocket回调
        wsHandler.onConnectionStateChange = (isConnected) => {
            this.updateConnectionUI(isConnected);
        };

        wsHandler.onRecordButtonStateChange = (isRecording) => {
            this.updateRecordButtonState(isRecording);
        };

        wsHandler.onSessionStateChange = (isSpeaking) => {
            this.updateSessionStatus(isSpeaking);
        };

        wsHandler.onSessionEmotionChange = (emoji) => {
            this.updateSessionEmotion(emoji);
        };

        // 设置录音器回调
        audioRecorder.onRecordingStart = (seconds) => {
            this.updateRecordButtonState(true, seconds);
        };

        audioRecorder.onRecordingStop = () => {
            this.updateRecordButtonState(false);
        };

        audioRecorder.onVisualizerUpdate = (dataArray) => {
            this.drawVisualizer(dataArray);
        };

        // 连接按钮
        const connectButton = document.getElementById('connectButton');
        let isConnecting = false;

        const handleConnect = async () => {
            if (isConnecting) return;

            if (wsHandler.isConnected()) {
                wsHandler.disconnect();
            } else {
                isConnecting = true;
                await wsHandler.connect();
                isConnecting = false;
            }
        };

        connectButton.addEventListener('click', handleConnect);

        // 设备配置面板编辑/确定切换
        const toggleButton = document.getElementById('toggleConfig');
        const deviceMacInput = document.getElementById('deviceMac');
        const deviceNameInput = document.getElementById('deviceName');
        const clientIdInput = document.getElementById('clientId');

        toggleButton.addEventListener('click', () => {
            this.isEditing = !this.isEditing;

            deviceMacInput.disabled = !this.isEditing;
            deviceNameInput.disabled = !this.isEditing;
            clientIdInput.disabled = !this.isEditing;

            toggleButton.textContent = this.isEditing ? '确定' : '编辑';

            if (!this.isEditing) {
                saveConfig();
            }
        });

        // 标签页切换
        const tabs = document.querySelectorAll('.tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // 如果正在录音，不允许切换标签页
                if (audioRecorder.isRecording) {
                    return;
                }
                
                tabs.forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                tab.classList.add('active');
                const tabContent = document.getElementById(`${tab.dataset.tab}Tab`);
                tabContent.classList.add('active');

                // 根据标签页设置录音模式
                if (tab.dataset.tab === 'voice') {
                    this.currentVoiceTab = 'manual';
                    audioRecorder.setRecordingMode('manual');
                    setTimeout(() => {
                        this.initVisualizer();
                    }, 50);
                } else if (tab.dataset.tab === 'voiceAuto') {
                    this.currentVoiceTab = 'auto';
                    audioRecorder.setRecordingMode('auto');
                    setTimeout(() => {
                        this.initVisualizerAuto();
                    }, 50);
                }
            });
        });

        // 发送文本消息
        const messageInput = document.getElementById('messageInput');
        const sendTextButton = document.getElementById('sendTextButton');

        const sendMessage = () => {
            const message = messageInput.value.trim();
            if (message && wsHandler.sendTextMessage(message)) {
                messageInput.value = '';
            }
        };

        sendTextButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // 手动模式录音按钮
        const recordButton = document.getElementById('recordButton');
        console.log('绑定手动模式按钮事件, element:', recordButton);
        if (recordButton) {
            recordButton.addEventListener('click', () => {
                console.log('手动模式录音按钮被点击');
                if (audioRecorder.isRecording) {
                    audioRecorder.stop();
                } else {
                    audioRecorder.setRecordingMode('manual');
                    this.currentVoiceTab = 'manual';
                    audioRecorder.start();
                }
            });
            console.log('手动模式按钮事件绑定成功');
        } else {
            console.error('recordButton 元素不存在!');
        }

        // 自动模式录音按钮
        const recordButtonAuto = document.getElementById('recordButtonAuto');
        console.log('绑定自动模式按钮事件, element:', recordButtonAuto);
        if (recordButtonAuto) {
            recordButtonAuto.addEventListener('click', () => {
                console.log('自动模式录音按钮被点击');
                if (audioRecorder.isRecording) {
                    audioRecorder.stop();
                } else {
                    audioRecorder.setRecordingMode('auto');
                    this.currentVoiceTab = 'auto';
                    audioRecorder.start();
                }
            });
            console.log('自动模式按钮事件绑定成功');
        } else {
            console.error('recordButtonAuto 元素不存在!');
        }

        // 窗口大小变化
        window.addEventListener('resize', () => {
            this.initVisualizer();
            this.initVisualizerAuto();
        });
    }
}

// 创建单例
let uiControllerInstance = null;

export function getUIController() {
    if (!uiControllerInstance) {
        uiControllerInstance = new UIController();
    }
    return uiControllerInstance;
}

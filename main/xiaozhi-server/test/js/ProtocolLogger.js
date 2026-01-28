/**
 * ProtocolLogger - 协议日志记录器
 * 
 * 用于记录和验证小智协议的消息收发，帮助调试和验证协议正确性。
 */

import { TTSState, XiaozhiMessageType } from './ConnectionManager.js';

/**
 * 日志条目类型
 */
export const LogDirection = {
    SEND: 'SEND',
    RECV: 'RECV'
};

/**
 * 日志条目结构
 * @typedef {Object} LogEntry
 * @property {number} timestamp - 时间戳
 * @property {string} direction - 方向 (SEND/RECV)
 * @property {string} type - 消息类型
 * @property {Object} data - 消息数据
 * @property {string} mode - 连接模式
 * @property {string} [rawChunk] - 原始分块数据（仅 Agora RTC 模式）
 */

/**
 * 协议日志记录器
 */
export class ProtocolLogger {
    constructor() {
        this._logs = [];
        this._listeners = [];
        this._maxLogs = 1000; // 最大日志条数
        this._enabled = true;
    }

    /**
     * 启用/禁用日志记录
     * @param {boolean} enabled 
     */
    setEnabled(enabled) {
        this._enabled = enabled;
    }

    /**
     * 是否启用
     * @returns {boolean}
     */
    isEnabled() {
        return this._enabled;
    }

    /**
     * 添加日志监听器
     * @param {Function} listener - (entry: LogEntry) => void
     */
    addListener(listener) {
        this._listeners.push(listener);
    }

    /**
     * 移除日志监听器
     * @param {Function} listener 
     */
    removeListener(listener) {
        this._listeners = this._listeners.filter(l => l !== listener);
    }

    /**
     * 记录发送的消息
     * @param {string} type - 消息类型
     * @param {Object} data - 消息数据
     * @param {string} mode - 连接模式
     * @param {string} [rawChunk] - 原始分块数据
     */
    logSend(type, data, mode = 'websocket', rawChunk = null) {
        this._log(LogDirection.SEND, type, data, mode, rawChunk);
    }

    /**
     * 记录接收的消息
     * @param {string} type - 消息类型
     * @param {Object} data - 消息数据
     * @param {string} mode - 连接模式
     * @param {string} [rawChunk] - 原始分块数据
     */
    logReceive(type, data, mode = 'websocket', rawChunk = null) {
        this._log(LogDirection.RECV, type, data, mode, rawChunk);
    }

    /**
     * 记录音频数据
     * @param {string} direction - 方向
     * @param {number} size - 数据大小（字节）
     * @param {string} mode - 连接模式
     */
    logAudio(direction, size, mode = 'websocket') {
        this._log(direction, 'audio', { size, unit: 'bytes' }, mode);
    }

    /**
     * 内部日志方法
     */
    _log(direction, type, data, mode, rawChunk = null) {
        if (!this._enabled) return;

        const entry = {
            timestamp: Date.now(),
            direction,
            type,
            data,
            mode,
            rawChunk
        };

        this._logs.push(entry);

        // 限制日志条数
        if (this._logs.length > this._maxLogs) {
            this._logs.shift();
        }

        // 通知监听器
        for (const listener of this._listeners) {
            try {
                listener(entry);
            } catch (e) {
                console.error('ProtocolLogger listener error:', e);
            }
        }
    }

    /**
     * 获取所有日志
     * @returns {LogEntry[]}
     */
    getLogs() {
        return [...this._logs];
    }

    /**
     * 获取特定类型的日志
     * @param {string} type - 消息类型
     * @returns {LogEntry[]}
     */
    getLogsByType(type) {
        return this._logs.filter(l => l.type === type);
    }

    /**
     * 清空日志
     */
    clear() {
        this._logs = [];
    }

    /**
     * 验证 TTS 状态机时序
     * @returns {Object} - { valid: boolean, errors: string[], warnings: string[] }
     */
    validateTtsStateMachine() {
        const ttsLogs = this._logs.filter(
            l => l.direction === LogDirection.RECV && l.type === XiaozhiMessageType.TTS
        );
        
        const errors = [];
        const warnings = [];
        
        if (ttsLogs.length === 0) {
            return { valid: true, errors: [], warnings: ['没有收到任何 TTS 消息'] };
        }

        let state = 'idle'; // idle -> started -> sentence_start -> sentence_end -> stopped
        let sentenceCount = 0;
        let sentenceStartText = null;

        for (let i = 0; i < ttsLogs.length; i++) {
            const log = ttsLogs[i];
            const ttsState = log.data.state;
            const text = log.data.text;

            switch (ttsState) {
                case TTSState.START:
                    if (state !== 'idle' && state !== 'stopped') {
                        errors.push(`[${i}] 非法状态转换: ${state} -> start`);
                    }
                    state = 'started';
                    sentenceCount = 0;
                    break;

                case TTSState.SENTENCE_START:
                    if (state !== 'started' && state !== 'sentence_end') {
                        errors.push(`[${i}] sentence_start 之前应为 start 或 sentence_end，当前状态: ${state}`);
                    }
                    state = 'sentence_start';
                    sentenceStartText = text;
                    sentenceCount++;
                    break;

                case TTSState.SENTENCE_END:
                    if (state !== 'sentence_start') {
                        errors.push(`[${i}] sentence_end 之前应为 sentence_start，当前状态: ${state}`);
                    }
                    // 检查文本是否匹配（可选，因为有些实现可能不完全匹配）
                    if (sentenceStartText && text && sentenceStartText !== text) {
                        warnings.push(`[${i}] sentence_end 文本与 sentence_start 不一致`);
                    }
                    state = 'sentence_end';
                    sentenceStartText = null;
                    break;

                case TTSState.STOP:
                    if (state !== 'started' && state !== 'sentence_end') {
                        warnings.push(`[${i}] stop 之前状态异常: ${state}`);
                    }
                    state = 'stopped';
                    break;

                default:
                    warnings.push(`[${i}] 未知的 TTS 状态: ${ttsState}`);
            }
        }

        // 最终状态检查
        if (state !== 'stopped' && state !== 'idle') {
            warnings.push(`TTS 状态机未正常结束，最终状态: ${state}`);
        }

        return {
            valid: errors.length === 0,
            errors,
            warnings,
            summary: {
                totalMessages: ttsLogs.length,
                sentenceCount,
                finalState: state
            }
        };
    }

    /**
     * 验证 Hello 握手
     * @returns {Object} - { valid: boolean, errors: string[] }
     */
    validateHelloHandshake() {
        const helloSent = this._logs.find(
            l => l.direction === LogDirection.SEND && l.type === XiaozhiMessageType.HELLO
        );
        const helloRecv = this._logs.find(
            l => l.direction === LogDirection.RECV && l.type === XiaozhiMessageType.HELLO
        );

        const errors = [];

        if (!helloSent) {
            errors.push('未发送 hello 消息');
        }

        if (!helloRecv) {
            errors.push('未收到 hello 响应');
        } else if (!helloRecv.data.session_id) {
            errors.push('hello 响应缺少 session_id');
        }

        // 检查时序
        if (helloSent && helloRecv && helloSent.timestamp > helloRecv.timestamp) {
            errors.push('hello 响应在发送之前收到（时序异常）');
        }

        return {
            valid: errors.length === 0,
            errors,
            sentAt: helloSent?.timestamp,
            receivedAt: helloRecv?.timestamp,
            sessionId: helloRecv?.data?.session_id
        };
    }

    /**
     * 获取对话流程统计
     * @returns {Object}
     */
    getConversationStats() {
        const stats = {
            messagesSent: 0,
            messagesReceived: 0,
            textInputs: 0,
            sttResults: 0,
            ttsStarts: 0,
            ttsStops: 0,
            aborts: 0,
            mcpCalls: 0,
            audioPacketsSent: 0,
            audioPacketsReceived: 0
        };

        for (const log of this._logs) {
            if (log.direction === LogDirection.SEND) {
                stats.messagesSent++;
                if (log.type === XiaozhiMessageType.LISTEN && log.data?.state === 'detect') {
                    stats.textInputs++;
                }
                if (log.type === XiaozhiMessageType.ABORT) {
                    stats.aborts++;
                }
                if (log.type === 'audio') {
                    stats.audioPacketsSent++;
                }
            } else {
                stats.messagesReceived++;
                if (log.type === XiaozhiMessageType.STT) {
                    stats.sttResults++;
                }
                if (log.type === XiaozhiMessageType.TTS) {
                    if (log.data?.state === TTSState.START) stats.ttsStarts++;
                    if (log.data?.state === TTSState.STOP) stats.ttsStops++;
                }
                if (log.type === XiaozhiMessageType.MCP) {
                    stats.mcpCalls++;
                }
                if (log.type === 'audio') {
                    stats.audioPacketsReceived++;
                }
            }
        }

        return stats;
    }

    /**
     * 导出日志为 JSON
     * @returns {string}
     */
    exportJson() {
        return JSON.stringify({
            exportedAt: new Date().toISOString(),
            logCount: this._logs.length,
            logs: this._logs
        }, null, 2);
    }

    /**
     * 导出日志为可读文本
     * @returns {string}
     */
    exportText() {
        const lines = [];
        lines.push(`=== 小智协议日志 (${this._logs.length} 条) ===`);
        lines.push(`导出时间: ${new Date().toISOString()}`);
        lines.push('');

        for (const log of this._logs) {
            const time = new Date(log.timestamp).toISOString().slice(11, 23);
            const dir = log.direction === LogDirection.SEND ? '>>>' : '<<<';
            const mode = log.mode === 'agora-rtc' ? '[RTC]' : '[WS]';
            
            let content = '';
            if (log.type === 'audio') {
                content = `AUDIO ${log.data.size} bytes`;
            } else {
                content = JSON.stringify(log.data);
            }
            
            lines.push(`${time} ${mode} ${dir} ${log.type.toUpperCase()}: ${content}`);
        }

        return lines.join('\n');
    }

    /**
     * 格式化单条日志为 HTML
     * @param {LogEntry} entry 
     * @returns {string}
     */
    formatEntryHtml(entry) {
        const time = new Date(entry.timestamp).toISOString().slice(11, 23);
        const dirClass = entry.direction === LogDirection.SEND ? 'send' : 'recv';
        const dirIcon = entry.direction === LogDirection.SEND ? '⬆️' : '⬇️';
        const modeLabel = entry.mode === 'agora-rtc' ? 'RTC' : 'WS';
        
        let content = '';
        if (entry.type === 'audio') {
            content = `<span class="audio-info">${entry.data.size} bytes</span>`;
        } else {
            content = `<pre>${JSON.stringify(entry.data, null, 2)}</pre>`;
        }

        return `
            <div class="protocol-log-entry ${dirClass}">
                <span class="timestamp">${time}</span>
                <span class="mode">[${modeLabel}]</span>
                <span class="direction">${dirIcon}</span>
                <span class="type">${entry.type}</span>
                <div class="content">${content}</div>
            </div>
        `;
    }
}

// 全局单例
export const protocolLogger = new ProtocolLogger();

export default ProtocolLogger;

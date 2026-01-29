"""
打断模块的核心类型定义

参考 ten-framework 的设计:
- TTSAudioEndReason (对应 InterruptReason)
- RequestState (对应 InterruptState)
- flush_id 机制 (对应 FlushRequest)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class InterruptSource(Enum):
    """
    打断触发源枚举
    
    定义了打断请求的来源，便于追踪和统计。
    设计为可扩展，后续可以添加新的触发源。
    """
    # 语音活动检测触发（用户开始说话）
    VAD = "vad"
    # 用户主动打断（如按键、手势）
    USER_ACTION = "user_action"
    # 系统打断（如超时、错误恢复）
    SYSTEM = "system"
    # API 远程打断
    API = "api"
    # 特定关键词触发
    KEYWORD = "keyword"
    # 会话结束
    SESSION_END = "session_end"
    # 未知来源（兼容性）
    UNKNOWN = "unknown"


class InterruptTarget(Enum):
    """
    打断目标枚举
    
    支持分层打断，可以选择性地打断特定组件。
    参考 ten-framework 的分层设计：ASR -> LLM -> TTS
    """
    # 语音识别
    ASR = "asr"
    # 大语言模型
    LLM = "llm"
    # 语音合成
    TTS = "tts"
    # 音频播放/输出
    AUDIO_OUTPUT = "audio_output"
    # 全部组件
    ALL = "all"


class InterruptReason(Enum):
    """
    打断原因枚举
    
    参考 ten-framework 的 TTSAudioEndReason:
    - REQUEST_END = 1 (正常结束)
    - INTERRUPTED = 2 (被打断)
    - ERROR = 3 (错误)
    """
    # 正常结束（请求完成）
    REQUEST_END = 1
    # 被打断（收到 flush 信号）
    INTERRUPTED = 2
    # 发生错误
    ERROR = 3
    # 超时
    TIMEOUT = 4
    # 用户取消
    CANCELLED = 5


class InterruptState(Enum):
    """
    请求状态枚举
    
    参考 ten-framework 的 RequestState，追踪请求的生命周期。
    """
    # 已排队等待处理
    QUEUED = "queued"
    # 正在处理中
    PROCESSING = "processing"
    # 正在完成（等待最后的数据）
    FINALIZING = "finalizing"
    # 已完成
    COMPLETED = "completed"
    # 已被打断
    INTERRUPTED = "interrupted"
    # 发生错误
    ERROR = "error"


@dataclass
class FlushRequest:
    """
    Flush（打断）请求数据结构
    
    参考 ten-framework 的 tts_flush 数据结构：
    - flush_id: 唯一标识符
    - metadata: 元数据（session_id, turn_id 等）
    """
    # 唯一标识符，用于追踪和匹配
    flush_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # 打断的目标请求 ID（可选，用于定向打断）
    target_request_id: Optional[str] = None
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 创建时间
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.flush_id:
            self.flush_id = str(uuid.uuid4())


@dataclass
class InterruptEvent:
    """
    打断事件数据结构
    
    包含打断操作的完整信息，用于事件通知和日志记录。
    """
    # 事件 ID
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # 会话 ID
    session_id: str = ""
    # 打断触发源
    source: InterruptSource = InterruptSource.UNKNOWN
    # 打断目标列表
    targets: list = field(default_factory=lambda: [InterruptTarget.ALL])
    # 打断原因
    reason: InterruptReason = InterruptReason.INTERRUPTED
    # Flush 请求信息
    flush_request: Optional[FlushRequest] = None
    # 被打断的请求 ID 列表
    interrupted_request_ids: list = field(default_factory=list)
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 事件创建时间
    timestamp: datetime = field(default_factory=datetime.now)
    # 打断是否成功
    success: bool = True
    # 错误信息（如果有）
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，便于序列化和日志记录"""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "source": self.source.value,
            "targets": [t.value for t in self.targets],
            "reason": self.reason.value,
            "flush_id": self.flush_request.flush_id if self.flush_request else None,
            "interrupted_request_ids": self.interrupted_request_ids,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class RequestContext:
    """
    请求上下文，追踪单个请求的状态
    
    参考 ten-framework 中对 request_id 的追踪机制。
    """
    # 请求 ID
    request_id: str
    # 当前状态
    state: InterruptState = InterruptState.QUEUED
    # 所属目标组件
    target: InterruptTarget = InterruptTarget.ALL
    # 创建时间
    created_at: datetime = field(default_factory=datetime.now)
    # 开始处理时间
    started_at: Optional[datetime] = None
    # 完成时间
    completed_at: Optional[datetime] = None
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 结束原因
    end_reason: Optional[InterruptReason] = None
    
    def mark_processing(self):
        """标记为处理中"""
        self.state = InterruptState.PROCESSING
        self.started_at = datetime.now()
    
    def mark_completed(self, reason: InterruptReason = InterruptReason.REQUEST_END):
        """标记为已完成"""
        self.state = InterruptState.COMPLETED
        self.completed_at = datetime.now()
        self.end_reason = reason
    
    def mark_interrupted(self):
        """标记为已打断"""
        self.state = InterruptState.INTERRUPTED
        self.completed_at = datetime.now()
        self.end_reason = InterruptReason.INTERRUPTED
    
    @property
    def duration_ms(self) -> Optional[int]:
        """计算处理时长（毫秒）"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None



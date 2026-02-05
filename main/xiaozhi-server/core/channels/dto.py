"""
通道数据传输对象

定义通道层使用的数据结构，包括：
- AudioPacket: 统一的音频数据包格式
- ChannelMessage: 统一的通道消息
- ChannelInfo: 通道元信息
"""
from dataclasses import dataclass, field
from typing import Optional, Union
from enum import Enum


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"      # 文本消息（JSON 指令）
    AUDIO = "audio"    # 音频消息（Opus 数据）


class ChannelType(Enum):
    """通道类型"""
    WEBSOCKET = "websocket"           # WebSocket 直连
    MQTT_GATEWAY = "mqtt_gateway"     # MQTT 网关转发
    WEBRTC = "webrtc"                 # WebRTC（预留）
    AGORA = "agora"                   # Agora RTC（预留）


@dataclass
class AudioPacket:
    """
    统一的音频数据包格式
    
    所有通道的音频数据都转换为此格式，屏蔽底层差异。
    
    Attributes:
        data: 原始音频数据 (Opus 编码)
        timestamp: 时间戳 (毫秒)，用于排序和同步
        sequence: 序列号，用于检测丢包和排序
    """
    data: bytes
    timestamp: int = 0
    sequence: int = 0
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __bool__(self) -> bool:
        return len(self.data) > 0


@dataclass
class ChannelMessage:
    """
    统一的通道消息
    
    封装从通道接收的消息，统一文本和音频的处理接口。
    
    Attributes:
        type: 消息类型 (TEXT/AUDIO)
        data: 消息内容 (str for TEXT, AudioPacket for AUDIO)
    """
    type: MessageType
    data: Union[str, AudioPacket]
    
    @classmethod
    def text(cls, content: str) -> "ChannelMessage":
        """创建文本消息"""
        return cls(type=MessageType.TEXT, data=content)
    
    @classmethod
    def audio(cls, packet: AudioPacket) -> "ChannelMessage":
        """创建音频消息"""
        return cls(type=MessageType.AUDIO, data=packet)
    
    @property
    def is_text(self) -> bool:
        return self.type == MessageType.TEXT
    
    @property
    def is_audio(self) -> bool:
        return self.type == MessageType.AUDIO


@dataclass
class ChannelInfo:
    """
    通道元信息
    
    记录通道连接的相关信息，用于日志、认证、路由等。
    
    Attributes:
        channel_type: 通道类型
        device_id: 设备标识
        client_id: 客户端标识
        client_ip: 客户端 IP
        session_id: 会话标识
        headers: 原始请求头
        query_params: URL 查询参数
        extra: 扩展信息（用于特定通道的额外数据）
    """
    channel_type: str
    device_id: str = ""
    client_id: Optional[str] = None
    client_ip: Optional[str] = None
    session_id: Optional[str] = None
    headers: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)  # 扩展字段，用于 WebRTC/Agora 等特殊参数
    
    def get_extra(self, key: str, default=None):
        """获取扩展信息"""
        return self.extra.get(key, default)
    
    def set_extra(self, key: str, value):
        """设置扩展信息"""
        self.extra[key] = value

"""
通道抽象层

提供统一的通道接口，屏蔽底层协议差异。

支持的通道类型：
- WebSocket 直连：用于移动端 App、浏览器
- MQTT 网关：用于 ESP32 等嵌入式设备（通过 xiaozhi-mqtt-gateway 转发）
- WebRTC：预留，用于浏览器实时音视频（标准 WebRTC 协议）
- Agora：预留，用于 Agora SDK 接入

Usage:
    from core.channels import ChannelFactory, BaseChannel, AudioPacket
    
    # 从 WebSocket 创建通道（自动识别类型）
    channel = ChannelFactory.create_from_websocket(websocket)
    
    # 接收消息
    async for msg in channel.receive_messages():
        if msg.is_text:
            handle_text(msg.data)
        elif msg.is_audio:
            handle_audio(msg.data)
    
    # 发送音频
    packet = AudioPacket(data=opus_data, timestamp=timestamp)
    await channel.send_audio(packet)
    
    # 发送文本
    await channel.send_json({"type": "tts", "state": "start"})
"""

from core.channels.dto import (
    AudioPacket,
    ChannelMessage,
    ChannelInfo,
    MessageType,
    ChannelType,
)
from core.channels.base import BaseChannel
from core.channels.factory import ChannelFactory
from core.channels.websocket_channel import WebSocketChannel
from core.channels.mqtt_gateway_channel import MqttGatewayChannel

# RTC 通道预留
from core.channels.rtc_channel import RTCChannelBase, WebRTCChannel, AgoraChannel

__all__ = [
    # 数据对象
    "AudioPacket",
    "ChannelMessage", 
    "ChannelInfo",
    "MessageType",
    "ChannelType",
    # 基类
    "BaseChannel",
    "RTCChannelBase",
    # 实现类
    "WebSocketChannel",
    "MqttGatewayChannel",
    "WebRTCChannel",
    "AgoraChannel",
    # 工厂
    "ChannelFactory",
]

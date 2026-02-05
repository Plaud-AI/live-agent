"""
通道抽象基类

定义所有通道必须实现的接口，包括：
- 消息接收（异步迭代器）
- 音频发送
- 文本发送
- 连接管理

支持的通道类型：
- WebSocket 直连
- MQTT 网关转发
- WebRTC（预留）
- Agora RTC（预留）
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from core.channels.dto import AudioPacket, ChannelMessage, ChannelInfo

TAG = __name__


class BaseChannel(ABC):
    """
    通道抽象基类
    
    所有通道实现必须继承此类并实现抽象方法。
    通道负责：
    1. 底层协议的封装/解封装
    2. 音频数据的格式转换
    3. 连接生命周期管理
    
    Usage:
        channel = SomeChannel(websocket, info)
        async for msg in channel.receive_messages():
            if msg.is_text:
                handle_text(msg.data)
            elif msg.is_audio:
                handle_audio(msg.data)
    """
    
    def __init__(self, info: ChannelInfo):
        """
        初始化通道
        
        Args:
            info: 通道元信息
        """
        self.info = info
        self._closed = False
        self._logger = logging.getLogger(TAG)
    
    # ==================== 属性 ====================
    
    @property
    def is_closed(self) -> bool:
        """连接是否已关闭"""
        return self._closed
    
    @property
    def channel_type(self) -> str:
        """通道类型标识"""
        return self.info.channel_type
    
    @property
    def device_id(self) -> str:
        """设备ID"""
        return self.info.device_id
    
    @property
    def client_id(self) -> Optional[str]:
        """客户端ID"""
        return self.info.client_id
    
    @property
    def client_ip(self) -> Optional[str]:
        """客户端IP"""
        return self.info.client_ip
    
    # ==================== 抽象方法（子类必须实现） ====================
    
    @abstractmethod
    async def receive_messages(self) -> AsyncIterator[ChannelMessage]:
        """
        异步迭代接收消息
        
        子类实现时需要：
        1. 从底层连接读取原始数据
        2. 转换为统一的 ChannelMessage 格式
        3. 处理连接关闭和异常
        
        Yields:
            ChannelMessage: 统一格式的消息对象
            
        Example:
            async for msg in channel.receive_messages():
                if msg.is_text:
                    print(f"收到文本: {msg.data}")
                elif msg.is_audio:
                    print(f"收到音频: {len(msg.data)} bytes")
        """
        pass
    
    @abstractmethod
    async def send_audio(self, packet: AudioPacket) -> None:
        """
        发送音频数据包
        
        子类实现时需要：
        1. 根据通道类型添加必要的头部/封装
        2. 处理发送失败和重试逻辑
        
        Args:
            packet: 音频数据包
            
        Raises:
            ConnectionError: 连接已关闭
            Exception: 发送失败
        """
        pass
    
    @abstractmethod
    async def send_text(self, message: str) -> None:
        """
        发送文本消息
        
        Args:
            message: 文本消息内容（通常是 JSON 字符串）
            
        Raises:
            ConnectionError: 连接已关闭
            Exception: 发送失败
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        关闭通道连接
        
        子类实现时需要：
        1. 清理资源
        2. 关闭底层连接
        3. 设置 _closed 标志
        """
        pass
    
    # ==================== 通用方法（子类可直接使用或覆盖） ====================
    
    async def send_json(self, data: dict) -> None:
        """
        发送 JSON 对象
        
        Args:
            data: 字典对象，将被序列化为 JSON 字符串
        """
        await self.send_text(json.dumps(data, ensure_ascii=False))
    
    def get_extra(self, key: str, default=None):
        """
        获取通道扩展信息
        
        用于存储特定通道的额外数据，如：
        - WebRTC: ICE candidates, SDP
        - Agora: channel name, token
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            扩展信息值
        """
        return self.info.get_extra(key, default)
    
    def set_extra(self, key: str, value) -> None:
        """
        设置通道扩展信息
        
        Args:
            key: 键名
            value: 值
        """
        self.info.set_extra(key, value)
    
    # ==================== 生命周期钩子（子类可选覆盖） ====================
    
    async def on_connect(self) -> None:
        """
        连接建立后的回调
        
        子类可覆盖此方法执行初始化逻辑，如：
        - WebRTC: 完成 ICE 协商
        - Agora: 加入频道
        """
        pass
    
    async def on_disconnect(self) -> None:
        """
        连接断开前的回调
        
        子类可覆盖此方法执行清理逻辑
        """
        pass
    
    # ==================== 魔术方法 ====================
    
    def __repr__(self) -> str:
        status = "closed" if self._closed else "open"
        return f"<{self.__class__.__name__} type={self.channel_type} device={self.device_id} status={status}>"
    
    async def __aenter__(self):
        """支持 async with 语法"""
        await self.on_connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """支持 async with 语法"""
        await self.on_disconnect()
        await self.close()
        return False

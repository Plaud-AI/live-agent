"""
WebSocket 直连通道实现

用于移动端 App、浏览器等直接 WebSocket 连接的客户端。
音频格式：纯 Opus 数据包（无头部）
"""
import logging
from typing import AsyncIterator

import websockets

from core.channels.base import BaseChannel
from core.channels.dto import AudioPacket, ChannelMessage, ChannelInfo

TAG = __name__


class WebSocketChannel(BaseChannel):
    """
    WebSocket 直连通道
    
    特点：
    - 音频数据为纯 Opus 编码，无额外头部
    - TCP 保证顺序，无需乱序处理
    - 适用于网络稳定的客户端（App、浏览器）
    
    Usage:
        channel = WebSocketChannel(websocket, info)
        async for msg in channel.receive_messages():
            process(msg)
    """
    
    def __init__(self, websocket, info: ChannelInfo):
        """
        初始化 WebSocket 通道
        
        Args:
            websocket: websockets 库的连接对象
            info: 通道元信息
        """
        super().__init__(info)
        self._ws = websocket
        self._logger = logging.getLogger(TAG)
    
    @property
    def websocket(self):
        """
        获取底层 websocket 对象
        
        用于兼容旧代码，新代码应使用通道方法
        """
        return self._ws
    
    async def receive_messages(self) -> AsyncIterator[ChannelMessage]:
        """
        接收消息并转换为统一格式
        
        WebSocket 消息类型：
        - str: 文本消息（JSON 指令）
        - bytes: 音频消息（纯 Opus 数据）
        """
        try:
            async for message in self._ws:
                if self._closed:
                    break
                
                if isinstance(message, str):
                    yield ChannelMessage.text(message)
                elif isinstance(message, bytes):
                    # WebSocket 直连：纯 Opus 数据，无头部
                    packet = AudioPacket(data=message)
                    yield ChannelMessage.audio(packet)
                    
        except websockets.exceptions.ConnectionClosed as e:
            self._logger.info(f"WebSocket 连接关闭: device={self.device_id}, code={e.code}")
        except Exception as e:
            self._logger.error(f"WebSocket 接收消息异常: device={self.device_id}, error={e}")
        finally:
            self._closed = True
    
    async def send_audio(self, packet: AudioPacket) -> None:
        """
        发送音频数据
        
        WebSocket 直连模式直接发送 Opus 数据，无需添加头部
        """
        if self._closed:
            self._logger.warning(f"尝试在已关闭的通道发送音频: device={self.device_id}")
            return
            
        try:
            await self._ws.send(packet.data)
        except websockets.exceptions.ConnectionClosed as e:
            self._logger.warning(f"发送音频时连接已关闭: device={self.device_id}, code={e.code}")
            self._closed = True
            raise
        except Exception as e:
            self._logger.error(f"发送音频失败: device={self.device_id}, error={e}")
            raise
    
    async def send_text(self, message: str) -> None:
        """发送文本消息"""
        if self._closed:
            self._logger.warning(f"尝试在已关闭的通道发送文本: device={self.device_id}")
            return
            
        try:
            await self._ws.send(message)
        except websockets.exceptions.ConnectionClosed as e:
            self._logger.warning(f"发送文本时连接已关闭: device={self.device_id}, code={e.code}")
            self._closed = True
            raise
        except Exception as e:
            self._logger.error(f"发送文本失败: device={self.device_id}, error={e}")
            raise
    
    async def close(self) -> None:
        """关闭 WebSocket 连接"""
        if self._closed:
            return
            
        self._closed = True
        try:
            await self._ws.close()
            self._logger.info(f"WebSocket 通道已关闭: device={self.device_id}")
        except Exception as e:
            self._logger.error(f"关闭 WebSocket 连接失败: device={self.device_id}, error={e}")

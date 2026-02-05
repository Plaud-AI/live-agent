"""
MQTT 网关通道实现

用于通过 xiaozhi-mqtt-gateway 转发的 ESP32 设备连接。
音频格式：16 字节头部 + Opus 数据

头部格式（16字节，大端序）：
┌──────────┬──────────┬─────────────┬──────────┬───────────┬────────────┐
│  type    │ reserved │ payload_len │ sequence │ timestamp │ opus_len   │
│  (1B)    │  (1B)    │   (2B)      │  (4B)    │   (4B)    │   (4B)     │
└──────────┴──────────┴─────────────┴──────────┴───────────┴────────────┘
"""
import logging
import time
from typing import AsyncIterator

import websockets

from core.channels.base import BaseChannel
from core.channels.dto import AudioPacket, ChannelMessage, ChannelInfo

TAG = __name__


class MqttGatewayChannel(BaseChannel):
    """
    MQTT 网关通道
    
    特点：
    - 音频数据带 16 字节头部（时间戳、序列号等）
    - 需要处理 UDP 传输可能导致的乱序
    - 适用于 ESP32 等通过 MQTT+UDP 连接的嵌入式设备
    
    乱序处理策略：
    - 维护一个小型缓冲区暂存乱序包
    - 基于时间戳排序后输出
    - 缓冲区满时强制输出避免阻塞
    """
    
    HEADER_SIZE = 16           # 头部大小（字节）
    MAX_BUFFER_SIZE = 20       # 乱序缓冲区最大容量
    
    def __init__(self, websocket, info: ChannelInfo):
        """
        初始化 MQTT 网关通道
        
        Args:
            websocket: websockets 库的连接对象（来自网关转发）
            info: 通道元信息
        """
        super().__init__(info)
        self._ws = websocket
        self._logger = logging.getLogger(TAG)
        
        # 发送序列号（递增）
        self._send_sequence = 0
        
        # 乱序重排序缓冲区
        self._reorder_buffer: dict[int, AudioPacket] = {}
        self._last_processed_timestamp = 0
    
    @property
    def websocket(self):
        """
        获取底层 websocket 对象
        
        用于兼容旧代码，新代码应使用通道方法
        """
        return self._ws
    
    async def receive_messages(self) -> AsyncIterator[ChannelMessage]:
        """
        接收消息，解析头部并处理乱序
        
        处理流程：
        1. 接收原始消息
        2. 文本消息直接返回
        3. 二进制消息解析头部，提取音频数据
        4. 基于时间戳排序后输出
        """
        try:
            async for message in self._ws:
                if self._closed:
                    break
                
                if isinstance(message, str):
                    yield ChannelMessage.text(message)
                elif isinstance(message, bytes):
                    # 解析并重排序音频包
                    packets = self._parse_audio_message(message)
                    for packet in packets:
                        yield ChannelMessage.audio(packet)
                        
        except websockets.exceptions.ConnectionClosed as e:
            self._logger.info(f"MQTT Gateway 连接关闭: device={self.device_id}, code={e.code}")
        except Exception as e:
            self._logger.error(f"MQTT Gateway 接收消息异常: device={self.device_id}, error={e}")
        finally:
            self._closed = True
    
    def _parse_audio_message(self, message: bytes) -> list[AudioPacket]:
        """
        解析 MQTT 网关音频消息
        
        Args:
            message: 原始消息（16字节头部 + Opus数据）
            
        Returns:
            按时间戳排序后的音频包列表
        """
        if len(message) < self.HEADER_SIZE:
            # 无效包（太短），作为原始数据返回
            self._logger.warning(f"收到无效音频包: len={len(message)}, device={self.device_id}")
            return [AudioPacket(data=message)]
        
        try:
            # 解析 16 字节头部
            # type = message[0]  # 暂未使用
            # reserved = message[1]
            # payload_len = int.from_bytes(message[2:4], "big")
            sequence = int.from_bytes(message[4:8], "big")
            timestamp = int.from_bytes(message[8:12], "big")
            opus_length = int.from_bytes(message[12:16], "big")
            
            # 提取音频数据
            if opus_length > 0 and len(message) >= self.HEADER_SIZE + opus_length:
                audio_data = message[self.HEADER_SIZE:self.HEADER_SIZE + opus_length]
            else:
                # 长度无效，取头部后所有数据
                audio_data = message[self.HEADER_SIZE:]
            
            packet = AudioPacket(
                data=audio_data,
                timestamp=timestamp,
                sequence=sequence
            )
            
            # 乱序重排序
            return self._reorder_packet(packet)
            
        except Exception as e:
            self._logger.error(f"解析 MQTT 音频包失败: error={e}, device={self.device_id}")
            # 解析失败，返回去除头部的原始数据
            return [AudioPacket(data=message[self.HEADER_SIZE:])]
    
    def _reorder_packet(self, packet: AudioPacket) -> list[AudioPacket]:
        """
        基于时间戳的乱序重排序
        
        策略：
        - 时间戳递增的包直接输出
        - 乱序包暂存到缓冲区
        - 每次输出后检查缓冲区是否有后续包可输出
        - 缓冲区满时强制输出最旧的包
        
        Args:
            packet: 待处理的音频包
            
        Returns:
            按顺序应该输出的包列表
        """
        result = []
        
        # 时间戳递增，正常顺序
        if packet.timestamp >= self._last_processed_timestamp:
            result.append(packet)
            self._last_processed_timestamp = packet.timestamp
            
            # 检查缓冲区中是否有后续包可以输出
            while True:
                next_ts = None
                for ts in sorted(self._reorder_buffer.keys()):
                    if ts > self._last_processed_timestamp:
                        next_ts = ts
                        break
                
                if next_ts is None:
                    break
                
                buffered = self._reorder_buffer.pop(next_ts)
                result.append(buffered)
                self._last_processed_timestamp = next_ts
        else:
            # 乱序包，暂存到缓冲区
            if len(self._reorder_buffer) < self.MAX_BUFFER_SIZE:
                self._reorder_buffer[packet.timestamp] = packet
            else:
                # 缓冲区满，强制输出（避免阻塞）
                self._logger.warning(f"乱序缓冲区已满，强制输出: device={self.device_id}")
                result.append(packet)
        
        return result
    
    async def send_audio(self, packet: AudioPacket) -> None:
        """
        发送音频数据（添加 16 字节头部）
        
        头部结构：
        - type (1B): 固定为 1
        - reserved (1B): 保留
        - payload_length (2B): 负载长度
        - sequence (4B): 序列号
        - timestamp (4B): 时间戳
        - opus_length (4B): Opus 数据长度
        """
        if self._closed:
            self._logger.warning(f"尝试在已关闭的通道发送音频: device={self.device_id}")
            return
        
        try:
            # 构建 16 字节头部
            header = bytearray(16)
            header[0] = 1  # type
            header[2:4] = len(packet.data).to_bytes(2, "big")  # payload_length
            header[4:8] = self._send_sequence.to_bytes(4, "big")  # sequence
            
            # 使用传入的时间戳或当前时间
            timestamp = packet.timestamp if packet.timestamp else int(time.time() * 1000) % (2**32)
            header[8:12] = timestamp.to_bytes(4, "big")  # timestamp
            header[12:16] = len(packet.data).to_bytes(4, "big")  # opus_length
            
            # 发送完整数据包
            complete_packet = bytes(header) + packet.data
            await self._ws.send(complete_packet)
            
            self._send_sequence += 1
            
        except websockets.exceptions.ConnectionClosed as e:
            self._logger.warning(f"发送音频时连接已关闭: device={self.device_id}, code={e.code}")
            self._closed = True
            raise
        except Exception as e:
            self._logger.error(f"MQTT Gateway 发送音频失败: device={self.device_id}, error={e}")
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
            self._logger.error(f"MQTT Gateway 发送文本失败: device={self.device_id}, error={e}")
            raise
    
    async def close(self) -> None:
        """关闭连接并清理资源"""
        if self._closed:
            return
        
        self._closed = True
        self._reorder_buffer.clear()
        
        try:
            await self._ws.close()
            self._logger.info(f"MQTT Gateway 通道已关闭: device={self.device_id}")
        except Exception as e:
            self._logger.error(f"关闭 MQTT Gateway 连接失败: device={self.device_id}, error={e}")

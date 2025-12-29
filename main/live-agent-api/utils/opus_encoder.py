"""
Opus 编码工具类
将 PCM 音频数据编码为 Opus 格式，与语音对话返回给设备的格式一致
"""

import numpy as np
from opuslib_next import Encoder
from opuslib_next import constants
from typing import List
from config.logger import setup_logging

TAG = __name__
logger = setup_logging(TAG)


class OpusEncoder:
    """PCM 到 Opus 的编码器"""

    def __init__(
        self, 
        sample_rate: int = 16000, 
        channels: int = 1, 
        frame_size_ms: int = 60
    ):
        """
        初始化 Opus 编码器

        Args:
            sample_rate: 采样率 (Hz)，默认 16000
            channels: 通道数 (1=单声道, 2=立体声)，默认 1
            frame_size_ms: 帧大小 (毫秒)，默认 60ms
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_size_ms = frame_size_ms
        
        # 计算每帧样本数 = 采样率 * 帧大小(毫秒) / 1000
        self.frame_size = (sample_rate * frame_size_ms) // 1000
        # 总帧大小 = 每帧样本数 * 通道数
        self.total_frame_size = self.frame_size * channels

        # 比特率和复杂度设置
        self.bitrate = 24000  # bps
        self.complexity = 10  # 最高质量

        try:
            # 创建 Opus 编码器
            self.encoder = Encoder(
                sample_rate, channels, constants.APPLICATION_AUDIO
            )
            self.encoder.bitrate = self.bitrate
            self.encoder.complexity = self.complexity
            self.encoder.signal = constants.SIGNAL_VOICE  # 语音信号优化
        except Exception as e:
            logger.bind(tag=TAG).error(f"初始化 Opus 编码器失败: {e}")
            raise RuntimeError("Opus 编码器初始化失败") from e

    def encode_pcm_to_opus(self, pcm_data: bytes) -> List[bytes]:
        """
        将 PCM 数据编码为 Opus 格式

        Args:
            pcm_data: PCM 字节数据 (16位小端，单声道，16kHz)

        Returns:
            Opus 数据帧列表
        """
        # 将字节数据转换为 numpy 数组
        samples = np.frombuffer(pcm_data, dtype=np.int16)
        
        opus_frames = []
        offset = 0

        # 处理所有完整帧
        while offset <= len(samples) - self.total_frame_size:
            frame = samples[offset:offset + self.total_frame_size]
            encoded = self._encode_frame(frame)
            if encoded:
                opus_frames.append(encoded)
            offset += self.total_frame_size

        # 处理剩余数据（填充零）
        remaining = len(samples) - offset
        if remaining > 0:
            last_frame = np.zeros(self.total_frame_size, dtype=np.int16)
            last_frame[:remaining] = samples[offset:]
            encoded = self._encode_frame(last_frame)
            if encoded:
                opus_frames.append(encoded)

        return opus_frames

    def _encode_frame(self, frame: np.ndarray) -> bytes:
        """编码一帧音频数据"""
        try:
            frame_bytes = frame.tobytes()
            encoded = self.encoder.encode(frame_bytes, self.frame_size)
            return encoded
        except Exception as e:
            logger.bind(tag=TAG).error(f"Opus 编码失败: {e}")
            return None


def pcm_to_opus_stream(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """
    将 PCM 数据转换为连续的 Opus 数据流
    
    这个函数返回的格式与语音对话中发送给设备的格式一致：
    - 每帧前面有 16 字节的头
    - 头格式: [1字节类型][1字节tag][4字节长度][10字节保留]
    
    Args:
        pcm_data: PCM 字节数据 (16位小端，单声道)
        sample_rate: 采样率，默认 16000 Hz
    
    Returns:
        带头部的 Opus 数据流
    """
    encoder = OpusEncoder(sample_rate=sample_rate)
    opus_frames = encoder.encode_pcm_to_opus(pcm_data)
    
    # 构建带头部的数据流
    result = bytearray()
    for opus_frame in opus_frames:
        # 添加 16 字节头
        header = bytearray(16)
        header[0] = 1  # 音频消息类型
        header[1] = 0  # 消息标签 (NORMAL)
        header[2:6] = len(opus_frame).to_bytes(4, "big")  # 数据长度
        # bytes 3-15 保留
        
        result.extend(header)
        result.extend(opus_frame)
    
    return bytes(result)


def pcm_to_opus_raw(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """
    将 PCM 数据转换为原始 Opus 数据（无头部）
    
    Args:
        pcm_data: PCM 字节数据 (16位小端，单声道)
        sample_rate: 采样率，默认 16000 Hz
    
    Returns:
        连接在一起的原始 Opus 帧数据
    """
    encoder = OpusEncoder(sample_rate=sample_rate)
    opus_frames = encoder.encode_pcm_to_opus(pcm_data)
    return b"".join(opus_frames)


"""
RTC 通道实现

包含：  
- RTCChannelBase: RTC 通道抽象基类
- WebRTCChannel: 标准 WebRTC 通道（预留）
- AgoraChannel: Agora RTC 通道实现

Agora SDK 重要限制：
- 一个进程只能有一个 AgoraService 实例
- 回调中不能调用 SDK API，也不能执行耗时操作
- 音频数据需要通过队列传递
"""

import asyncio
import logging
import json
import time
from abc import abstractmethod
from typing import AsyncIterator, Optional
from queue import Queue, Empty
import threading

from core.channels.base import BaseChannel
from core.channels.dto import AudioPacket, ChannelMessage, ChannelInfo, MessageType

TAG = __name__

# 尝试导入 Agora SDK
try:
    from agora.rtc.rtc_connection import (
        RTCConnection,
        LocalUser,
        AudioFrame,
        IRTCConnectionObserver,
    )
    from agora.rtc.agora_base import EncodedAudioFrameInfo, AudioCodecType
    AGORA_SDK_AVAILABLE = True
except ImportError:
    AGORA_SDK_AVAILABLE = False
    RTCConnection = None
    LocalUser = None
    AudioFrame = None
    EncodedAudioFrameInfo = None
    AudioCodecType = None


class RTCChannelBase(BaseChannel):
    """
    RTC 通道抽象基类
    
    为 WebRTC、Agora 等实时通信协议提供统一的抽象层。
    """
    
    def __init__(self, info: ChannelInfo):
        super().__init__(info)
        self._logger = logging.getLogger(TAG)
        
        # RTC 连接状态
        self._rtc_connected = False
        self._ice_connection_state = "new"
    
    @property
    def is_rtc_connected(self) -> bool:
        """RTC 连接是否已建立"""
        return self._rtc_connected
    
    @property
    def ice_connection_state(self) -> str:
        """ICE 连接状态"""
        return self._ice_connection_state
    
    @abstractmethod
    async def handle_signaling(self, message: dict) -> Optional[dict]:
        """处理信令消息"""
        pass
    
    @abstractmethod
    async def create_offer(self) -> dict:
        """创建 SDP Offer"""
        pass
    
    @abstractmethod
    async def set_remote_description(self, sdp: dict) -> None:
        """设置远端 SDP"""
        pass
    
    @abstractmethod
    async def add_ice_candidate(self, candidate: dict) -> None:
        """添加 ICE Candidate"""
        pass
    
    async def on_ice_connection_state_change(self, state: str) -> None:
        """ICE 连接状态变化回调"""
        self._ice_connection_state = state
        self._logger.info(f"ICE 连接状态变化: {state}, device={self.device_id}")
        
        if state in ("connected", "completed"):
            self._rtc_connected = True
        elif state in ("failed", "disconnected", "closed"):
            self._rtc_connected = False


class WebRTCChannel(RTCChannelBase):
    """
    WebRTC 通道（预留实现）
    
    TODO: 使用 aiortc 库实现标准 WebRTC 支持
    """
    
    def __init__(self, info: ChannelInfo):
        super().__init__(info)
        self._logger.info(f"WebRTC 通道初始化（未实现）: device={self.device_id}")
    
    async def receive_messages(self) -> AsyncIterator[ChannelMessage]:
        raise NotImplementedError("WebRTC 通道尚未实现")
    
    async def send_audio(self, packet: AudioPacket) -> None:
        raise NotImplementedError("WebRTC 通道尚未实现")
    
    async def send_text(self, message: str) -> None:
        raise NotImplementedError("WebRTC 通道尚未实现")
    
    async def close(self) -> None:
        self._closed = True
    
    async def handle_signaling(self, message: dict) -> Optional[dict]:
        raise NotImplementedError("WebRTC 通道尚未实现")
    
    async def create_offer(self) -> dict:
        raise NotImplementedError("WebRTC 通道尚未实现")
    
    async def set_remote_description(self, sdp: dict) -> None:
        raise NotImplementedError("WebRTC 通道尚未实现")
    
    async def add_ice_candidate(self, candidate: dict) -> None:
        raise NotImplementedError("WebRTC 通道尚未实现")


class AgoraChannel(RTCChannelBase):
    """
    Agora RTC 通道实现
    
    基于 agora-python-server-sdk 实现，支持：
    - 音频收发（PCM 格式）
    - 数据通道（文本消息）
    - 频道管理（加入/离开）
    
    使用前需要先初始化 AgoraServiceManager
    
    音频流程：
    1. 远程用户音频 → AudioFrameObserver.on_playback_audio_frame_before_mixing
       → _audio_queue → receive_messages() → ASR
    2. TTS 音频 → send_audio() → connection.push_audio_pcm_data → 远程用户
    
    Agora 配置（存储在 info.extra）：
    - app_id: Agora App ID
    - channel_name: 频道名称
    - token: 鉴权 Token
    - uid: 用户 ID
    - remote_uid: 远程用户 ID（订阅）
    """
    
    def __init__(self, info: ChannelInfo):
        super().__init__(info)
        
        # Agora 配置
        self._app_id = info.get_extra("app_id")
        self._channel_name = info.get_extra("channel_name")
        self._token = info.get_extra("token")
        self._uid = info.get_extra("uid", 0)
        self._remote_uid = info.get_extra("remote_uid", 0)
        
        # Agora 连接对象
        self._connection: Optional['RTCConnection'] = None
        self._local_user: Optional['LocalUser'] = None
        
        # Observer 对象（必须保持引用，防止被 GC 回收）
        self._audio_observer = None
        self._connection_observer = None
        self._local_user_observer = None
        
        # 音频队列（用于从回调传递音频到异步生成器）
        self._audio_queue: Queue = Queue(maxsize=1000)
        self._text_queue: Queue = Queue(maxsize=100)
        
        # 发送队列（用于异步发送，避免每次都切换线程池）
        self._send_queue: Queue = Queue(maxsize=500)
        self._priority_queue: Queue = Queue(maxsize=50)  # 状态消息优先队列
        self._send_thread: Optional[threading.Thread] = None
        
        # 状态标志
        self._joined = False
        self._stop_event = threading.Event()
        
        # 音频参数
        self._sample_rate = 16000
        self._channels = 1
        self._bytes_per_sample = 2  # 16-bit PCM
        
        self._logger.info(
            f"Agora 通道初始化: channel={self._channel_name}, uid={self._uid}"
        )
    
    @property
    def app_id(self) -> Optional[str]:
        return self._app_id
    
    @property
    def channel_name(self) -> Optional[str]:
        return self._channel_name
    
    @property
    def is_joined(self) -> bool:
        return self._joined
    
    async def join_channel(self) -> bool:
        """
        加入 Agora 频道
        
        重要：所有 Agora SDK 同步调用必须在线程池中执行，
        避免阻塞 asyncio 事件循环导致服务卡死。
        
        Returns:
            bool: 是否成功加入
        """
        if not AGORA_SDK_AVAILABLE:
            self._logger.error("Agora SDK 不可用")
            return False
        
        if self._joined:
            self._logger.warning("已经加入频道，跳过重复加入")
            return True
        
        try:
            from core.agora import AgoraServiceManager
            
            if not AgoraServiceManager.is_initialized():
                self._logger.error("AgoraServiceManager 未初始化")
                return False
            
            # 获取事件循环
            loop = asyncio.get_running_loop()
            
            # 所有 Agora SDK 同步调用放到线程池执行，避免阻塞事件循环
            def _sync_join_channel():
                """在线程池中执行所有 Agora SDK 同步调用"""
                # 创建连接
                self._connection = AgoraServiceManager.create_connection(
                    channel_name=self._channel_name,
                    user_id=self._uid,
                    token=self._token,
                )
                
                if self._connection is None:
                    return False, "创建 Agora 连接失败"
                
                # 注册观察者
                self._register_observers()
                
                # 加入频道
                token = self._token or self._app_id
                result = self._connection.connect(
                    token,
                    self._channel_name,
                    str(self._uid)
                )
                
                if result != 0:
                    return False, f"加入频道失败，错误码: {result}"
                
                # 发布音频
                ret = self._connection.publish_audio()
                print(f"[AgoraChannel] publish_audio 返回值: {ret}")
                self._logger.info(f"publish_audio 返回值: {ret}")
                
                # 显式订阅所有音频（即使配置了 auto_subscribe_audio）
                local_user = self._connection.get_local_user()
                if local_user:
                    ret = local_user.subscribe_all_audio()
                    print(f"[AgoraChannel] subscribe_all_audio 返回值: {ret}")
                    self._logger.info(f"subscribe_all_audio 返回值: {ret}")
                
                # 创建 Data Stream（用于文本消息）
                old_stream_id = getattr(self._connection, '_data_stream_id', -1)
                stream_id = self._connection._create_data_stream(reliable=True, ordered=True)
                if stream_id is None or stream_id < 0:
                    self._logger.warning(f"创建 Data Stream 失败，错误码: {stream_id}")
                else:
                    self._connection._data_stream_id = stream_id
                    self._logger.info(f"Data Stream 创建成功并更新: stream_id={stream_id}")
                    print(f"[AgoraChannel] Data Stream 更新: {old_stream_id} -> {stream_id}")
                
                return True, None
            
            # 在线程池中执行，设置 30 秒超时
            success, error_msg = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_join_channel),
                timeout=30.0
            )
            
            if not success:
                self._logger.error(error_msg)
                return False
            
            self._joined = True
            self._rtc_connected = True
            
            # 启动专用发送线程
            self._start_send_thread()
            
            self._logger.info(f"成功加入 Agora 频道: {self._channel_name}")
            return True
            
        except asyncio.TimeoutError:
            self._logger.error("加入 Agora 频道超时(30s)")
            return False
        except Exception as e:
            self._logger.error(f"加入频道异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _start_send_thread(self) -> None:
        """启动专用发送线程"""
        if self._send_thread is not None and self._send_thread.is_alive():
            return
        
        self._send_thread = threading.Thread(
            target=self._send_thread_loop,
            name=f"AgoraSend-{self._channel_name}",
            daemon=True
        )
        self._send_thread.start()
        self._logger.info(f"发送线程已启动: {self._channel_name}")
    
    def _send_thread_loop(self) -> None:
        """
        发送线程主循环
        
        从发送队列取数据，执行 Agora SDK 调用。
        
        优先级：
        1. 优先队列中的状态消息（stt, tts start/stop 等）
        2. 普通队列中的音频和其他文本消息
        """
        self._logger.info(f"发送线程开始运行: {self._channel_name}")
        send_count = 0
        priority_count = 0
        error_count = 0
        
        while not self._stop_event.is_set():
            try:
                # 1. 优先处理状态消息（立即发送，不等待）
                while True:
                    try:
                        item = self._priority_queue.get_nowait()
                        if item is None:
                            break
                        msg_type, data = item
                        if msg_type == "text" and self._connection:
                            ret = self._connection.send_stream_message(data)
                            if ret != 0:
                                self._logger.error(f"状态消息发送失败: ret={ret}")
                            else:
                                priority_count += 1
                        send_count += 1
                    except Empty:
                        break
                
                # 2. 处理普通队列（音频和其他消息）
                try:
                    item = self._send_queue.get(timeout=0.005)
                except Empty:
                    continue
                
                if item is None:  # 哨兵值，退出
                    break
                
                msg_type, data = item
                
                if msg_type == "audio":
                    # 发送音频
                    opus_data, info = data
                    if self._connection:
                        ret = self._connection.push_audio_encoded_data(opus_data, info)
                        if ret != 0 and error_count < 5:
                            self._logger.error(f"push_audio_encoded_data 失败: ret={ret}")
                            error_count += 1
                    send_count += 1
                    
                elif msg_type == "text":
                    # 发送普通文本
                    text_data = data
                    if self._connection:
                        ret = self._connection.send_stream_message(text_data)
                        if ret != 0:
                            self._logger.error(f"send_stream_message 失败: ret={ret}")
                    send_count += 1
                
                # 批量处理：优先队列 + 普通队列（最多 10 个）
                batch_count = 0
                while batch_count < 10:
                    # 先检查优先队列
                    try:
                        item = self._priority_queue.get_nowait()
                        if item is not None:
                            msg_type, data = item
                            if msg_type == "text" and self._connection:
                                self._connection.send_stream_message(data)
                                priority_count += 1
                            send_count += 1
                            batch_count += 1
                            continue
                    except Empty:
                        pass
                    
                    # 再检查普通队列
                    try:
                        item = self._send_queue.get_nowait()
                        if item is None:
                            break
                        msg_type, data = item
                        if msg_type == "audio":
                            opus_data, info = data
                            if self._connection:
                                self._connection.push_audio_encoded_data(opus_data, info)
                            send_count += 1
                        elif msg_type == "text":
                            if self._connection:
                                self._connection.send_stream_message(data)
                            send_count += 1
                        batch_count += 1
                    except Empty:
                        break
                
            except Exception as e:
                self._logger.error(f"发送线程异常: {e}")
                import traceback
                traceback.print_exc()
        
        self._logger.info(f"发送线程退出: {self._channel_name}, 共发送 {send_count} 条消息, 优先消息 {priority_count} 条")
    
    def _stop_send_thread(self) -> None:
        """停止发送线程"""
        if self._send_thread is None:
            return
        
        # 发送哨兵值
        try:
            self._send_queue.put(None, timeout=1.0)
        except:
            pass
        
        # 等待线程退出
        self._send_thread.join(timeout=2.0)
        if self._send_thread.is_alive():
            self._logger.warning(f"发送线程未能正常退出: {self._channel_name}")
        self._send_thread = None
    
    async def leave_channel(self) -> None:
        """离开 Agora 频道"""
        if not self._joined or self._connection is None:
            return
        
        try:
            self._stop_event.set()
            
            # 停止发送线程
            self._stop_send_thread()
            
            # 在线程池中执行同步 SDK 调用
            loop = asyncio.get_running_loop()
            connection = self._connection
            
            def _sync_leave():
                connection.disconnect()
                connection.release()
            
            await loop.run_in_executor(None, _sync_leave)
            
            self._joined = False
            self._rtc_connected = False
            self._logger.info(f"已离开 Agora 频道: {self._channel_name}")
        except Exception as e:
            self._logger.error(f"离开频道异常: {e}")
    
    def _register_observers(self) -> None:
        """注册音频和连接观察者"""
        if self._connection is None:
            return
        
        print(f"[AgoraChannel] 开始注册 Observers...")
        
        # 创建观察者实例（保存为实例属性，防止被 GC 回收）
        self._audio_observer = _AgoraAudioObserver(
            audio_queue=self._audio_queue,
            logger=self._logger,
            channel_name=self._channel_name,
        )
        
        self._connection_observer = _AgoraConnectionObserver(
            channel=self,
            logger=self._logger,
        )
        
        self._local_user_observer = _AgoraLocalUserObserver(
            text_queue=self._text_queue,
            logger=self._logger,
        )
        
        # 注册连接观察者
        ret = self._connection.register_observer(self._connection_observer)
        print(f"[AgoraChannel] 注册 ConnectionObserver: ret={ret}")
        
        # 关键：设置音频帧参数必须在注册观察者之前调用！
        # 参考 SDK 示例: set_playback_audio_frame_before_mixing_parameters must be call before register_audio_frame_observer
        local_user = self._connection.get_local_user()
        if local_user:
            ret = local_user.set_playback_audio_frame_before_mixing_parameters(
                channels=1,  # 单声道
                sample_rate_hz=16000  # 16kHz 采样率
            )
            print(f"[AgoraChannel] set_playback_audio_frame_before_mixing_parameters: ret={ret}")
        else:
            print(f"[AgoraChannel] 警告: local_user 为空，无法设置音频帧参数")
        
        # 注册音频帧观察者（必须在设置参数之后）
        # enable_vad=0 禁用 VAD，vad_configure=None
        ret = self._connection.register_audio_frame_observer(self._audio_observer, 0, None)
        print(f"[AgoraChannel] 注册 AudioFrameObserver: ret={ret}")
        
        # 注册本地用户观察者
        ret = self._connection.register_local_user_observer(self._local_user_observer)
        print(f"[AgoraChannel] 注册 LocalUserObserver: ret={ret}")
        
        self._logger.info(f"Observer 已注册并保持引用")
        print(f"[AgoraChannel] 所有 Observers 注册完成")
    
    async def receive_messages(self) -> AsyncIterator[ChannelMessage]:
        """
        接收消息（音频和文本）
        
        从队列中获取音频帧，转换为 ChannelMessage
        """
        if not self._joined:
            self._logger.warning("尚未加入频道，无法接收消息")
            return
        
        while not self._closed and not self._stop_event.is_set():
            try:
                # 非阻塞检查音频队列
                try:
                    audio_data = self._audio_queue.get_nowait()
                    timestamp = int(time.time() * 1000)
                    packet = AudioPacket(
                        data=audio_data,
                        timestamp=timestamp,
                        sequence=0
                    )
                    yield ChannelMessage.audio(packet)
                except Empty:
                    pass
                
                # 非阻塞检查文本队列
                try:
                    text_data = self._text_queue.get_nowait()
                    yield ChannelMessage.text(text_data)
                except Empty:
                    pass
                
                # 避免忙等待
                await asyncio.sleep(0.01)
                
            except Exception as e:
                self._logger.error(f"接收消息异常: {e}")
                break
    
    async def send_audio(self, packet: AudioPacket) -> None:
        """
        发送音频到远程用户
        
        将 Opus 编码音频放入发送队列，由专用发送线程执行 SDK 调用。
        这样避免每次发送都从线程池获取线程的开销。
        """
        if not self._joined or self._connection is None:
            self._logger.warning("尚未加入频道，无法发送音频")
            return
        
        try:
            # packet.data 是 Opus 编码数据
            opus_data = packet.data
            
            if not opus_data or len(opus_data) == 0:
                return
            
            # 创建编码音频帧信息
            # Opus 通常使用 60ms 帧，16kHz 采样率，单声道
            info = EncodedAudioFrameInfo(
                codec=AudioCodecType.AUDIO_CODEC_OPUS,
                sample_rate=16000,
                samples_per_channel=960,  # 60ms at 16kHz
                number_of_channels=1,
                capture_time_ms=packet.timestamp if packet.timestamp else 0,
            )
            
            # 放入发送队列（非阻塞），由专用发送线程处理
            try:
                self._send_queue.put_nowait(("audio", (opus_data, info)))
            except:
                # 队列满，丢弃（不阻塞）
                if not hasattr(self, '_audio_drop_count'):
                    self._audio_drop_count = 0
                self._audio_drop_count += 1
                if self._audio_drop_count <= 5:
                    self._logger.warning(f"发送队列已满，丢弃音频包")
                return
            
            # 记录首次发送
            if not hasattr(self, '_audio_send_count'):
                self._audio_send_count = 0
            self._audio_send_count += 1
            
            if self._audio_send_count == 1:
                self._logger.info(f"首次发送音频入队: size={len(opus_data)}, codec=OPUS")
            
        except Exception as e:
            self._logger.error(f"发送音频异常: {e}")
    
    async def send_text(self, message: str) -> None:
        """
        发送文本消息（通过数据通道）
        
        状态消息（stt, tts）优先发送，其他消息进入普通队列。
        """
        if not self._joined or self._connection is None:
            self._logger.warning("尚未加入频道，无法发送文本")
            return
        
        try:
            # 通过数据通道发送
            data = message.encode('utf-8')
            
            # 判断是否是状态消息（stt 或 tts 类型）
            is_state_message = ('"type":"stt"' in message or 
                               '"type":"tts"' in message or
                               '"type": "stt"' in message or
                               '"type": "tts"' in message)
            
            # 如果消息过长，需要分片
            max_size = 1024
            if len(data) <= max_size:
                if is_state_message:
                    # 状态消息进入优先队列
                    try:
                        self._priority_queue.put_nowait(("text", data))
                        self._logger.debug(f"[RTC] 状态消息入优先队列: len={len(data)}")
                    except:
                        # 优先队列满，尝试普通队列
                        self._send_queue.put_nowait(("text", data))
                else:
                    # 普通消息进入普通队列
                    try:
                        self._send_queue.put_nowait(("text", data))
                    except:
                        self._logger.warning(f"发送队列已满，丢弃文本消息")
                        return
            else:
                # 长消息分片发送（通常不是状态消息）
                message_id = str(int(time.time() * 1000))
                parts = [data[i:i+max_size] for i in range(0, len(data), max_size)]
                total_parts = len(parts)
                
                for i, part in enumerate(parts):
                    header = f"{message_id}|{i}|{total_parts}|".encode('utf-8')
                    chunk_data = header + part
                    
                    try:
                        self._send_queue.put_nowait(("text", chunk_data))
                    except:
                        self._logger.warning(f"发送队列已满，丢弃文本分片 {i+1}/{total_parts}")
            
        except Exception as e:
            self._logger.error(f"发送文本异常: {e}")
    
    async def close(self) -> None:
        """关闭通道"""
        await self.leave_channel()
        self._closed = True
        self._logger.info(f"Agora 通道已关闭: {self._channel_name}")
    
    async def mute_local_audio(self, mute: bool) -> None:
        """静音/取消静音本地音频"""
        if self._connection is None:
            return
        
        try:
            loop = asyncio.get_running_loop()
            connection = self._connection
            
            def _sync_mute():
                if mute:
                    connection.unpublish_audio()
                else:
                    connection.publish_audio()
            
            await loop.run_in_executor(None, _sync_mute)
        except Exception as e:
            self._logger.error(f"静音操作异常: {e}")
    
    # ==================== 信令方法（Agora 不需要） ====================
    
    async def handle_signaling(self, message: dict) -> Optional[dict]:
        """Agora 不使用传统的 WebRTC 信令"""
        return None
    
    async def create_offer(self) -> dict:
        """Agora 不使用 SDP"""
        return {}
    
    async def set_remote_description(self, sdp: dict) -> None:
        """Agora 不使用 SDP"""
        pass
    
    async def add_ice_candidate(self, candidate: dict) -> None:
        """Agora 不使用 ICE"""
        pass


# ==================== Agora 观察者类 ====================

class _AgoraAudioObserver:
    """
    Agora 音频帧观察者
    
    接收远程用户的音频帧，放入队列供异步处理
    
    重要：回调中不能调用 SDK API，不能执行耗时操作
    """
    
    def __init__(self, audio_queue: Queue, logger, channel_name: str):
        self._audio_queue = audio_queue
        self._logger = logger
        self._channel_name = channel_name
        self._frame_count = 0
        print(f"[AgoraAudioObserver] 音频观察者已创建: channel={channel_name}")
    
    def on_playback_audio_frame_before_mixing(
        self,
        agora_local_user,
        channel_id: str,
        uid: str,
        audio_frame,
        vad_result_state: int = -1,
        vad_result_bytes = None
    ) -> int:
        """
        接收远程用户的音频帧（混音前）
        
        这是获取单个远程用户原始音频的最佳回调
        
        SDK 2.1.6+ 新增参数:
        - vad_result_state: VAD 状态 (-1=未启用, 0=无声, 1=开始说话, 2=说话中, 3=停止说话)
        - vad_result_bytes: VAD 处理后的音频数据
        """
        try:
            self._frame_count += 1
            
            # 获取 PCM 数据
            pcm_data = audio_frame.buffer
            
            # 第一帧打印详细日志
            if self._frame_count == 1:
                print(f"[AgoraAudioObserver] 收到首个音频帧: uid={uid}, channel={channel_id}, size={len(pcm_data) if pcm_data else 0}, vad_state={vad_result_state}")
                self._logger.info(f"[Agora] 收到首个音频帧: uid={uid}, channel={channel_id}, size={len(pcm_data) if pcm_data else 0}, vad_state={vad_result_state}")
            
            # 放入队列（非阻塞）
            if not self._audio_queue.full():
                self._audio_queue.put_nowait(pcm_data)
            else:
                # 队列满，丢弃最旧的数据
                try:
                    self._audio_queue.get_nowait()
                    self._audio_queue.put_nowait(pcm_data)
                except Empty:
                    pass
            
            if self._frame_count % 100 == 0:
                print(f"[AgoraAudioObserver] 收到音频帧 #{self._frame_count}: uid={uid}, size={len(pcm_data) if pcm_data else 0}")
                self._logger.debug(
                    f"[Agora] 收到音频帧 #{self._frame_count}: "
                    f"uid={uid}, size={len(pcm_data) if pcm_data else 0} bytes"
                )
            
        except Exception as e:
            print(f"[AgoraAudioObserver] 音频回调异常: {e}")
            import traceback
            traceback.print_exc()
            self._logger.error(f"[Agora] 音频回调异常: {e}")
        
        return 0  # 返回 0 表示成功
    
    def on_record_audio_frame(self, agora_local_user, channel_id, audio_frame) -> int:
        """录制音频帧回调（本地麦克风）"""
        return 0
    
    def on_playback_audio_frame(self, agora_local_user, channel_id, audio_frame) -> int:
        """播放音频帧回调（混音后）- 用于调试"""
        if not hasattr(self, '_playback_frame_count'):
            self._playback_frame_count = 0
        self._playback_frame_count += 1
        if self._playback_frame_count == 1:
            print(f"[AgoraAudioObserver] on_playback_audio_frame 首次触发: channel={channel_id}")
        return 0
    
    def on_mixed_audio_frame(self, agora_local_user, channel_id, audio_frame) -> int:
        """混合音频帧回调"""
        return 0
    
    def on_ear_monitoring_audio_frame(self, agora_local_user, audio_frame) -> int:
        """耳返音频帧回调"""
        return 0
    
    def on_get_audio_frame_position(self, agora_local_user=None) -> int:
        """获取音频帧位置"""
        # 返回需要监听的音频帧位置（位掩码）
        # 1: POSITION_PLAYBACK - 播放音频帧
        # 2: POSITION_RECORD - 录制音频帧
        # 4: POSITION_MIXED - 混合音频帧
        # 8: POSITION_BEFORE_MIXING - 混音前音频帧
        if not hasattr(self, '_position_called'):
            self._position_called = True
            print(f"[AgoraAudioObserver] on_get_audio_frame_position 被调用，返回 9 (PLAYBACK | BEFORE_MIXING)")
        return 9  # 1 | 8 = PLAYBACK + BEFORE_MIXING


class _AgoraConnectionObserver:
    """Agora 连接状态观察者"""
    
    def __init__(self, channel: AgoraChannel, logger):
        self._channel = channel
        self._logger = logger
    
    def on_connecting(self, agora_rtc_conn, conn_info, reason):
        """正在连接"""
        print(f"[Agora] 正在连接: reason={reason}")
        self._logger.info(f"[Agora] 正在连接: reason={reason}")
    
    def on_connected(self, agora_rtc_conn, conn_info, reason):
        """连接成功"""
        print(f"[Agora] 连接成功: reason={reason}")
        self._logger.info(f"[Agora] 连接成功: reason={reason}")
        self._channel._rtc_connected = True
    
    def on_disconnected(self, agora_rtc_conn, conn_info, reason):
        """连接断开"""
        print(f"[Agora] 连接断开: reason={reason}")
        self._logger.info(f"[Agora] 连接断开: reason={reason}")
        self._channel._rtc_connected = False
    
    def on_reconnecting(self, agora_rtc_conn, conn_info, reason):
        """正在重连"""
        print(f"[Agora] 正在重连: reason={reason}")
        self._logger.info(f"[Agora] 正在重连: reason={reason}")
    
    def on_reconnected(self, agora_rtc_conn, conn_info, reason):
        """重连成功"""
        print(f"[Agora] 重连成功: reason={reason}")
        self._logger.info(f"[Agora] 重连成功: reason={reason}")
        self._channel._rtc_connected = True
    
    def on_connection_failure(self, agora_rtc_conn, conn_info, reason):
        """连接失败"""
        print(f"[Agora] 连接失败: reason={reason}")
        self._logger.error(f"[Agora] 连接失败: reason={reason}")
        self._channel._rtc_connected = False
    
    def on_user_joined(self, agora_rtc_conn, user_id):
        """远程用户加入"""
        print(f"[Agora] 远程用户加入: uid={user_id}")
        self._logger.info(f"[Agora] 远程用户加入: uid={user_id}")
    
    def on_user_left(self, agora_rtc_conn, user_id, reason):
        """远程用户离开"""
        print(f"[Agora] 远程用户离开: uid={user_id}, reason={reason}")
        self._logger.info(f"[Agora] 远程用户离开: uid={user_id}, reason={reason}")
    
    def on_transport_stats(self, agora_rtc_conn, stats):
        """传输统计（可选）"""
        pass
    
    def on_user_network_quality(self, agora_rtc_conn, user_id, tx_quality, rx_quality):
        """网络质量（可选）"""
        pass
    
    def on_stream_message_error(self, agora_rtc_conn, user_id, stream_id, code, missed, cached):
        """Data Stream 错误"""
        print(f"[Agora] Data Stream 错误: user_id={user_id}, stream_id={stream_id}, code={code}")
        self._logger.warning(f"[Agora] Data Stream 错误: user_id={user_id}, stream_id={stream_id}, code={code}")
    
    def on_token_privilege_will_expire(self, agora_rtc_conn, token):
        """Token 即将过期"""
        print(f"[Agora] Token 即将过期")
        self._logger.warning(f"[Agora] Token 即将过期")
    
    def on_token_privilege_did_expire(self, agora_rtc_conn):
        """Token 已过期"""
        print(f"[Agora] Token 已过期")
        self._logger.error(f"[Agora] Token 已过期")
    
    def on_error(self, agora_rtc_conn, error_code, error_msg):
        """连接错误"""
        print(f"[Agora] 连接错误: code={error_code}, msg={error_msg}")
        self._logger.error(f"[Agora] 连接错误: code={error_code}, msg={error_msg}")
    
    def on_channel_media_relay_state_changed(self, agora_rtc_conn, state, code):
        """媒体转发状态变化"""
        pass
    
    def on_channel_media_relay_event(self, agora_rtc_conn, event):
        """媒体转发事件"""
        pass


class _AgoraLocalUserObserver:
    """Agora 本地用户观察者（用于数据通道）"""
    
    def __init__(self, text_queue: Queue, logger):
        self._text_queue = text_queue
        self._logger = logger
        self._message_cache = {}
    
    def on_stream_message(self, agora_local_user, user_id, stream_id, data, length):
        """
        接收数据通道消息
        
        消息可能是分片的，格式: message_id|part_index|total_parts|content
        """
        print(f"[on_stream_message] 收到消息: user_id={user_id}, stream_id={stream_id}, length={length}")
        self._logger.info(f"[Agora] 收到 Data Stream 消息: user_id={user_id}, stream_id={stream_id}, length={length}")
        try:
            text = data.decode('utf-8')
            print(f"[on_stream_message] 消息内容: {text[:100]}...")
            self._logger.info(f"[Agora] 消息内容: {text[:100]}...")
            
            # 检查是否是分片消息
            if '|' in text and text.count('|') >= 3:
                parts = text.split('|', 3)
                message_id, part_index, total_parts, content = parts
                part_index = int(part_index)
                total_parts = int(total_parts)
                
                # 缓存分片
                if message_id not in self._message_cache:
                    self._message_cache[message_id] = {}
                self._message_cache[message_id][part_index] = content
                
                # 检查是否完整
                if len(self._message_cache[message_id]) == total_parts:
                    # 重组消息
                    full_message = ''.join(
                        self._message_cache[message_id][i]
                        for i in range(total_parts)
                    )
                    del self._message_cache[message_id]
                    
                    if not self._text_queue.full():
                        self._text_queue.put_nowait(full_message)
            else:
                # 非分片消息，直接放入队列
                if not self._text_queue.full():
                    self._text_queue.put_nowait(text)
            
        except Exception as e:
            self._logger.error(f"[Agora] 数据通道消息处理异常: {e}")
    
    # 添加 SDK 需要的所有回调方法（避免 AttributeError）
    def on_audio_track_publish_success(self, agora_local_user, agora_local_audio_track):
        pass
    
    def on_audio_track_publish_start(self, agora_local_user, agora_local_audio_track):
        pass
    
    def on_audio_track_unpublished(self, agora_local_user, agora_local_audio_track):
        pass
    
    def on_audio_track_publication_failure(self, agora_local_user, agora_local_audio_track, error):
        pass
    
    def on_local_audio_track_state_changed(self, agora_local_user, agora_local_audio_track, state, error):
        pass
    
    def on_audio_publish_state_changed(self, agora_local_user, channel, old_state, new_state, elapse):
        pass
    
    def on_video_publish_state_changed(self, agora_local_user, channel, old_state, new_state, elapse):
        pass
    
    def on_local_audio_track_statistics(self, agora_local_user, stats):
        pass
    
    def on_remote_audio_track_statistics(self, agora_local_user, agora_remote_audio_track, stats):
        pass
    
    def on_user_audio_track_subscribed(self, agora_local_user, user_id, agora_remote_audio_track):
        print(f"[Agora] 订阅用户音频成功: user_id={user_id}")
        self._logger.info(f"[Agora] 订阅用户音频成功: user_id={user_id}")
    
    def on_user_audio_track_state_changed(self, agora_local_user, user_id, agora_remote_audio_track, state, reason, elapsed):
        pass
    
    def on_audio_subscribe_state_changed(self, agora_local_user, channel, user_id, old_state, new_state, elapse):
        print(f"[Agora] 音频订阅状态变化: user_id={user_id}, old_state={old_state}, new_state={new_state}")
        self._logger.info(f"[Agora] 音频订阅状态变化: user_id={user_id}, old_state={old_state}, new_state={new_state}")
    
    def on_first_remote_audio_frame(self, agora_local_user, user_id, elapsed):
        print(f"[Agora] 收到首帧远程音频: user_id={user_id}, elapsed={elapsed}ms")
        self._logger.info(f"[Agora] 收到首帧远程音频: user_id={user_id}, elapsed={elapsed}ms")
    
    def on_first_remote_audio_decoded(self, agora_local_user, user_id, elapsed):
        pass
    
    def on_video_track_publish_success(self, agora_local_user, agora_local_video_track):
        pass
    
    def on_video_track_publish_start(self, agora_local_user, agora_local_video_track):
        pass
    
    def on_video_track_unpublished(self, agora_local_user, agora_local_video_track):
        pass
    
    def on_video_track_publication_failure(self, agora_local_user, agora_local_video_track, error):
        pass
    
    def on_local_video_track_state_changed(self, agora_local_user, agora_local_video_track, state, error):
        pass
    
    def on_local_video_track_statistics(self, agora_local_user, agora_local_video_track, stats):
        pass
    
    def on_user_video_track_subscribed(self, agora_local_user, user_id, info, agora_remote_video_track):
        pass
    
    def on_user_video_track_state_changed(self, agora_local_user, user_id, agora_remote_video_track, state, reason, elapsed):
        pass
    
    def on_remote_video_track_statistics(self, agora_local_user, agora_remote_video_track, stats):
        pass
    
    def on_audio_volume_indication(self, agora_local_user, speakers_list, speaker_number, total_volume):
        pass
    
    def on_active_speaker(self, agora_local_user, userId):
        pass
    
    def on_remote_video_stream_info_updated(self, agora_local_user, info):
        pass
    
    def on_video_subscribe_state_changed(self, agora_local_user, channel, user_id, old_state, new_state, elapse):
        pass
    
    def on_first_remote_video_frame(self, agora_local_user, user_id, width, height, elapsed):
        pass
    
    def on_first_remote_video_decoded(self, agora_local_user, user_id, width, height, elapsed):
        pass
    
    def on_first_remote_video_frame_rendered(self, agora_local_user, user_id, width, height, elapsed):
        pass
    
    def on_video_size_changed(self, agora_local_user, user_id, width, height, rotation):
        pass
    
    def on_user_info_updated(self, agora_local_user, user_id, msg, val):
        self._logger.info(f"[Agora] 用户信息更新: user_id={user_id}, msg={msg}, val={val}")
    
    def on_intra_request_received(self, agora_local_user):
        pass
    
    def on_remote_subscribe_fallback_to_audio_only(self, agora_local_user, user_id, is_fallback_or_recover):
        pass
    
    def on_user_state_changed(self, agora_local_user, user_id, state):
        self._logger.info(f"[Agora] 用户状态变化: user_id={user_id}, state={state}")
    
    def on_audio_meta_data_received(self, agora_local_user, user_id, data):
        pass

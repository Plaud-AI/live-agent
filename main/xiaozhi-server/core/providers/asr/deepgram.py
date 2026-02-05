# -*- coding: utf-8 -*-
"""
Deepgram 流式语音识别服务
参考 ten-framework 项目的 deepgram_asr_python 实现
支持实时 WebSocket 流式语音识别
"""
import json
import time
import uuid
import asyncio
import websockets
import opuslib_next
from websockets.protocol import State
from config.logger import setup_logging
from core.providers.asr.base import ASRProviderBase
from core.providers.asr.dto.dto import InterfaceType

TAG = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    """Deepgram 流式语音识别 Provider"""

    def __init__(self, config, delete_audio_file):
        super().__init__()
        self.interface_type = InterfaceType.STREAM
        self.config = config
        self.text = ""
        self.decoder = opuslib_next.Decoder(16000, 1)
        self.asr_ws = None
        self.forward_task = None
        self.is_processing = False
        self.is_connected = False
        self.keepalive_task = None

        # Deepgram API 配置
        self.api_key = config.get("api_key")
        self.url = config.get("url", "wss://api.deepgram.com/v1/listen")
        
        # 识别参数
        self.language = config.get("language", "zh-CN")
        self.model = config.get("model", "nova-2")
        self.sample_rate = config.get("sample_rate", 16000)
        self.encoding = config.get("encoding", "linear16")
        self.channels = config.get("channels", 1)
        self.smart_format = config.get("smart_format", True)
        self.punctuate = config.get("punctuate", True)
        self.interim_results = config.get("interim_results", True)
        self.endpointing = config.get("endpointing", 300)  # 静音检测时间(ms)
        
        # 热词支持
        self.hotwords = config.get("hotwords", [])
        
        # KeepAlive 配置
        self.keepalive_enabled = config.get("keep_alive", True)
        
        # 其他配置
        self.output_dir = config.get("output_dir", "./tmp/")
        self.delete_audio_file = delete_audio_file
        
        # 验证必要配置
        if not self.api_key:
            raise ValueError("Deepgram API key 是必需的")

    def _build_ws_url(self) -> str:
        """构建 WebSocket URL，添加查询参数"""
        params = []
        
        # 基本参数
        params.append(f"language={self.language}")
        params.append(f"model={self.model}")
        params.append(f"sample_rate={self.sample_rate}")
        params.append(f"encoding={self.encoding}")
        params.append(f"channels={self.channels}")
        
        # 功能参数
        if self.smart_format:
            params.append("smart_format=true")
        if self.punctuate:
            params.append("punctuate=true")
        if self.interim_results:
            params.append("interim_results=true")
        if self.endpointing:
            params.append(f"endpointing={self.endpointing}")
            
        # 热词支持
        if self.hotwords:
            for hw in self.hotwords:
                tokens = hw.split("|")
                if len(tokens) == 2 and tokens[1].replace(".", "").isdigit():
                    # 格式: "word|boost" -> "keywords=word:boost"
                    params.append(f"keywords={tokens[0]}:{tokens[1]}")
                else:
                    logger.bind(tag=TAG).warning(f"无效的热词格式: {hw}")
        
        # 数据隐私选项
        params.append("mip_opt_out=true")
        
        url = f"{self.url}?{'&'.join(params)}"
        return url

    async def open_audio_channels(self, conn):
        """打开音频通道"""
        await super().open_audio_channels(conn)

    async def receive_audio(self, conn, audio, audio_have_voice):
        """接收音频数据"""
        # 初始化音频缓存
        if not hasattr(conn, 'asr_audio_for_voiceprint'):
            conn.asr_audio_for_voiceprint = []
        
        # 存储音频数据（用于声纹识别）
        if audio:
            conn.asr_audio_for_voiceprint.append(audio)
        
        conn.asr_audio.append(audio)
        conn.asr_audio = conn.asr_audio[-10:]

        # 只在有声音且没有连接时建立连接
        if audio_have_voice and not self.is_processing and not self.asr_ws:
            # 记录 ASR 开始时间（用户开始说话）
            if hasattr(conn, 'latency_metrics') and conn.latency_metrics:
                conn.latency_metrics.mark_asr_start()
            try:
                await self._start_recognition(conn)
            except Exception as e:
                logger.bind(tag=TAG).error(f"开始识别失败: {str(e)}")
                await self._cleanup()
                return

        # 发送音频数据
        if self.asr_ws and self.is_processing and self.is_connected:
            try:
                # 判断输入数据类型：
                # - Agora 通道：音频数据已经是 PCM 格式，直接发送
                # - WebSocket 通道：音频数据是 Opus 编码，需要解码
                channel_type = getattr(conn.channel, 'channel_type', 'websocket') if hasattr(conn, 'channel') else 'websocket'
                
                if channel_type == 'agora':
                    # Agora 通道：直接使用 PCM 数据
                    pcm_frame = audio
                else:
                    # WebSocket 通道：Opus 解码
                    pcm_frame = self.decoder.decode(audio, 960)
                
                await self.asr_ws.send(pcm_frame)
            except Exception as e:
                logger.bind(tag=TAG).warning(f"发送音频失败: {str(e)}")
                await self._cleanup()

    async def _start_recognition(self, conn):
        """开始识别会话"""
        ws_url = self._build_ws_url()
        logger.bind(tag=TAG).info(f"连接 Deepgram: {ws_url}")
        
        # 建立 WebSocket 连接
        self.asr_ws = await websockets.connect(
            ws_url,
            additional_headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/octet-stream",
            },
            open_timeout=10,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=5,
        )
        
        logger.bind(tag=TAG).debug("Deepgram WebSocket 连接建立成功")
        
        self.is_processing = True
        self.is_connected = True
        
        # 启动消息处理任务
        self.forward_task = asyncio.create_task(self._forward_results(conn))
        
        # 启动 KeepAlive 任务
        if self.keepalive_enabled:
            logger.bind(tag=TAG).debug("启用 KeepAlive: 每5秒发送心跳")
            self.keepalive_task = asyncio.create_task(self._keepalive_loop())
        
        # 发送缓存的音频数据
        if conn.asr_audio:
            # 判断通道类型
            channel_type = getattr(conn.channel, 'channel_type', 'websocket') if hasattr(conn, 'channel') else 'websocket'
            
            for cached_audio in conn.asr_audio[-10:]:
                try:
                    if channel_type == 'agora':
                        # Agora 通道：直接使用 PCM 数据
                        pcm_frame = cached_audio
                    else:
                        # WebSocket 通道：Opus 解码
                        pcm_frame = self.decoder.decode(cached_audio, 960)
                    await self.asr_ws.send(pcm_frame)
                except Exception as e:
                    logger.bind(tag=TAG).warning(f"发送缓存音频失败: {e}")
                    break

    async def _keepalive_loop(self):
        """KeepAlive 心跳任务"""
        try:
            while self.is_processing and self.asr_ws and self.keepalive_enabled:
                await asyncio.sleep(5)
                if not self._is_ws_connected() or self.asr_ws is None:
                    break
                try:
                    await self.asr_ws.send(json.dumps({"type": "KeepAlive"}))
                    logger.bind(tag=TAG).debug("[KeepAlive] 心跳发送成功")
                except Exception as e:
                    logger.bind(tag=TAG).info(f"KeepAlive 发送失败: {e}")
                    break
        except asyncio.CancelledError:
            logger.bind(tag=TAG).debug("KeepAlive 任务已取消")
        except Exception as e:
            logger.bind(tag=TAG).info(f"KeepAlive 任务异常: {e}")

    def _is_ws_connected(self) -> bool:
        """检查 WebSocket 连接状态"""
        if self.asr_ws is None:
            return False
        try:
            if hasattr(self.asr_ws, "state"):
                return self.is_processing and self.asr_ws.state == State.OPEN
            return self.is_processing
        except Exception:
            return False

    async def _forward_results(self, conn):
        """转发识别结果"""
        try:
            while not conn.stop_event.is_set():
                try:
                    response = await asyncio.wait_for(self.asr_ws.recv(), timeout=1.0)
                    result = json.loads(response)
                    
                    message_type = result.get("type")
                    
                    if message_type == "Results":
                        should_exit = await self._handle_result(conn, result)
                        if should_exit:
                            logger.bind(tag=TAG).debug("识别完成，退出循环并清理连接")
                            break
                    elif message_type == "Error":
                        error_msg = result.get("description", "Unknown error")
                        logger.bind(tag=TAG).error(f"Deepgram 错误: {error_msg}")
                    elif message_type == "Metadata":
                        logger.bind(tag=TAG).debug(f"Deepgram 元数据: {result}")
                        
                except asyncio.TimeoutError:
                    continue
                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).info("Deepgram 连接已关闭")
                    self.is_connected = False
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(f"处理结果失败: {str(e)}")
                    break

        except Exception as e:
            logger.bind(tag=TAG).error(f"结果转发失败: {str(e)}")
        finally:
            await self._cleanup()
            if conn:
                if hasattr(conn, 'asr_audio_for_voiceprint'):
                    conn.asr_audio_for_voiceprint = []
                if hasattr(conn, 'asr_audio'):
                    conn.asr_audio = []

    async def _handle_result(self, conn, result):
        """处理识别结果"""
        try:
            is_final = result.get("is_final", False)
            
            # 从 channel.alternatives[0] 提取转录文本
            channel = result.get("channel", {})
            alternatives = channel.get("alternatives", [])
            
            if not alternatives:
                return
            
            first_alt = alternatives[0]
            transcript = first_alt.get("transcript", "").strip()
            
            if not transcript:
                return
            
            # 获取时间信息
            start_seconds = result.get("start", 0)
            duration_seconds = result.get("duration", 0)
            
            logger.bind(tag=TAG).debug(
                f"Deepgram 识别结果: text='{transcript}', final={is_final}, "
                f"start={start_seconds:.2f}s, duration={duration_seconds:.2f}s"
            )
            
            if is_final:
                logger.bind(tag=TAG).info(f"识别到文本: {transcript}")
                
                # 记录 ASR Final 结果时间
                if hasattr(conn, 'latency_metrics') and conn.latency_metrics:
                    conn.latency_metrics.mark_asr_final()
                
                # 手动模式下累积识别结果
                if conn.client_listen_mode == "manual":
                    if self.text:
                        self.text += transcript
                    else:
                        self.text = transcript

                    # 手动模式下，只有在收到 stop 信号后才触发处理
                    if conn.client_voice_stop:
                        audio_data = getattr(conn, 'asr_audio_for_voiceprint', [])
                        if len(audio_data) > 0:
                            logger.bind(tag=TAG).debug("收到最终识别结果，触发处理")
                            await self.handle_voice_stop(conn, audio_data)
                            conn.asr_audio.clear()
                            conn.reset_vad_states()
                            # 手动模式处理完成后也退出循环
                            return True
                else:
                    # 自动模式下直接覆盖，处理完后退出循环
                    # 与其他流式 ASR（阿里云、讯飞、豆包）保持一致的行为
                    self.text = transcript
                    conn.reset_vad_states()
                    audio_data = getattr(conn, 'asr_audio_for_voiceprint', [])
                    await self.handle_voice_stop(conn, audio_data)
                    # 返回 True 表示应该退出循环，清理连接
                    return True
                    
        except Exception as e:
            logger.bind(tag=TAG).error(f"处理识别结果失败: {e}")
        
        return False

    async def _send_finalize(self):
        """发送 Finalize 消息"""
        if self.asr_ws and self._is_ws_connected():
            try:
                finalize_msg = {"type": "Finalize"}
                await self.asr_ws.send(json.dumps(finalize_msg))
                logger.bind(tag=TAG).debug("已发送 Finalize 消息")
            except Exception as e:
                logger.bind(tag=TAG).error(f"发送 Finalize 失败: {e}")

    async def _send_stop_request(self):
        """发送停止请求（用于手动模式下通知 ASR 结束识别）"""
        await self._send_finalize()

    async def _cleanup(self):
        """清理资源"""
        logger.bind(tag=TAG).debug(
            f"开始 Deepgram 会话清理 | 当前状态: processing={self.is_processing}, "
            f"connected={self.is_connected}"
        )

        # 状态重置
        self.is_processing = False
        self.is_connected = False
        
        # 取消 KeepAlive 任务
        if self.keepalive_task and not self.keepalive_task.done():
            self.keepalive_task.cancel()
            try:
                await self.keepalive_task
            except asyncio.CancelledError:
                pass
            self.keepalive_task = None

        # 关闭 WebSocket 连接
        if self.asr_ws:
            try:
                if self.asr_ws.state == State.OPEN:
                    await asyncio.wait_for(self.asr_ws.close(), timeout=2.0)
                logger.bind(tag=TAG).debug("Deepgram WebSocket 连接已关闭")
            except Exception as e:
                logger.bind(tag=TAG).error(f"关闭 WebSocket 连接失败: {e}")
            finally:
                self.asr_ws = None

        # 清理任务引用
        self.forward_task = None
        
        logger.bind(tag=TAG).debug("Deepgram 会话清理完成")

    async def speech_to_text(self, opus_data, session_id, audio_format):
        """获取识别结果"""
        result = self.text
        self.text = ""
        return result, None

    async def close(self):
        """关闭资源"""
        await self._cleanup()
        if hasattr(self, 'decoder') and self.decoder is not None:
            try:
                del self.decoder
                self.decoder = None
                logger.bind(tag=TAG).debug("Deepgram decoder 资源已释放")
            except Exception as e:
                logger.bind(tag=TAG).debug(f"释放 Deepgram decoder 资源时出错: {e}")

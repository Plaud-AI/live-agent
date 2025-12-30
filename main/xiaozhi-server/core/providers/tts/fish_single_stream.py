import queue
import asyncio
import traceback
import time
import httpx
import threading
from concurrent.futures import ThreadPoolExecutor
from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.providers.tts.base import TTSProviderBase
from core.utils import opus_encoder_utils, textUtils
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType, TTSAudioDTO, MessageTag
from fishaudio import FishAudio, TTSConfig

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    
    # Text segmentation punctuation sets
    #
    # HARD_PUNCTS: sentence-ending punctuation (safer boundaries)
    # SOFT_PUNCTS: clause boundaries (lower latency, may cut mid-sentence)
    #
    # Note:
    # - Include '.' for English sentences, but we skip decimal points like "1.5"
    # - Also include fullwidth dot '．' (U+FF0E) which may appear in some model outputs
    HARD_PUNCTS = (".", "。", "！", "？", "!", "?", "；", ";", "．")
    SOFT_PUNCTS = (",", "，", "：", ":", "\n")
    # First segment: allow both soft + hard for faster first audio
    FIRST_SEGMENT_PUNCTS = SOFT_PUNCTS + HARD_PUNCTS
    # Normal segments: prefer hard; optionally allow soft when segment is long enough
    NORMAL_PUNCTS = HARD_PUNCTS

    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        
        # Mark as streaming interface
        self.interface_type = InterfaceType.SINGLE_STREAM

        # Fish Audio configuration
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("FishSpeech API key is required")
        
        # Create httpx client with connection pool for reuse
        self._httpx_client = httpx.Client(
            base_url="https://api.fish.audio",  # Required for path-only requests
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            timeout=httpx.Timeout(60.0),
            http2=True,  # Enable HTTP/2 for better multiplexing
        )
        self._client = FishAudio(api_key=self.api_key, httpx_client=self._httpx_client)
        
        self.model = config.get("model", "speech-1.6")
        self.reference_id = config.get("reference_id")
        self.format = config.get("response_format", "pcm")
        # IMPORTANT: base-class to_tts()/to_tts_stream() uses audio_file_type to decide how to decode bytes.
        # FishAudio returns bytes in `response_format` (default pcm). If we keep base default "wav",
        # PCM would be treated as WAV and ffmpeg will fail with "invalid RIFF header".
        self.audio_file_type = self.format
        self.sample_rate = int(config.get("sample_rate", 16000))
        self.normalize = str(config.get("normalize", True)).lower() in ("true", "1", "yes")
        # FishAudio latency mode (keep backward-compatible default)
        self.latency_mode = config.get("latency_mode", "balanced")

        # Segmentation tuning (latency vs naturalness)
        # - max chars: hard cap to prevent pathological long segments (reduces TTS first-chunk spikes)
        # - soft punct min chars: avoid over-fragmentation at early commas
        #
        # 优化说明 (2024-12-30):
        # - first_soft_punct_min_chars: 从 0 改为 12，避免 "(calm) Ah," 等过短首句导致吞字
        # - soft_punct_min_chars: 从 25 改为 30，减少逗号处的过度分割
        # - 问题场景：LLM 输出 "(calm) Ah, a new presence..." 时
        #   原逻辑会在 "Ah," 处分割，导致 TTS 片段过短，设备端播放时吞字
        self.first_segment_max_chars = int(config.get("first_segment_max_chars", 120))
        self.segment_max_chars = int(config.get("segment_max_chars", 160))
        self.enable_soft_puncts = str(config.get("enable_soft_puncts", True)).lower() in ("true", "1", "yes")
        self.first_soft_punct_min_chars = int(config.get("first_soft_punct_min_chars", 12))  # 原值 0，优化为 12（阻止 "Ah," 等过短片段）
        self.soft_punct_min_chars = int(config.get("soft_punct_min_chars", 30))  # 原值 25，优化为 30

        # Prefetch configuration - 预加载深度（同时进行的 TTS 请求数）
        # 注意：FishSpeech API 可能有并发限制，建议设为 2 避免限速
        self.prefetch_depth = int(config.get("prefetch_depth", 2))

        # Initialize Opus encoder
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=self.sample_rate, channels=1, frame_size_ms=60
        )

        # PCM buffer for accumulating data before encoding
        self.pcm_buffer = bytearray()
        
        # Session state
        self._session_started = False
        
        # Disable base class first sentence handling (STT already sends start)
        self.tts_audio_first_sentence = False
        
        # Text buffer state
        self._text_buffer = ""
        self._processed_idx = 0
        
        # Prefetch state
        self._prefetch_buffers = {}  # segment_idx -> {"text": str, "audio_chunks": [], "done": Event, "error": Exception}
        self._prefetch_lock = threading.Lock()
        self._next_send_idx = 0  # 从 0 开始，所有句子都通过 prefetch 机制处理
        self._segment_idx = 0
        self._tts_executor = None
        
        # 首句流式发送状态 (segment 0 使用流式模式，边接收边发送)
        self._first_segment_streaming = False
        self._first_segment_audio_queue = queue.Queue()  # 首句音频队列
        self._first_segment_done = threading.Event()

    def _get_tts_executor(self):
        """懒加载 TTS 线程池"""
        if self._tts_executor is None:
            self._tts_executor = ThreadPoolExecutor(
                max_workers=self.prefetch_depth,
                thread_name_prefix="TTS-Prefetch"
            )
        return self._tts_executor

    def tts_text_priority_thread(self):
        """Streaming text processing thread with prefetch pipeline.
        
        Lifecycle alignment:
        - tts_text_queue FIRST -> initialize session
        - tts_text_queue TEXT -> extract segments, prefetch TTS
        - tts_text_queue LAST -> flush remaining, send LAST
        
        Prefetch mechanism:
        - Multiple segments can be processed in parallel
        - Audio is sent in order (segment 0, then 1, then 2...)
        - First segment is streamed directly for low latency
        - Subsequent segments are prefetched while previous ones play
        """
        while not self.conn.stop_event.is_set():
            try:
                # 尝试处理已完成的预加载任务（即使没有新消息）
                self._flush_completed_prefetch()
                
                try:
                    message = self.tts_text_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Handle FIRST - session start
                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False
                    self._text_buffer = ""
                    self._processed_idx = 0
                    self._session_started = False
                    self.pcm_buffer.clear()
                    self.conn._latency_tts_first_text_time = None
                    
                    # 设置首句标志，用于触发 sendAudioHandle 中的流控重置
                    # tts start 的发送由 sendAudioHandle.py 统一处理
                    self.tts_audio_first_sentence = True
                    
                    # 清理预加载状态
                    # 现在所有句子都通过 prefetch 机制处理，_next_send_idx 从 0 开始
                    with self._prefetch_lock:
                        self._prefetch_buffers.clear()
                        self._next_send_idx = 0  # 从 0 开始
                        self._segment_idx = 0
                    
                    # 清理首句流式状态
                    self._first_segment_streaming = False
                    self._first_segment_done.clear()
                    # 清空首句音频队列
                    while not self._first_segment_audio_queue.empty():
                        try:
                            self._first_segment_audio_queue.get_nowait()
                        except queue.Empty:
                            break
                    
                    logger.bind(tag=TAG).debug("TTS session initialized (prefetch enabled)")
                    continue
                
                # Check for abort
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("Received abort signal, skipping TTS processing")
                    # If session was started, send LAST to close it
                    if self._session_started:
                        self.tts_audio_queue.put(TTSAudioDTO(
                            sentence_type=SentenceType.LAST,
                            audio_data=None,
                            text=None,
                            message_tag=self._message_tag,
                        ))
                        self._session_started = False
                    # 清理预加载
                    with self._prefetch_lock:
                        self._prefetch_buffers.clear()
                    continue
                
                # Handle TEXT content
                if ContentType.TEXT == message.content_type:
                    self._text_buffer += message.content_detail
                    
                    # 提取所有可用的句子
                    while True:
                        segment = self._extract_segment()
                        if not segment:
                            break
                        
                        # Record TTS first text input time (for latency tracking)
                        if self.conn._latency_tts_first_text_time is None:
                            self.conn._latency_tts_first_text_time = time.time() * 1000
                            logger.bind(tag=TAG).debug("📝 [Latency] TTS received first text")
                        
                        # 【核心优化】所有句子都立即提交到后台线程
                        # 首句 (segment 0) 使用流式模式，后续句子使用缓冲模式
                        # 这样消息处理循环永不阻塞，后续句子可以尽早开始 prefetch
                        self._submit_prefetch_async(segment)
                    
                    # 尝试发送已完成的预加载
                    self._flush_completed_prefetch()
                    
                    # 首句流式发送（非阻塞，从队列读取已接收的 chunk）
                    self._send_first_segment_chunks()
                
                # Handle LAST - session end
                if message.sentence_type == SentenceType.LAST:
                    # Process remaining text
                    remaining = self._text_buffer[self._processed_idx:]
                    if remaining.strip():
                        segment = textUtils.get_string_no_punctuation_or_emoji(remaining)
                        if segment:
                            # 统一使用非阻塞提交
                            self._submit_prefetch_async(segment)
                    
                    # 等待所有预加载完成并发送
                    self._flush_all_prefetch()
                    
                    # Send LAST to audio queue
                    self.tts_audio_queue.put(TTSAudioDTO(
                        sentence_type=SentenceType.LAST,
                        audio_data=None,
                        text=None,
                        message_tag=self._message_tag,
                    ))
                    
                    self._session_started = False
                    logger.bind(tag=TAG).debug("TTS session ended")

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"TTS text processing failed: {str(e)}, type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )

    def _submit_prefetch_async(self, text: str):
        """提交句子到后台线程（非阻塞）
        
        首句 (segment_idx=0) 使用流式模式，边接收边发送
        后续句子使用缓冲模式，等待完成后按顺序发送
        """
        segment_idx = self._segment_idx
        self._segment_idx += 1
        
        is_first_segment = (segment_idx == 0)
        
        # 创建预加载缓冲区
        with self._prefetch_lock:
            self._prefetch_buffers[segment_idx] = {
                "text": text,
                "audio_chunks": [],
                "done": threading.Event(),
                "error": None,
                "first_chunk_time": None,
                "is_streaming": is_first_segment,  # 首句使用流式模式
            }
        
        if is_first_segment:
            self._first_segment_streaming = True
            self._first_segment_done.clear()
            logger.bind(tag=TAG).debug(f"🚀 [Stream] Submitted first segment: {text[:30]}...")
        else:
            logger.bind(tag=TAG).debug(f"📦 [Prefetch] Submitted segment {segment_idx}: {text[:30]}...")
        
        # 提交到线程池
        executor = self._get_tts_executor()
        executor.submit(self._prefetch_tts_worker, text, segment_idx)
    
    def _send_first_segment_chunks(self):
        """发送首句已接收的音频 chunk（非阻塞）
        
        从首句音频队列中读取已接收的 chunk 并发送
        不等待 TTS 完成，只发送当前可用的数据
        """
        if not self._first_segment_streaming:
            return
        
        chunks_sent = 0
        while True:
            try:
                item = self._first_segment_audio_queue.get_nowait()
            except queue.Empty:
                break
            
            if item is None:
                # None 表示首句流式处理完成
                self._first_segment_streaming = False
                self._first_segment_done.set()
                # 更新 _next_send_idx，准备发送后续句子
                with self._prefetch_lock:
                    self._next_send_idx = 1
                logger.bind(tag=TAG).debug(f"✅ [Stream] First segment streaming completed, sent {chunks_sent} chunks")
                break
            
            # 发送音频 chunk
            opus_data, text = item
            if chunks_sent == 0 and text:
                # 首个 chunk 发送 FIRST（触发 sentence_start）
                self.tts_audio_queue.put(TTSAudioDTO(
                    sentence_type=SentenceType.FIRST,
                    audio_data=None,
                    text=text,
                    message_tag=self._message_tag,
                ))
                self._session_started = True
            
            if opus_data:
                self.tts_audio_queue.put(TTSAudioDTO(
                    sentence_type=SentenceType.MIDDLE,
                    audio_data=opus_data,
                    text=None,
                    message_tag=self._message_tag,
                ))
                chunks_sent += 1
    
    def _submit_prefetch(self, text: str):
        """提交句子到预加载队列（旧接口，兼容性保留）"""
        self._submit_prefetch_async(text)

    def _prefetch_tts_worker(self, text: str, segment_idx: int):
        """预加载工作线程：获取 TTS 音频
        
        每个线程使用独立的 Opus 编码器实例，避免线程安全问题
        
        首句 (segment_idx=0) 使用流式模式：
        - 边接收边放入 _first_segment_audio_queue
        - 消息处理线程从队列读取并发送，实现最低延迟
        
        后续句子使用缓冲模式：
        - 缓冲所有 chunk 到 audio_chunks
        - 完成后标记 done，等待按顺序发送
        """
        original_text = text
        text = MarkdownCleaner.clean_markdown(text)
        
        # 判断是否为首句流式模式
        is_streaming = False
        with self._prefetch_lock:
            if segment_idx in self._prefetch_buffers:
                is_streaming = self._prefetch_buffers[segment_idx].get("is_streaming", False)
        
        if not text.strip():
            if is_streaming:
                # 首句为空，发送结束信号
                self._first_segment_audio_queue.put(None)
            with self._prefetch_lock:
                if segment_idx in self._prefetch_buffers:
                    self._prefetch_buffers[segment_idx]["done"].set()
            return
        
        start_time = time.time() * 1000
        
        # 创建独立的 Opus 编码器实例（线程安全）
        local_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=self.sample_rate, channels=1, frame_size_ms=60
        )
        
        # 计算每帧字节数
        frame_bytes = int(
            local_encoder.sample_rate
            * local_encoder.channels
            * local_encoder.frame_size_ms
            / 1000
            * 2
        )
        
        # 使用独立的 PCM 缓冲区
        pcm_buffer = bytearray()
        audio_chunks = []  # 仅用于后续句子的缓冲模式
        
        try:
            mode_tag = "Stream" if is_streaming else "Prefetch"
            logger.bind(tag=TAG).info(f"🔄 [{mode_tag}] TTS request: segment={segment_idx}, reference_id={self.reference_id}, text={text[:50]}...")
            
            audio_stream = self._client.tts.stream(
                text=text,
                reference_id=self.reference_id,
                model=self.model,
                config=TTSConfig(
                    format=self.format,
                    sample_rate=self.sample_rate,
                    normalize=self.normalize,
                    latency=self.latency_mode,
                ),
            )
            
            first_chunk_logged = False
            first_opus_sent = False
            
            for chunk in audio_stream:
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info(f"🛑 [{mode_tag}] Abort during TTS, segment={segment_idx}")
                    break
                
                # 记录首包时间
                if not first_chunk_logged:
                    first_chunk_logged = True
                    first_chunk_time = time.time() * 1000
                    api_latency = (first_chunk_time - start_time) / 1000
                    logger.bind(tag=TAG).info(f"⚡ [{mode_tag}] Segment {segment_idx} first chunk: {api_latency:.3f}s")
                    
                    # 更新 conn 的首包时间（用于延迟统计）
                    if is_streaming:
                        self.conn.tts_first_chunk_time = first_chunk_time
                    
                    with self._prefetch_lock:
                        if segment_idx in self._prefetch_buffers:
                            self._prefetch_buffers[segment_idx]["first_chunk_time"] = first_chunk_time
                
                # 累积 PCM 数据
                pcm_buffer.extend(chunk)
                
                # 编码完整帧（使用独立编码器）
                while len(pcm_buffer) >= frame_bytes:
                    frame = bytes(pcm_buffer[:frame_bytes])
                    del pcm_buffer[:frame_bytes]
                    
                    opus_data = self._encode_frame_with_encoder(local_encoder, frame, False)
                    if opus_data:
                        if is_streaming:
                            # 首句流式模式：直接放入队列
                            # 第一个 chunk 同时携带文本（用于触发 sentence_start）
                            if not first_opus_sent:
                                self._first_segment_audio_queue.put((opus_data, original_text))
                                first_opus_sent = True
                            else:
                                self._first_segment_audio_queue.put((opus_data, None))
                        else:
                            # 后续句子缓冲模式：存入列表
                            audio_chunks.append(opus_data)
            
            # 处理剩余数据
            if pcm_buffer and not self.conn.client_abort:
                opus_data = self._encode_frame_with_encoder(local_encoder, bytes(pcm_buffer), True)
                if opus_data:
                    if is_streaming:
                        if not first_opus_sent:
                            self._first_segment_audio_queue.put((opus_data, original_text))
                        else:
                            self._first_segment_audio_queue.put((opus_data, None))
                    else:
                        audio_chunks.append(opus_data)
            
            elapsed = (time.time() * 1000 - start_time) / 1000
            logger.bind(tag=TAG).info(f"✅ [{mode_tag}] Segment {segment_idx} completed in {elapsed:.3f}s")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"❌ [Prefetch] Segment {segment_idx} error: {e}")
            with self._prefetch_lock:
                if segment_idx in self._prefetch_buffers:
                    self._prefetch_buffers[segment_idx]["error"] = e
        
        finally:
            # 清理编码器
            try:
                local_encoder.close()
            except Exception:
                pass
            
            if is_streaming:
                # 首句流式模式：发送结束信号
                self._first_segment_audio_queue.put(None)
            
            # 存储结果并标记完成
            with self._prefetch_lock:
                if segment_idx in self._prefetch_buffers:
                    self._prefetch_buffers[segment_idx]["audio_chunks"] = audio_chunks
                    self._prefetch_buffers[segment_idx]["done"].set()

    def _encode_frame_with_encoder(self, encoder, pcm_data: bytes, end_of_stream: bool = False) -> bytes:
        """使用指定编码器编码 PCM 帧为 Opus"""
        result = []
        
        def callback(opus_data):
            result.append(opus_data)
        
        encoder.encode_pcm_to_opus_stream(
            pcm_data, end_of_stream=end_of_stream, callback=callback
        )
        
        return result[0] if result else None

    def _flush_completed_prefetch(self):
        """发送已完成的预加载结果（按顺序）
        
        注意：首句 (segment 0) 通过流式队列处理，这里只处理 segment >= 1
        必须等待首句流式完成后才开始处理后续句子
        """
        # 首句尚未完成，不处理后续句子
        if self._first_segment_streaming:
            return
        
        while True:
            with self._prefetch_lock:
                # 检查下一个要发送的段落是否就绪（从 segment 1 开始）
                if self._next_send_idx not in self._prefetch_buffers:
                    break
                
                buffer = self._prefetch_buffers[self._next_send_idx]
                
                # 跳过首句（已通过流式队列处理）
                if buffer.get("is_streaming", False):
                    segment_idx = self._next_send_idx
                    self._next_send_idx += 1
                    del self._prefetch_buffers[segment_idx]
                    continue
                
                # 如果还没完成，等待
                if not buffer["done"].is_set():
                    break
                
                # 取出并删除缓冲区
                segment_idx = self._next_send_idx
                self._next_send_idx += 1
                del self._prefetch_buffers[segment_idx]
            
            # 发送结果（在锁外操作）
            self._send_prefetch_result(buffer)

    def _flush_all_prefetch(self):
        """等待并发送所有剩余的预加载结果
        
        在会话结束时调用，确保所有音频都发送完毕
        """
        # 首先等待首句流式完成（如果还在进行中）
        if self._first_segment_streaming:
            logger.bind(tag=TAG).debug("Waiting for first segment streaming to complete...")
            self._first_segment_done.wait(timeout=30)
            # 发送首句队列中剩余的 chunk
            self._send_first_segment_chunks()
        
        while True:
            with self._prefetch_lock:
                if self._next_send_idx not in self._prefetch_buffers:
                    break
                
                buffer = self._prefetch_buffers[self._next_send_idx]
            
            # 跳过首句（已通过流式队列处理）
            if buffer.get("is_streaming", False):
                with self._prefetch_lock:
                    segment_idx = self._next_send_idx
                    self._next_send_idx += 1
                    if segment_idx in self._prefetch_buffers:
                        del self._prefetch_buffers[segment_idx]
                continue
            
            # 等待完成
            buffer["done"].wait(timeout=30)
            
            with self._prefetch_lock:
                if self._next_send_idx in self._prefetch_buffers:
                    segment_idx = self._next_send_idx
                    self._next_send_idx += 1
                    del self._prefetch_buffers[segment_idx]
            
            # 发送结果
            self._send_prefetch_result(buffer)

    def _send_prefetch_result(self, buffer: dict):
        """发送预加载结果到音频队列"""
        text = buffer["text"]
        audio_chunks = buffer["audio_chunks"]
        error = buffer["error"]
        
        if error:
            logger.bind(tag=TAG).warning(f"Skipping segment due to prefetch error: {error}")
            return
        
        if not audio_chunks:
            logger.bind(tag=TAG).debug(f"Skipping empty segment: {text[:30]}...")
            return
        
        # 发送 FIRST（触发 sentence_start）
        self.tts_audio_queue.put(TTSAudioDTO(
            sentence_type=SentenceType.FIRST,
            audio_data=None,
            text=text,
            message_tag=self._message_tag,
        ))
        self._session_started = True
        
        # 发送所有音频块
        for opus_data in audio_chunks:
            if self.conn.client_abort:
                break
            self.tts_audio_queue.put(TTSAudioDTO(
                sentence_type=SentenceType.MIDDLE,
                audio_data=opus_data,
                text=None,
                message_tag=self._message_tag,
            ))
        
        logger.bind(tag=TAG).debug(f"📤 [Prefetch] Sent segment: {text[:30]}... ({len(audio_chunks)} chunks)")

    def _stream_tts_segment(self, text: str):
        """[DEPRECATED] 同步阻塞式 TTS streaming.
        
        此方法已被 _prefetch_tts_worker + _first_segment_audio_queue 机制取代。
        保留此代码用于参考和回滚。
        
        问题：此方法会阻塞消息处理线程，导致后续句子无法并行 prefetch。
        """
        text = MarkdownCleaner.clean_markdown(text)
        if not text.strip():
            return
        
        logger.bind(tag=TAG).info(f"FishSpeech streaming (first segment): {text}")
        start_time = time.time() * 1000
        first_chunk_logged = False  # Track first chunk for this segment
        
        # Calculate bytes per frame for Opus encoding
        frame_bytes = int(
            self.opus_encoder.sample_rate
            * self.opus_encoder.channels
            * self.opus_encoder.frame_size_ms
            / 1000
            * 2  # 16-bit = 2 bytes per sample
        )
        
        try:
            # Get audio stream from FishSpeech
            logger.bind(tag=TAG).info(f"TTS stream request: reference_id={self.reference_id}, text={text[:50]}...")
            audio_stream = self._client.tts.stream(
                text=text,
                reference_id=self.reference_id,
                model=self.model,
                config=TTSConfig(
                    format=self.format,
                    sample_rate=self.sample_rate,
                    normalize=self.normalize,
                    latency=self.latency_mode,
                ),
            )
            
            # Send FIRST for each text segment (triggers sentence_start on client)
            # This ensures client receives all text segments, not just the first one
            self.tts_audio_queue.put(TTSAudioDTO(
                sentence_type=SentenceType.FIRST,
                audio_data=None,
                text=text,
                message_tag=self._message_tag,
            ))
            self._session_started = True
            
            # Process audio stream chunks
            for chunk in audio_stream:
                # Check for abort during streaming
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("Abort during TTS streaming, stopping")
                    break
                
                # Log first chunk latency for each segment
                if not first_chunk_logged:
                    first_chunk_logged = True
                    first_chunk_time = time.time() * 1000
                    self.conn.tts_first_chunk_time = first_chunk_time
                    api_latency = (first_chunk_time - start_time) / 1000
                    logger.bind(tag=TAG).info(f"[Latency] TTS segment first chunk: {api_latency:.3f}s")
                
                # Add chunk to PCM buffer
                self.pcm_buffer.extend(chunk)
                
                # Encode and send complete frames as MIDDLE messages
                while len(self.pcm_buffer) >= frame_bytes:
                    # Check abort again before processing
                    if self.conn.client_abort:
                        break
                    
                    frame = bytes(self.pcm_buffer[:frame_bytes])
                    del self.pcm_buffer[:frame_bytes]
                    
                    self.opus_encoder.encode_pcm_to_opus_stream(
                        frame, end_of_stream=False, callback=self._handle_opus_middle
                    )
            
            # Flush remaining data (less than one frame)
            if self.pcm_buffer and not self.conn.client_abort:
                self.opus_encoder.encode_pcm_to_opus_stream(
                    bytes(self.pcm_buffer),
                    end_of_stream=True,
                    callback=self._handle_opus_middle,
                )
                self.pcm_buffer.clear()
            
            elapsed = (time.time() * 1000 - start_time) / 1000
            logger.bind(tag=TAG).debug(f"TTS segment completed in {elapsed:.3f}s: {text[:30]}...")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"FishSpeech streaming error: {e}")
            # On error, clear buffer to avoid corrupted audio
            self.pcm_buffer.clear()

    def _handle_opus_middle(self, opus_data: bytes):
        """Handle encoded Opus data, send as MIDDLE message"""
        if self.conn.client_abort:
            return
        
        self.tts_audio_queue.put(TTSAudioDTO(
            sentence_type=SentenceType.MIDDLE,
            audio_data=opus_data,
            text=None,
            message_tag=self._message_tag,
        ))

    def _extract_segment(self) -> str | None:
        """Extract next text segment based on punctuation.
        
        Returns cleaned segment text or None if no complete segment found.
        """
        current_text = self._text_buffer[self._processed_idx:]
        if not current_text:
            return None
        
        is_first_segment = not self._session_started

        # Choose max length cap (prevent extremely long segments without punctuation)
        max_chars = (
            getattr(self, "first_segment_max_chars", 0)
            if is_first_segment
            else getattr(self, "segment_max_chars", 0)
        )
        if max_chars is None:
            max_chars = 0
        if max_chars < 0:
            max_chars = 0

        # Helper: find first dot that isn't a decimal point or part of ellipsis (supports '.' and '．')
        def _find_first_non_decimal_dot(text: str, dot_char: str, start_pos: int) -> int:
            pos = max(start_pos, 0)
            while True:
                pos = text.find(dot_char, pos)
                if pos == -1:
                    return -1
                prev_ch = text[pos - 1] if pos - 1 >= 0 else ""
                next_ch = text[pos + 1] if pos + 1 < len(text) else ""
                # Skip decimal points (e.g., "1.5")
                if prev_ch.isdigit() and next_ch.isdigit():
                    pos += 1
                    continue
                # Skip ellipsis: if next char is also a dot, skip this one
                # This handles "..." or "...." patterns
                if next_ch == dot_char:
                    pos += 1
                    continue
                # Skip if this dot follows another dot (part of ellipsis)
                if prev_ch == dot_char:
                    pos += 1
                    continue
                return pos

        def _find_first_punct(text: str, puncts: tuple[str, ...], start_pos: int) -> int:
            earliest = -1
            for punct in puncts:
                if punct in (".", "．"):
                    pos = _find_first_non_decimal_dot(text, punct, start_pos)
                else:
                    pos = text.find(punct, start_pos)
                if pos != -1 and (earliest == -1 or pos < earliest):
                    earliest = pos
            return earliest

        # 1) Always try hard puncts (sentence boundaries)
        hard_pos = _find_first_punct(current_text, self.HARD_PUNCTS, 0)

        # 2) Optionally allow soft puncts (commas/colons/newlines) for lower latency
        soft_pos = -1
        if is_first_segment:
            # First segment: always allow soft puncts (min chars configurable; default 0 to allow "Oh,")
            min_chars = max(int(getattr(self, "first_soft_punct_min_chars", 0)), 0)
            soft_pos = _find_first_punct(current_text, self.SOFT_PUNCTS, max(min_chars - 1, 0))
        elif getattr(self, "enable_soft_puncts", True):
            min_chars = max(int(getattr(self, "soft_punct_min_chars", 0)), 0)
            soft_pos = _find_first_punct(current_text, self.SOFT_PUNCTS, max(min_chars - 1, 0))

        # Pick the earliest boundary we can use
        split_pos = -1
        if hard_pos != -1 and (soft_pos == -1 or hard_pos <= soft_pos):
            split_pos = hard_pos
        elif soft_pos != -1:
            split_pos = soft_pos

        if split_pos != -1:
            segment_raw = current_text[: split_pos + 1]
            self._processed_idx += len(segment_raw)
            return textUtils.get_string_no_punctuation_or_emoji(segment_raw)

        # 3) Fallback: no punctuation found, but segment is too long → force cut to avoid TTS latency spikes
        if max_chars > 0 and len(current_text) >= max_chars:
            # Prefer cutting at whitespace before max_chars
            window = current_text[:max_chars]
            cut_at = window.rfind(" ")
            if cut_at <= 0:
                # No whitespace (e.g., Chinese) → cut hard at max_chars
                cut_at = max_chars

            # Consume the cut segment plus subsequent whitespace (so next segment doesn't start with spaces)
            consume_len = cut_at
            while consume_len < len(current_text) and current_text[consume_len].isspace():
                consume_len += 1

            segment_raw = current_text[:cut_at]
            self._processed_idx += consume_len
            return textUtils.get_string_no_punctuation_or_emoji(segment_raw)

        return None

    def _audio_play_priority_thread(self):
        """Override base class to accumulate all segments into one report.
        
        - Each FIRST still triggers sentence_start on client (for real-time display)
        - But report accumulates all text segments and audio, only reports on LAST
        """
        from core.utils.output_counter import add_device_output
        from core.handle.reportHandle import enqueue_tts_report
        from core.handle.sendAudioHandle import sendAudioMessage
        from core.utils.opus import pack_opus_with_header
        
        # Accumulated text and audio for the entire session (one LLM response)
        session_text_parts = []
        session_audio = []
        session_message_tag = MessageTag.NORMAL
        
        # Track last send future for ordering
        last_send_future = None
        
        while not self.conn.stop_event.is_set():
            text = None
            try:
                try:
                    tts_audio_message = self.tts_audio_queue.get(timeout=0.1)
                    if isinstance(tts_audio_message, TTSAudioDTO):
                        sentence_type = tts_audio_message.sentence_type
                        audio_datas = tts_audio_message.audio_data
                        text = tts_audio_message.text
                        message_tag = tts_audio_message.message_tag
                    elif isinstance(tts_audio_message, tuple):
                        sentence_type = tts_audio_message[0]
                        audio_datas = tts_audio_message[1]
                        text = tts_audio_message[2]
                        message_tag = MessageTag.NORMAL
                    else:
                        logger.bind(tag=TAG).warning(f"Unknown tts_audio_message type: {type(tts_audio_message)}")
                        continue
                except queue.Empty:
                    if self.conn.stop_event.is_set():
                        break
                    continue

                if self.conn.client_abort:
                    # Only handle abort once per session
                    if session_text_parts or session_audio:
                        logger.bind(tag=TAG).debug("Received abort, reporting accumulated content")
                        full_text = "".join(session_text_parts)
                        if full_text and session_audio:
                            enqueue_tts_report(self.conn, full_text, session_audio, session_message_tag)
                            logger.bind(tag=TAG).info(f"Abort report: {full_text[:50]}...")
                        
                        # 清空队列中的所有待处理消息，避免 stop 后继续发送
                        # 注意：这不会丢失正常数据，因为：
                        # 1. client_abort=True 只在用户主动打断时设置
                        # 2. 被清空的音频属于被打断的会话，用户已不需要
                        # 3. 新会话开始时 client_abort 会被重置为 False
                        while not self.tts_audio_queue.empty():
                            try:
                                self.tts_audio_queue.get_nowait()
                            except queue.Empty:
                                break
                        
                        # Send LAST to trigger TTS stop message
                        last_send_future = asyncio.run_coroutine_threadsafe(
                            sendAudioMessage(self.conn, SentenceType.LAST, None, None, session_message_tag),
                            self.conn.loop,
                        )
                        session_text_parts, session_audio = [], []
                    continue

                # Handle FIRST: accumulate text, don't report yet
                if sentence_type == SentenceType.FIRST:
                    if text:
                        session_text_parts.append(text)
                    session_message_tag = message_tag

                # Handle MIDDLE: accumulate audio
                if isinstance(audio_datas, bytes):
                    audio_with_header = pack_opus_with_header(audio_datas, message_tag)
                    session_audio.append(audio_with_header)

                # Handle LAST: report the entire accumulated session
                if sentence_type == SentenceType.LAST:
                    if session_text_parts or session_audio:
                        full_text = "".join(session_text_parts)
                        if full_text and session_audio:
                            enqueue_tts_report(self.conn, full_text, session_audio, session_message_tag)
                            logger.bind(tag=TAG).info(f"Session report: {full_text[:80]}...")
                    session_text_parts, session_audio = [], []

                # Wait for previous send to complete (maintain order)
                if last_send_future is not None:
                    try:
                        last_send_future.result(timeout=5.0)
                    except Exception as e:
                        logger.bind(tag=TAG).warning(f"Previous audio send timeout: {e}")

                # Send audio to client (async, non-blocking)
                last_send_future = asyncio.run_coroutine_threadsafe(
                    sendAudioMessage(self.conn, sentence_type, audio_datas, text, message_tag),
                    self.conn.loop,
                )

                # Track output
                if self.conn.max_output_size > 0 and text:
                    add_device_output(self.conn.headers.get("device-id"), len(text))

            except Exception as e:
                logger.bind(tag=TAG).error(f"_audio_play_priority_thread error: {text} {e}")

        # Wait for last send to complete before exiting
        if last_send_future is not None:
            try:
                last_send_future.result(timeout=2.0)
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Final audio send failed (connection may be closed): {e}")
        
        # On connection close, report remaining accumulated data
        if session_text_parts and session_audio:
            try:
                full_text = "".join(session_text_parts)
                enqueue_tts_report(self.conn, full_text, session_audio, session_message_tag)
                logger.bind(tag=TAG).info(f"Connection close report: {full_text}")
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Connection close report failed: {e}")

    async def text_to_speak(self, text, output_file):
        """Non-streaming TTS interface (required by base class)
        
        This provider primarily uses streaming, but this method is needed
        for compatibility with base class abstract method.
        """
        text = MarkdownCleaner.clean_markdown(text)
        audio_bytes = self._client.tts.convert(
            text=text,
            reference_id=self.reference_id,
            model=self.model,
            config=TTSConfig(
                format=self.format,
                sample_rate=self.sample_rate,
                normalize=self.normalize,
                latency=self.latency_mode,
            )
        )
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(audio_bytes)
        return audio_bytes

    async def close(self):
        """Resource cleanup"""
        await super().close()
        if hasattr(self, "opus_encoder"):
            self.opus_encoder.close()
        if hasattr(self, "_client"):
            self._client.close()
        if hasattr(self, "_httpx_client"):
            self._httpx_client.close()
        if hasattr(self, "_tts_executor") and self._tts_executor:
            self._tts_executor.shutdown(wait=False)

import queue
import asyncio
import traceback
import time
import httpx
from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.providers.tts.base import TTSProviderBase
from core.utils import opus_encoder_utils, textUtils
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType, TTSAudioDTO, MessageTag
from fishaudio import FishAudio, TTSConfig

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    
    # Punctuation sets for text segmentation
    # First segment: use aggressive punctuation for faster response
    FIRST_SEGMENT_PUNCTS = (",", "，", "。", "！", "？", "!", "?", "；", ";", "：", ":")
    # Normal segments: use sentence-ending punctuation
    NORMAL_PUNCTS = ("。", "！", "？", "!", "?", "；", ";")

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
        self.sample_rate = int(config.get("sample_rate", 16000))
        self.normalize = str(config.get("normalize", True)).lower() in ("true", "1", "yes")

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

    def tts_text_priority_thread(self):
        """Streaming text processing thread with lifecycle alignment:
        - tts_text_queue FIRST -> tts_audio_queue FIRST (session start)
        - tts_text_queue TEXT (MIDDLE) -> tts_audio_queue MIDDLE (audio chunks)
        - tts_text_queue LAST -> tts_audio_queue LAST (session end)
        """
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                
                # Handle FIRST - session start
                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False
                    self._text_buffer = ""
                    self._processed_idx = 0
                    self._session_started = False
                    self.pcm_buffer.clear()
                    self.conn._latency_tts_first_text_time = None
                    logger.bind(tag=TAG).debug("TTS session initialized")
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
                    continue
                
                # Handle TEXT content
                if ContentType.TEXT == message.content_type:
                    self._text_buffer += message.content_detail
                    
                    # Try to extract and process segments
                    while True:
                        segment = self._extract_segment()
                        if not segment:
                            break
                        
                        # Record TTS first text input time (for latency tracking)
                        if self.conn._latency_tts_first_text_time is None:
                            self.conn._latency_tts_first_text_time = time.time() * 1000
                            logger.bind(tag=TAG).debug("📝 [Latency] TTS received first text")
                        
                        self._stream_tts_segment(segment)
                
                # Handle LAST - session end
                if message.sentence_type == SentenceType.LAST:
                    # Process remaining text
                    remaining = self._text_buffer[self._processed_idx:]
                    if remaining.strip():
                        segment = textUtils.get_string_no_punctuation_or_emoji(remaining)
                        if segment:
                            self._stream_tts_segment(segment)
                    
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

    def _stream_tts_segment(self, text: str):
        """Process a text segment with streaming TTS, sending audio chunks as MIDDLE messages"""
        text = MarkdownCleaner.clean_markdown(text)
        if not text.strip():
            return
        
        logger.bind(tag=TAG).info(f"FishSpeech streaming: {text}")
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
                    latency="balanced",
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
        
        logger.bind(tag=TAG).debug(f"Sending opus frame: {len(opus_data)} bytes")
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
        
        # Choose punctuation set: aggressive for first segment, normal for rest
        puncts = self.FIRST_SEGMENT_PUNCTS if not self._session_started else self.NORMAL_PUNCTS
        
        # Find earliest punctuation position
        earliest_pos = -1
        for punct in puncts:
            pos = current_text.find(punct)
            if pos != -1 and (earliest_pos == -1 or pos < earliest_pos):
                earliest_pos = pos
        
        if earliest_pos == -1:
            return None
        
        # Extract segment including punctuation
        segment_raw = current_text[:earliest_pos + 1]
        self._processed_idx += len(segment_raw)
        
        # Clean and return
        return textUtils.get_string_no_punctuation_or_emoji(segment_raw)

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
                latency="balanced",
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

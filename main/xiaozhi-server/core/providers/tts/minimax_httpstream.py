import os
import json
import time
import queue
import asyncio
import requests
import traceback
from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.utils.util import parse_string_to_list
from core.providers.tts.base import TTSProviderBase
from core.utils import opus_encoder_utils, textUtils
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType, TTSAudioDTO, MessageTag

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    
    # Punctuation sets for text segmentation
    # First segment: use aggressive punctuation for faster response
    FIRST_SEGMENT_PUNCTS = (",", "，", "。", "！", "？", "!", "?", "；", ";", "：", ":")
    # Normal segments: use sentence-ending punctuation
    NORMAL_PUNCTS = ("。", "！", "？", "!", "?", "；", ";")
    
    # Fish Speech emotion tag to MiniMax emotion mapping
    # Fish tags from role.md: happy, sad, curious, surprised, calm
    # MiniMax emotions: happy, sad, angry, fearful, disgusted, surprised, calm, fluent, whisper
    EMOTION_MAP = {
        "happy": "happy",
        "sad": "sad", 
        "curious": "fluent",     # curious -> fluent (smooth, engaging tone)
        "surprised": "surprised",
        "calm": "calm",          # direct mapping
    }

    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        
        # Mark as streaming interface
        self.interface_type = InterfaceType.SINGLE_STREAM
        
        self.group_id = config.get("group_id")
        self.api_key = config.get("api_key")
        self.model = config.get("model", "speech-02-turbo")
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice_id")

        default_voice_setting = {
            "voice_id": "female-shaonv",
            "speed": 1,
            "vol": 1,
            "pitch": 0,
            "emotion": "happy",
        }
        default_pronunciation_dict = {"tone": ["处理/(chu3)(li3)", "危险/dangerous"]}
        default_audio_setting = {
            "sample_rate": 24000,
            "format": "pcm",
            "channel": 1,
        }
        self.voice_setting = {
            **default_voice_setting,
            **config.get("voice_setting", {}),
        }
        self.pronunciation_dict = {
            **default_pronunciation_dict,
            **config.get("pronunciation_dict", {}),
        }
        self.audio_setting = {**default_audio_setting, **config.get("audio_setting", {})}
        self.timber_weights = parse_string_to_list(config.get("timber_weights"))

        if self.voice:
            self.voice_setting["voice_id"] = self.voice

        # Use alternative endpoint for reduced TTFA (Time to First Audio)
        # https://platform.minimax.io/docs/api-reference/speech-t2a-http
        self.api_url = config.get("api_url", "https://api.minimax.io/v1/t2a_v2")
        self.header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.audio_file_type = default_audio_setting.get("format", "pcm")
        
        # Get sample rate from audio_setting for opus encoder
        self.sample_rate = int(self.audio_setting.get("sample_rate", 24000))

        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=self.sample_rate, channels=1, frame_size_ms=60
        )

        # PCM buffer
        self.pcm_buffer = bytearray()
        
        # Session state
        self._session_started = False
        
        # Disable base class first sentence handling (STT already sends start)
        self.tts_audio_first_sentence = False
        
        # Text buffer state
        self._text_buffer = ""
        self._processed_idx = 0
        
        # Create requests session for connection reuse
        self._http_session = requests.Session()

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
                    self.before_stop_play_files.clear()
                    self.conn._latency_tts_first_text_time = None
                    self._message_tag = message.message_tag
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
                
                # Handle FILE content
                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"Adding audio file to playlist: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        # Process audio file data
                        self._process_audio_file_stream(
                            message.content_file,
                            callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail)
                        )
                
                # Handle LAST - session end
                if message.sentence_type == SentenceType.LAST:
                    # Process remaining text
                    remaining = self._text_buffer[self._processed_idx:]
                    if remaining.strip():
                        segment = textUtils.get_string_no_punctuation_or_emoji(remaining)
                        if segment:
                            self._stream_tts_segment(segment)
                    
                    # Process any pending audio files
                    self._process_before_stop_play_files_stream()

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"TTS text processing failed: {str(e)}, type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )

    def _stream_tts_segment(self, text: str):
        """Process a text segment with streaming TTS using synchronous HTTP requests.
        
        MiniMax T2A HTTP API is a synchronous API with stream mode.
        Reference: https://platform.minimax.io/docs/api-reference/speech-t2a-http
        
        Handles Fish Speech emotion tags by:
        1. Extracting emotion tag from text (e.g., "(happy) Hello!")
        2. Mapping to MiniMax emotion parameter
        3. Removing tag from text before synthesis
        """
        text = MarkdownCleaner.clean_markdown(text)
        if not text.strip():
            return
        
        # Extract and map emotion tag from Fish Speech format
        emotion, clean_text = textUtils.extract_emotion_tag(text)
        minimax_emotion = None
        if emotion:
            minimax_emotion = self.EMOTION_MAP.get(emotion)
            if minimax_emotion:
                logger.bind(tag=TAG).debug(f"Emotion tag mapped: ({emotion}) -> {minimax_emotion}")
            text = clean_text  # Use text without emotion tag
        
        if not text.strip():
            return
        
        logger.bind(tag=TAG).info(f"MiniMax streaming: {text[:50]}...")
        start_time = time.time() * 1000
        first_chunk_logged = False
        
        # Calculate bytes per frame for Opus encoding
        frame_bytes = int(
            self.opus_encoder.sample_rate
            * self.opus_encoder.channels
            * self.opus_encoder.frame_size_ms
            / 1000
            * 2  # 16-bit = 2 bytes per sample
        )
        
        # Build voice_setting with emotion if detected
        voice_setting = self.voice_setting.copy()
        if minimax_emotion:
            voice_setting["emotion"] = minimax_emotion
        
        payload = {
            "model": self.model,
            "text": text,
            "stream": True,
            "voice_setting": voice_setting,
            "pronunciation_dict": self.pronunciation_dict,
            "audio_setting": self.audio_setting,
        }

        if type(self.timber_weights) is list and len(self.timber_weights) > 0:
            payload["timber_weights"] = self.timber_weights
            payload["voice_setting"]["voice_id"] = ""

        try:
            # Use synchronous requests with stream=True for SSE response
            with self._http_session.post(
                self.api_url,
                headers=self.header,
                data=json.dumps(payload),
                timeout=30,
                stream=True,
            ) as resp:
                if resp.status_code != 200:
                    logger.bind(tag=TAG).error(
                        f"TTS request failed: {resp.status_code}, {resp.text}"
                    )
                    return

                self.pcm_buffer.clear()
                
                # Send FIRST for each text segment (triggers sentence_start on client)
                self.tts_audio_queue.put(TTSAudioDTO(
                    sentence_type=SentenceType.FIRST,
                    audio_data=None,
                    text=text,
                    message_tag=self._message_tag,
                ))
                self._session_started = True

                # Process SSE (Server-Sent Events) stream
                # Format: data: {"data": {"audio": "<hex>", "status": 1}, ...}\n\n
                buffer = b""
                for chunk in resp.iter_content(chunk_size=4096):
                    # Check for abort during streaming
                    if self.conn.client_abort:
                        logger.bind(tag=TAG).info("Abort during TTS streaming, stopping")
                        break
                    
                    if not chunk:
                        continue

                    buffer += chunk
                    
                    # Parse SSE data blocks
                    while True:
                        # Find data block delimiter
                        header_pos = buffer.find(b"data: ")
                        if header_pos == -1:
                            break

                        end_pos = buffer.find(b"\n\n", header_pos)
                        if end_pos == -1:
                            break

                        # Extract single complete JSON block
                        json_str = buffer[header_pos + 6 : end_pos].decode("utf-8")
                        buffer = buffer[end_pos + 2 :]

                        try:
                            data = json.loads(json_str)
                            status = data.get("data", {}).get("status", 1)
                            audio_hex = data.get("data", {}).get("audio")

                            # Only process status=1 valid audio blocks, ignore status=2 summary blocks
                            if status == 1 and audio_hex:
                                # Log first chunk latency
                                if not first_chunk_logged:
                                    first_chunk_logged = True
                                    first_chunk_time = time.time() * 1000
                                    self.conn.tts_first_chunk_time = first_chunk_time
                                    api_latency = (first_chunk_time - start_time) / 1000
                                    logger.bind(tag=TAG).info(f"[Latency] TTS segment first chunk: {api_latency:.3f}s")
                                
                                pcm_data = bytes.fromhex(audio_hex)
                                self.pcm_buffer.extend(pcm_data)

                        except json.JSONDecodeError as e:
                            logger.bind(tag=TAG).error(f"JSON parse failed: {e}")
                            continue

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
            logger.bind(tag=TAG).error(f"MiniMax streaming error: {e}")
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

    def _process_before_stop_play_files_stream(self):
        """Process pending audio files and send LAST signal"""
        for audio_datas, text in self.before_stop_play_files:
            self.tts_audio_queue.put(TTSAudioDTO(
                sentence_type=SentenceType.MIDDLE,
                audio_data=audio_datas,
                text=text,
                message_tag=self._message_tag,
            ))
        self.before_stop_play_files.clear()
        
        # Send LAST to audio queue
        self.tts_audio_queue.put(TTSAudioDTO(
            sentence_type=SentenceType.LAST,
            audio_data=None,
            text=None,
            message_tag=self._message_tag,
        ))
        
        self._session_started = False
        logger.bind(tag=TAG).debug("TTS session ended")

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
        Uses synchronous HTTP request internally.
        """
        text = MarkdownCleaner.clean_markdown(text)
        
        payload = {
            "model": self.model,
            "text": text,
            "stream": True,
            "voice_setting": self.voice_setting,
            "pronunciation_dict": self.pronunciation_dict,
            "audio_setting": self.audio_setting,
        }

        if type(self.timber_weights) is list and len(self.timber_weights) > 0:
            payload["timber_weights"] = self.timber_weights
            payload["voice_setting"]["voice_id"] = ""

        try:
            with self._http_session.post(
                self.api_url,
                headers=self.header,
                data=json.dumps(payload),
                timeout=30,
                stream=True,
            ) as resp:
                if resp.status_code != 200:
                    logger.bind(tag=TAG).error(
                        f"TTS request failed: {resp.status_code}, {resp.text}"
                    )
                    return None

                # Collect all PCM data from SSE stream
                pcm_data = bytearray()
                buffer = b""
                for chunk in resp.iter_content(chunk_size=4096):
                    if not chunk:
                        continue
                    buffer += chunk
                    while True:
                        header_pos = buffer.find(b"data: ")
                        if header_pos == -1:
                            break
                        end_pos = buffer.find(b"\n\n", header_pos)
                        if end_pos == -1:
                            break
                        json_str = buffer[header_pos + 6 : end_pos].decode("utf-8")
                        buffer = buffer[end_pos + 2 :]
                        try:
                            data = json.loads(json_str)
                            if data.get('data', {}).get('status') == 1:
                                audio_hex = data['data']['audio']
                                pcm_data.extend(bytes.fromhex(audio_hex))
                        except (json.JSONDecodeError, KeyError):
                            continue
                
                if output_file:
                    # Write raw PCM data to file for compatibility
                    with open(output_file, 'wb') as f:
                        f.write(bytes(pcm_data))
                
                return bytes(pcm_data)

        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS request exception: {e}")
            return None

    def to_tts(self, text: str) -> list:
        """Non-streaming TTS processing for testing and audio file saving scenarios
        Args:
            text: Text to convert
        Returns:
            list: List of opus encoded audio data
        """
        start_time = time.time()
        text = MarkdownCleaner.clean_markdown(text)

        payload = {
            "model": self.model,
            "text": text,
            "stream": True,
            "voice_setting": self.voice_setting,
            "pronunciation_dict": self.pronunciation_dict,
            "audio_setting": self.audio_setting,
        }

        if type(self.timber_weights) is list and len(self.timber_weights) > 0:
            payload["timber_weights"] = self.timber_weights
            payload["voice_setting"]["voice_id"] = ""

        try:
            with self._http_session.post(
                self.api_url,
                headers=self.header,
                data=json.dumps(payload),
                timeout=30,
                stream=True,
            ) as response:
                if response.status_code != 200:
                    logger.bind(tag=TAG).error(
                        f"TTS request failed: {response.status_code}, {response.text}"
                    )
                    return []

                # Use opus encoder to process PCM data
                opus_datas = []
                pcm_data = bytearray()
                buffer = b""
                
                # Process SSE stream
                for chunk in response.iter_content(chunk_size=4096):
                    if not chunk:
                        continue
                    buffer += chunk
                    while True:
                        header_pos = buffer.find(b"data: ")
                        if header_pos == -1:
                            break
                        end_pos = buffer.find(b"\n\n", header_pos)
                        if end_pos == -1:
                            break
                        json_str = buffer[header_pos + 6 : end_pos].decode("utf-8")
                        buffer = buffer[end_pos + 2 :]
                        try:
                            data = json.loads(json_str)
                            if data.get('data', {}).get('status') == 1:
                                audio_hex = data['data']['audio']
                                pcm_data.extend(bytes.fromhex(audio_hex))
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.bind(tag=TAG).warning(f"Invalid data block: {e}")
                            continue

                logger.bind(tag=TAG).info(f"TTS request success: {text}, elapsed: {time.time() - start_time:.3f}s")

                # Calculate bytes per frame
                frame_bytes = int(
                    self.opus_encoder.sample_rate
                    * self.opus_encoder.channels
                    * self.opus_encoder.frame_size_ms
                    / 1000
                    * 2
                )

                # Process merged PCM data in frames
                for i in range(0, len(pcm_data), frame_bytes):
                    frame = bytes(pcm_data[i:i+frame_bytes])
                    if len(frame) < frame_bytes:
                        frame += b"\x00" * (frame_bytes - len(frame))
 
                    self.opus_encoder.encode_pcm_to_opus_stream(
                        frame,
                        end_of_stream=(i + frame_bytes >= len(pcm_data)),
                        callback=lambda opus: opus_datas.append(opus)
                    )

                return opus_datas

        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS request exception: {e}")
            return []

    async def close(self):
        """Resource cleanup"""
        await super().close()
        if hasattr(self, "opus_encoder"):
            self.opus_encoder.close()
        if hasattr(self, "_http_session"):
            self._http_session.close()

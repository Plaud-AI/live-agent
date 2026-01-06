"""
MiniMax Dual Stream TTS Implementation

Based on WebSocket API (wss://api.minimax.io/ws/v1/t2a_v2), supporting:
1. Pre-connection optimization: establish WebSocket connection before LLM output
2. Session lifecycle management: task_start/task_continue/task_finish events
3. is_final flag: accurately determine last audio chunk per segment
4. Interruption handling: close WebSocket and create new connection

Reference: https://platform.minimax.io/docs/api-reference/speech-t2a-websocket
"""

import os
import time
import json
import queue
import asyncio
import traceback
import websockets

from core.utils.tts import MarkdownCleaner
from core.utils import opus_encoder_utils, textUtils
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import (
    SentenceType,
    ContentType,
    InterfaceType,
    TTSAudioDTO,
    MessageTag,
)
from config.logger import setup_logging
from core.utils.opus import pack_opus_with_header
from core.handle.reportHandle import enqueue_tts_report
from core.handle.sendAudioHandle import sendAudioMessage
from core.utils.output_counter import add_device_output

TAG = __name__
logger = setup_logging()

# MiniMax WebSocket API endpoint
MINIMAX_WS_URL = "wss://api.minimax.io/ws/v1/t2a_v2"


class TTSProvider(TTSProviderBase):
    """MiniMax Dual Stream TTS Implementation using WebSocket API"""

    # Fish Speech emotion tag to MiniMax emotion mapping
    EMOTION_MAP = {
        "happy": "happy",
        "sad": "sad",
        "curious": "fluent",
        "surprised": "surprised",
        "calm": "calm",
    }

    # Punctuation sets for text segmentation
    # First segment: use aggressive punctuation for faster first response
    FIRST_SEGMENT_PUNCTS = (",", "，", "。", "！", "？", "!", "?", "；", ";", "：", ":")
    # Normal segments: use sentence-ending punctuation
    NORMAL_PUNCTS = ("。", "！", "？", "!", "?", "；", ";")

    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        # Mark as dual stream interface
        self.interface_type = InterfaceType.DUAL_STREAM

        # MiniMax configuration
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("MiniMax API key is required")

        self.model = config.get("model", "speech-2.6-turbo")
        
        # Voice configuration
        if config.get("private_voice"):
            self.voice_id = config.get("private_voice")
        else:
            self.voice_id = config.get("voice_id", "female-shaonv")

        # Voice settings
        self.voice_setting = {
            "voice_id": self.voice_id,
            "speed": config.get("speed", 1),
            "vol": config.get("vol", 1),
            "pitch": config.get("pitch", 0),
            "emotion": config.get("emotion", "happy"),
        }

        # Audio settings (match HTTP API format)
        self.audio_setting = {
            "sample_rate": int(config.get("sample_rate", 16000)),
            "format": "pcm",  # Always use PCM for Opus encoding
            "channel": 1,
        }

        self.sample_rate = self.audio_setting["sample_rate"]
        self.audio_file_type = "pcm"

        # WebSocket connection state
        self.ws = None
        self._session_active = False
        self._task_started = False
        self._monitor_task = None
        
        # Connection keeper state (for low-latency preheat)
        self._connection_keeper_task = None
        self._preheat_ready = None  # asyncio.Event: set when connection is ready, clear to trigger preheat

        # Opus encoder (PCM -> Opus)
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=self.sample_rate, channels=1, frame_size_ms=60
        )

        # Session state
        self._session_text_buffer = []  # Accumulated text for reporting
        self._first_audio_sent = False
        self._session_end = False  # True when all text sent AND ready for final is_final
        self._abort_handled = False  # Prevent repeated abort handling
        self._first_segment_send_time = None  # For TTS API latency tracking

        # Text buffer for segment accumulation (similar to fish_single_stream)
        self._text_buffer = ""
        self._processed_idx = 0

        # Track task_continue/is_final count for accurate LAST detection
        self._sent_continue_count = 0  # Number of task_continue events sent
        self._received_final_count = 0  # Number of is_final responses received

        # Check API Key
        model_key_msg = check_model_key("TTS", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

    async def open_audio_channels(self, conn):
        """Override: establish WebSocket pre-connection and start connection keeper"""
        try:
            await super().open_audio_channels(conn)
            
            # Initialize event for connection keeper (clear = need preheat, set = ready)
            self._preheat_ready = asyncio.Event()
            
            # Start connection keeper task
            self._connection_keeper_task = asyncio.create_task(self._connection_keeper())
            
            # Wait for initial preheat to complete (with timeout)
            try:
                await asyncio.wait_for(self._preheat_ready.wait(), timeout=5)
                logger.bind(tag=TAG).info("Initial preheat completed")
            except asyncio.TimeoutError:
                logger.bind(tag=TAG).warning("Initial preheat timeout, will retry on first request")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to open audio channels: {e}")
            self.ws = None
            raise

    async def _connection_keeper(self):
        """
        Connection keeper coroutine - maintains WebSocket connection ready for low latency.
        
        Uses single Event: _preheat_ready
        - clear = need preheat (triggered by abort or initial state)
        - set = connection ready
        
        Lifecycle:
        1. Preheat connection (ensure_connection + send_task_start)
        2. Set _preheat_ready
        3. Poll until _preheat_ready is cleared (by abort) or connection invalid
        4. Go back to step 1
        """
        while not self.conn.stop_event.is_set():
            try:
                # Check if connection is still valid
                if self._task_started and self.ws and self._session_active:
                    self._preheat_ready.set()
                else:
                    # Preheat new connection
                    self._preheat_ready.clear()
                    logger.bind(tag=TAG).info("Connection keeper: preheating...")
                    await self._ensure_connection()
                    await self._send_task_start()
                    self._preheat_ready.set()
                    logger.bind(tag=TAG).info("Connection keeper: connection ready")
                
                # Wait until connection becomes invalid or abort triggers clear
                while (self._preheat_ready.is_set() and 
                       self._task_started and self.ws and self._session_active and
                       not self.conn.stop_event.is_set()):
                    await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                logger.bind(tag=TAG).info("Connection keeper: cancelled")
                break
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Connection keeper error: {e}")
                self._preheat_ready.set()  # Set anyway to unblock waiters
                await asyncio.sleep(0.5)  # Back off on error

    async def _send_task_start(self):
        """Send task_start event and wait for task_started response"""
        start_event = {
            "event": "task_start",
            "model": self.model,
            "voice_setting": self.voice_setting.copy(),
            "audio_setting": self.audio_setting,
        }
        
        await self.ws.send(json.dumps(start_event))
        logger.bind(tag=TAG).info(f"Sent task_start")
        
        response = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=2))
        if response.get("event") == "task_started":
            logger.bind(tag=TAG).info("MiniMax TTS task started")
            self._task_started = True
        else:
            raise Exception(f"Unexpected task_start response: {response}")

    async def _ensure_connection(self, max_retries: int = 2):
        """Ensure WebSocket connection is established with retry logic"""
        if self.ws and self._session_active:
            logger.bind(tag=TAG).info("Using existing WebSocket connection")
            return
        
        # Reset stale state before creating new connection
        if self.ws or self._session_active or self._task_started:
            logger.bind(tag=TAG).debug(
                f"Resetting stale state: ws={self.ws is not None}, "
                f"active={self._session_active}, started={self._task_started}"
            )
            self.ws = None
            self._session_active = False
            self._task_started = False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.bind(tag=TAG).debug(
                    f"Establishing MiniMax WebSocket connection (attempt {attempt + 1}/{max_retries + 1})..."
                )

                self.ws = await websockets.connect(
                    MINIMAX_WS_URL,
                    additional_headers=headers,
                    max_size=10 * 1024 * 1024,  # 10MB max message size
                    open_timeout=10,
                    close_timeout=5,
                )

                # Wait for connected_success event
                response = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=10))
                if response.get("event") == "connected_success":
                    logger.bind(tag=TAG).info("MiniMax WebSocket connected successfully")
                    self._session_active = True
                    return
                else:
                    raise Exception(f"Unexpected connection response: {response}")

            except Exception as e:
                last_error = e
                # Log detailed error info
                error_type = type(e).__name__
                logger.bind(tag=TAG).warning(
                    f"WebSocket connection attempt {attempt + 1} failed: {error_type}: {e}"
                )
                # For InvalidStatusCode, log the response body if available
                if hasattr(e, 'response') and e.response:
                    try:
                        body = e.response.body.decode() if hasattr(e.response, 'body') else str(e.response)
                        logger.bind(tag=TAG).warning(f"Response body: {body[:500]}")
                    except:
                        pass
                if self.ws:
                    try:
                        await self.ws.close()
                    except:
                        pass
                    self.ws = None
                if attempt < max_retries:
                    await asyncio.sleep(0.5)

        raise last_error

    def tts_text_priority_thread(self):
        """
        Override: dual stream TTS text processing thread

        Manages session lifecycle based on FIRST/LAST signals.
        Uses task_start/task_continue/task_finish events.
        """
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).debug(
                    f"Received TTS task | {message.sentence_type.name} | {message.content_type.name}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False
                    self._abort_handled = False  # Reset for new round

                if self.conn.client_abort and not self._abort_handled:
                    # ========== Interruption (only handle once) ==========
                    self._abort_handled = True
                    logger.bind(tag=TAG).info("Received interruption, closing WebSocket")
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self._abort_session(), self.conn.loop
                        )
                        future.result(timeout=5)
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to abort session: {e}")
                    continue

                if message.sentence_type == SentenceType.FIRST:
                    # ========== New dialogue round starts ==========
                    self.tts_audio_first_sentence = True
                    self._first_audio_sent = False
                    self._first_segment_send_time = None
                    self._session_text_buffer = []
                    self._session_end = False
                    self._text_buffer = ""
                    self._processed_idx = 0
                    self._sent_continue_count = 0
                    self._received_final_count = 0
                    self.conn._latency_tts_first_text_time = None
                    self._message_tag = message.message_tag

                    # Start new TTS session
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self._start_task(), self.conn.loop
                        )
                        future.result(timeout=10)
                        self.before_stop_play_files.clear()
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to start task: {e}")
                        continue

                elif ContentType.TEXT == message.content_type:
                    # ========== Text content ==========
                    if message.content_detail:
                        self._session_text_buffer.append(message.content_detail)
                        self._text_buffer += message.content_detail
                        logger.bind(tag=TAG).debug(
                            f"Text buffer updated: +'{message.content_detail}', total len={len(self._text_buffer)}"
                        )

                        # Record TTS first text input time
                        if self.conn._latency_tts_first_text_time is None:
                            self.conn._latency_tts_first_text_time = time.time() * 1000
                            logger.bind(tag=TAG).debug("📝 [Latency] TTS received first text")

                        # Extract and send segments by punctuation
                        while True:
                            segment = self._extract_segment()
                            if not segment:
                                logger.bind(tag=TAG).debug(
                                    f"No segment extracted, waiting for punctuation. Buffer: {self._text_buffer[self._processed_idx:][:30]}..."
                                )
                                break
                            try:
                                future = asyncio.run_coroutine_threadsafe(
                                    self._send_text(segment),
                                    loop=self.conn.loop,
                                )
                                future.result(timeout=10)
                            except Exception as e:
                                logger.bind(tag=TAG).error(f"Failed to send TTS text: {e}")
                                break

                elif ContentType.FILE == message.content_type:
                    # ========== File content ==========
                    logger.bind(tag=TAG).info(
                        f"Adding audio file to playback list: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        self._process_audio_file_stream(
                            message.content_file,
                            callback=lambda audio_data: self.handle_audio_file(
                                audio_data, message.content_detail
                            ),
                        )

                if message.sentence_type == SentenceType.LAST:
                    # ========== Dialogue round ends ==========
                    # Send remaining text buffer
                    remaining = self._text_buffer[self._processed_idx:]
                    if remaining.strip():
                        logger.bind(tag=TAG).debug(f"Sending remaining buffer: {remaining[:50]}...")
                        try:
                            future = asyncio.run_coroutine_threadsafe(
                                self._send_text(remaining),
                                loop=self.conn.loop,
                            )
                            future.result(timeout=10)
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"Failed to send remaining text: {e}")
                        self._processed_idx = len(self._text_buffer)

                    self._session_end = True
                    logger.bind(tag=TAG).debug("Session end flag set, waiting for final audio")

            except queue.Empty:
                # Check for abort during queue wait (only once per abort)
                if self.conn.client_abort and not self._abort_handled:
                    self._abort_handled = True
                    logger.bind(tag=TAG).info("Detected interruption during queue wait, aborting session")
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self._abort_session(), self.conn.loop
                        )
                        future.result(timeout=5)
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to abort session: {e}")
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"TTS text processing failed: {str(e)}, type: {type(e).__name__}, "
                    f"stack: {traceback.format_exc()}"
                )

    def _audio_play_priority_thread(self):
        """Audio playback thread with accumulated reporting"""
        enqueue_text = None
        enqueue_audio = []
        enqueue_report_time = None
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
                        report_time = tts_audio_message.report_time
                    elif isinstance(tts_audio_message, tuple):
                        sentence_type = tts_audio_message[0]
                        audio_datas = tts_audio_message[1]
                        text = tts_audio_message[2]
                        message_tag = MessageTag.NORMAL
                        report_time = None
                    else:
                        logger.bind(tag=TAG).warning(
                            f"Unknown tts_audio_message type: {type(tts_audio_message)}"
                        )
                        continue

                except queue.Empty:
                    if self.conn.stop_event.is_set():
                        break
                    continue

                if self.conn.client_abort:
                    logger.bind(tag=TAG).debug(
                        "Received interruption, report played content"
                    )
                    if enqueue_text and enqueue_audio:
                        enqueue_tts_report(
                            self.conn, enqueue_text, enqueue_audio, message_tag, enqueue_report_time
                        )
                        logger.bind(tag=TAG).info(
                            f"Interruption: reported played content: {enqueue_text[:50]}..."
                        )
                    enqueue_text, enqueue_audio, enqueue_report_time = None, [], None
                    last_send_future = None
                    continue

                # Report TTS data when next text starts or session ends
                if sentence_type is not SentenceType.MIDDLE:
                    if enqueue_text and enqueue_audio:
                        enqueue_tts_report(
                            self.conn, enqueue_text, enqueue_audio, message_tag, enqueue_report_time
                        )
                    enqueue_audio = []
                    enqueue_text = text
                    enqueue_report_time = report_time

                # Collect TTS audio data for reporting
                if isinstance(audio_datas, bytes) and enqueue_audio is not None:
                    audio_with_header = pack_opus_with_header(audio_datas, message_tag)
                    enqueue_audio.append(audio_with_header)

                # Wait for previous send to complete
                if last_send_future is not None:
                    try:
                        last_send_future.result(timeout=5.0)
                    except Exception as e:
                        logger.bind(tag=TAG).warning(f"Previous audio send failed: {e}")

                # Async send audio
                last_send_future = asyncio.run_coroutine_threadsafe(
                    sendAudioMessage(self.conn, sentence_type, audio_datas, text, message_tag),
                    self.conn.loop,
                )

                # Record output
                if self.conn.max_output_size > 0 and text:
                    add_device_output(self.conn.headers.get("device-id"), len(text))

            except Exception as e:
                logger.bind(tag=TAG).error(f"audio_play_priority_thread: {text} {e}")

        # Report remaining TTS data on connection close
        if enqueue_text and enqueue_audio:
            try:
                enqueue_tts_report(
                    self.conn, enqueue_text, enqueue_audio, message_tag, enqueue_report_time
                )
                logger.bind(tag=TAG).info(
                    f"Connection closing, reported remaining: {enqueue_text}"
                )
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Final report failed: {e}")

    async def _start_task(self):
        """Start or reuse TTS task (waits for connection keeper preheat)"""
        logger.bind(tag=TAG).debug(
            f"_start_task: task_started={self._task_started}, "
            f"ws={self.ws is not None}, session_active={self._session_active}"
        )

        # Reset state for new round
        self.opus_encoder.reset_state()
        self._session_text_buffer = []
        self._first_audio_sent = False
        self._first_segment_send_time = None
        self._session_end = False
        self._text_buffer = ""
        self._processed_idx = 0
        self._sent_continue_count = 0
        self._received_final_count = 0

        # Wait for connection keeper to preheat (if not already ready)
        if self._preheat_ready and not self._preheat_ready.is_set():
            logger.bind(tag=TAG).info("Waiting for connection keeper to preheat...")
            try:
                await asyncio.wait_for(self._preheat_ready.wait(), timeout=3)
            except asyncio.TimeoutError:
                logger.bind(tag=TAG).warning("Preheat wait timeout, will establish connection directly")

        # If task already started (preheated), just restart monitor
        if self._task_started and self.ws and self._session_active:
            logger.bind(tag=TAG).info("Using preheated connection, starting monitor")
            if self._monitor_task is None or self._monitor_task.done():
                self._monitor_task = asyncio.create_task(self._monitor_ws_response())
                await asyncio.sleep(0)
            return

        # Fallback: keeper failed or not running, establish connection directly
        logger.bind(tag=TAG).info("No preheated connection, establishing directly...")
        try:
            await self._ensure_connection()
            await self._send_task_start()
            
            # Start monitor task
            self._monitor_task = asyncio.create_task(self._monitor_ws_response())
            await asyncio.sleep(0)
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to start task: {e}")
            raise

    def _extract_segment(self) -> str | None:
        """
        Extract a complete segment from text buffer based on punctuation.
        Returns the segment if found, otherwise None.
        """
        unprocessed = self._text_buffer[self._processed_idx:]
        if not unprocessed:
            return None

        # Use different punctuation for first sentence (faster response)
        puncts = self.FIRST_SEGMENT_PUNCTS if self.tts_audio_first_sentence else self.NORMAL_PUNCTS

        # Find latest punctuation position
        latest_punct_pos = -1
        for punct in puncts:
            pos = unprocessed.rfind(punct)
            if pos > latest_punct_pos:
                latest_punct_pos = pos

        if latest_punct_pos == -1:
            return None

        # Extract segment including the punctuation
        segment = unprocessed[: latest_punct_pos + 1]
        self._processed_idx += len(segment)

        # After first segment, use normal punctuation
        if self.tts_audio_first_sentence:
            self.tts_audio_first_sentence = False

        return segment.strip() if segment.strip() else None

    async def _send_text(self, text: str):
        """Send text via task_continue event"""
        if not self.ws or not self._task_started:
            logger.bind(tag=TAG).warning("Cannot send text: task not started")
            return

        # Clean markdown and extract emotion tag
        text = MarkdownCleaner.clean_markdown(text)
        emotion, clean_text = textUtils.extract_emotion_tag(text)

        if emotion:
            minimax_emotion = self.EMOTION_MAP.get(emotion)
            if minimax_emotion:
                logger.bind(tag=TAG).debug(f"Emotion tag mapped: ({emotion}) -> {minimax_emotion}")
                # Update voice_setting emotion for next request
                self.voice_setting["emotion"] = minimax_emotion
            text = clean_text

        if not text.strip():
            return

        logger.bind(tag=TAG).info(f"Sending text to MiniMax: {text[:50]}...")

        continue_event = {
            "event": "task_continue",
            "text": text,
        }

        await self.ws.send(json.dumps(continue_event))
        self._sent_continue_count += 1
        
        # Record first segment send time for latency tracking
        if self._first_segment_send_time is None:
            self._first_segment_send_time = time.time() * 1000
        
        logger.bind(tag=TAG).info(f"task_continue sent, count: {self._sent_continue_count}")

    async def _monitor_ws_response(self):
        """Monitor WebSocket responses for audio data"""
        try:
            while not self.conn.stop_event.is_set() and self._session_active:
                try:
                    if not self.ws:
                        break

                    # Check for abort
                    if self.conn.client_abort:
                        logger.bind(tag=TAG).info("Monitor detected client_abort, exiting")
                        return

                    # Use short timeout to check abort periodically
                    try:
                        msg = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                    except asyncio.TimeoutError:
                        continue  # Check abort again

                    logger.bind(tag=TAG).debug(f"Monitor received: {msg[:200]}...")

                    response = json.loads(msg)
                    logger.bind(tag=TAG).debug(f"Monitor received: {str(response)[:200]}...")

                    event = response.get("event")

                    if event == "task_failed":
                        error_msg = response.get("base_resp", {}).get("status_msg", "Unknown error")
                        logger.bind(tag=TAG).error(f"TTS task failed: {error_msg}")
                        await self._cleanup_session()
                        break

                    elif event == "task_finished":
                        logger.bind(tag=TAG).info("TTS task finished")
                        await self._cleanup_session()
                        break

                    # Handle audio data (task_continued response)
                    elif "data" in response and "audio" in response["data"]:
                        audio_hex = response["data"]["audio"]
                        is_final = response.get("is_final", False)
                        logger.bind(tag=TAG).debug(
                            f"Received audio chunk, len={len(audio_hex) if audio_hex else 0}, is_final={is_final}"
                        )

                        if audio_hex and not self.conn.client_abort:
                            # Send FIRST before first audio
                            if not self._first_audio_sent:
                                self._first_audio_sent = True
                                self._message_report_time = int(time.time())
                                report_text = "".join(self._session_text_buffer) if self._session_text_buffer else None

                                # Log TTS API first chunk latency
                                if self._first_segment_send_time:
                                    first_chunk_time = time.time() * 1000
                                    api_latency = (first_chunk_time - self._first_segment_send_time) / 1000
                                    logger.bind(tag=TAG).info(f"[Latency] TTS API first chunk: {api_latency:.3f}s")

                                self.tts_audio_queue.put(
                                    TTSAudioDTO(
                                        sentence_type=SentenceType.FIRST,
                                        audio_data=None,
                                        text=report_text,
                                        message_tag=self._message_tag,
                                        report_time=self._message_report_time,
                                    )
                                )

                            # Decode hex audio and encode to Opus
                            pcm_data = bytes.fromhex(audio_hex)
                            self.opus_encoder.encode_pcm_to_opus_stream(
                                pcm_data, end_of_stream=False, callback=self._handle_opus
                            )

                        # Check if this is the final audio for current segment
                        if is_final:
                            self._received_final_count += 1
                            logger.bind(tag=TAG).debug(
                                f"Received is_final, count: {self._received_final_count}/{self._sent_continue_count}"
                            )

                            # Only send LAST when:
                            # 1. _session_end is True (all text from LLM received)
                            # 2. All task_continue responses received (counts match)
                            if self._session_end and self._received_final_count >= self._sent_continue_count:
                                logger.bind(tag=TAG).info(
                                    f"All audio received ({self._received_final_count}/{self._sent_continue_count}), sending LAST"
                                )
                                # Flush remaining opus buffer
                                self.opus_encoder.encode_pcm_to_opus_stream(
                                    b"", end_of_stream=True, callback=self._handle_opus
                                )

                                # Process before_stop_play_files (without sending LAST again)
                                for audio_datas, text in self.before_stop_play_files:
                                    self.tts_audio_queue.put(TTSAudioDTO(
                                        sentence_type=SentenceType.MIDDLE,
                                        audio_data=audio_datas,
                                        text=text,
                                        message_tag=self._message_tag,
                                    ))
                                self.before_stop_play_files.clear()

                                # Send LAST (only once)
                                self.tts_audio_queue.put(
                                    TTSAudioDTO(
                                        sentence_type=SentenceType.LAST,
                                        audio_data=None,
                                        text=None,
                                        message_tag=self._message_tag,
                                    )
                                )
                                
                                # Reset local state for next round (connection reuse)
                                # Keep _task_started = True to continue using the same task
                                self._session_end = False
                                self._sent_continue_count = 0
                                self._received_final_count = 0
                                # Don't reset _task_started - we'll continue the same task
                                logger.bind(tag=TAG).debug("Round completed, keeping task active for next round")

                except asyncio.TimeoutError:
                    logger.bind(tag=TAG).warning("WebSocket receive timeout")
                    self._reset_connection_state()
                    break
                except websockets.ConnectionClosed as e:
                    logger.bind(tag=TAG).warning(f"WebSocket connection closed: {e}")
                    self._reset_connection_state()
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Error in monitor task: {e}")
                    self._reset_connection_state()
                    break

        finally:
            self._monitor_task = None

    def _reset_connection_state(self):
        """Reset connection state when WebSocket is lost"""
        self._task_started = False
        self._session_active = False
        self.ws = None
        logger.bind(tag=TAG).info("Connection state reset, will reconnect on next task")

    def _handle_opus(self, opus_data: bytes):
        """Handle encoded Opus data, send as MIDDLE message"""
        if self.conn.client_abort:
            return

        self.tts_audio_queue.put(
            TTSAudioDTO(
                sentence_type=SentenceType.MIDDLE,
                audio_data=opus_data,
                text=None,
                message_tag=self._message_tag,
            )
        )

    async def _abort_session(self):
        """Abort current TTS session due to interruption"""
        logger.bind(tag=TAG).info("Aborting TTS session due to interruption...")

        # Send LAST to audio queue
        if self._first_audio_sent:
            self.opus_encoder.encode_pcm_to_opus_stream(
                b"", end_of_stream=True, callback=self._handle_opus
            )
            self.tts_audio_queue.put(
                TTSAudioDTO(
                    sentence_type=SentenceType.LAST,
                    audio_data=None,
                    text=None,
                    message_tag=self._message_tag,
                )
            )

        # Close WebSocket (will create new one for next utterance)
        await self._close_websocket()
        
        # Signal connection keeper to preheat next connection (clear = need preheat)
        if self._preheat_ready:
            self._preheat_ready.clear()

    async def _cleanup_session(self):
        """Clean up session state without closing WebSocket"""
        self._task_started = False
        self._session_active = False  # Mark session as inactive for keeper to restart
        self._first_audio_sent = False
        self._first_segment_send_time = None
        self._session_end = False
        self._text_buffer = ""
        self._processed_idx = 0
        self._sent_continue_count = 0
        self._received_final_count = 0
        self._session_text_buffer = []
        
        # Signal connection keeper to preheat next connection
        if self._preheat_ready:
            self._preheat_ready.clear()

    async def _close_websocket(self):
        """Close WebSocket connection and reset all session state"""
        # Cancel monitor task
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            finally:
                self._monitor_task = None

        # Close WebSocket
        if self.ws:
            try:
                # Try to send task_finish gracefully
                if self._task_started:
                    await self.ws.send(json.dumps({"event": "task_finish"}))
            except:
                pass
            try:
                await self.ws.close()
            except:
                pass
            finally:
                self.ws = None

        # Always reset session state to prevent keeper loop
        # (must be outside the if block to handle ws=None case)
        self._session_active = False
        self._task_started = False

    async def close(self):
        """Clean up WebSocket resources and connection keeper"""
        # Cancel connection keeper task
        if self._connection_keeper_task and not self._connection_keeper_task.done():
            self._connection_keeper_task.cancel()
            try:
                await self._connection_keeper_task
            except asyncio.CancelledError:
                pass
            finally:
                self._connection_keeper_task = None
        
        await self._close_websocket()
        await super().close()

    async def text_to_speak(self, text, output_file):
        """
        Non-streaming TTS interface (for compatibility)
        In dual stream mode, text is sent via _send_text
        """
        logger.bind(tag=TAG).debug(f"text_to_speak called: {text}")
        # In dual stream mode, this is handled by _send_text
        pass


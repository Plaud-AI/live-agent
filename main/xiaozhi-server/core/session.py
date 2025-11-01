"""
Session Module - Modern Agent Session Implementation

This module implements a clean, new-protocol-based agent session handler.
It is separate from the legacy ConnectionHandler to avoid complexity and technical debt.

Architecture:
    WebSocketServer.Pipeline -> Session -> AudioRecognition -> VAD/STT/LLM/TTS
"""

import asyncio
import logging
import uuid
from typing import Any, AsyncIterable

from config.models import Config
from core.audio.audio_frame import AudioFrame
from core.audio_recognition import AudioRecognition, EndOfTurnInfo
from core.stt.base import SpeechEvent
from core.llm.base import ChatChunk
from core.components import Components
from core.dialogue.context import ChatContext
from core.utils.aio import Chan
# from core.handle.textHandle import handleTextMessage


class Session:
    """
    Agent session handle
    
    This class manages a single client connection and coordinates:
    - Audio input/output
    - VAD and STT through AudioRecognition
    - LLM generation
    - TTS synthesis
    
    Each session is independent and uses the new streaming protocol.
    """
    
    def __init__(
        self,
        *,
        session_id: str | None = None,
        components: Components,
        config: Config,
        websocket=None,
    ):
        """
        Initialize a new session.
        
        Args:
            session_id: Optional session ID (auto-generated if not provided)
            components: Global AI components (VAD, STT, LLM, TTS)
            config: Session configuration
            websocket: WebSocket connection
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.components = components
        self.config = config
        self.websocket = websocket
        
        # Audio configuration
        audio_config = config.audio_params
        self.sample_rate = audio_config.sample_rate if audio_config.sample_rate else 16000
        self.num_channels = audio_config.channels if audio_config.channels else 1
        self.audio_format = audio_config.format if audio_config.format else "opus"  # opus, pcm, etc.
        
        # Audio queues
        self.audio_output_chan: Chan[AudioFrame] | None = None
        self.audio_recognition: AudioRecognition | None = None
        
        # Session state
        self.is_speaking = False # True when user is speaking
        self.is_processing = False  # True when LLM is generating
        self.last_transcript = ""
        
        # Background tasks
        self._tasks: set[asyncio.Task] = set()
        self._user_turn_completed_task: asyncio.Task | None = None  # Current user turn processing task (for serialization)
        self._closing = asyncio.Event()
        
        # Initialize chat context with system prompt
        self.chat_ctx = ChatContext.empty()
        
        # Add system prompt if available
        # TODO: Load system prompt from config or prompt manager
        system_prompt = "You are a helpful voice assistant. Keep responses concise and natural for spoken conversation."
        self.chat_ctx.add_message(role="system", content=system_prompt)
        
        logging.info(
            f"Session created: {self.session_id} "
            f"(audio: {self.audio_format}, {self.sample_rate}Hz, {self.num_channels}ch)"
        )
    
    async def _initialize(self):
        """
        Initialize session components.
        
        This method:
        1. Creates audio input channel
        2. Initializes AudioRecognition with STT stream
        3. Starts background tasks
        """
        logging.info(f"[{self.session_id}] Initializing session components...")
        
        # Get audio pipeline config
        min_endpointing_delay = 0.5
        max_endpointing_delay = 0.5
        
        # Create audio output channel
        self.audio_output_chan = Chan[AudioFrame]()
        
        # Create and start AudioRecognition
        self.audio_recognition = AudioRecognition(
            vad=self.components.vad,
            stt_node=self.stt_node,
            min_endpointing_delay=min_endpointing_delay,
            max_endpointing_delay=max_endpointing_delay,
            hooks=self,  # Session implements RecognitionHooks
            turn_detector=None,
        )
        
        self.audio_recognition.start()
        
        logging.info(
            f"[{self.session_id}] Components initialized "
            f"(min_delay={min_endpointing_delay}s, max_delay={max_endpointing_delay}s)"
        )
    
    async def run(self):
        """
        Run the session - main entry point.
        
        This method:
        1. Initializes all components
        2. Runs the message receive loop
        3. Routes messages to appropriate handlers
        4. Cleans up on connection close
        
        This should be called from WebSocketServer._handle_connection and will
        block until the connection is closed.
        """
        try:
            logging.info(f"[{self.session_id}] Starting session...")
            
            # Initialize components
            await self._initialize()
            
            logging.info(f"[{self.session_id}] Session running, waiting for messages...")
            
            # Main message loop
            async for message in self.websocket:
                await self._route_message(message)
        
        except Exception as e:
            logging.error(f"[{self.session_id}] Session error: {e}", exc_info=True)
            raise
        
        finally:
            logging.info(f"[{self.session_id}] Session ended, cleaning up...")
            await self.aclose()
    
    async def _route_message(self, message):
        """
        Route incoming WebSocket message to appropriate handler.
        
        Args:
            message: WebSocket message (bytes for audio, str for text/control)
        """
        try:
            # Handle binary audio data
            if isinstance(message, bytes):
                await self._handle_audio_message(message)
            
            # Handle text/JSON messages (legacy protocol)
            elif isinstance(message, str):
                # await handleTextMessage(self, message)
                pass
            
            else:
                logging.warning(
                    f"[{self.session_id}] Unknown message type: {type(message)}"
                )
        
        except Exception as e:
            logging.error(
                f"[{self.session_id}] Error routing message: {e}",
                exc_info=True
            )
    
    async def _handle_audio_message(self, audio_data: bytes):
        """
        Handle incoming audio data: convert bytes to AudioFrame and push to recognition.
        
        Args:
            audio_data: Raw audio bytes from WebSocket (Opus, PCM, etc.)
        """
        try:
            if not audio_data:
                return
            
            # Decode audio format if needed
            if self.audio_format == "opus":
                pcm_data = self._decode_opus(audio_data)
                if not pcm_data:
                    return
                audio_data = pcm_data
            elif self.audio_format == "pcm":
                pass  # Already PCM, use directly
            else:
                logging.warning(
                    f"[{self.session_id}] Unsupported audio format: {self.audio_format}"
                )
                return
            
            # Calculate samples per channel (PCM16 = 2 bytes per sample)
            bytes_per_sample = 2
            total_samples = len(audio_data) // bytes_per_sample
            samples_per_channel = total_samples // self.num_channels
            
            if samples_per_channel == 0:
                logging.warning(
                    f"[{self.session_id}] Audio data too small: {len(audio_data)} bytes"
                )
                return
            
            # Create AudioFrame and push to recognition
            frame = AudioFrame(
                audio_data=audio_data,
                sample_rate=self.sample_rate,
                num_channels=self.num_channels,
                samples_per_channel=samples_per_channel,
            )
            
            self.push_audio(frame)
        
        except Exception as e:
            logging.error(
                f"[{self.session_id}] Error handling audio: {e}",
                exc_info=True
            )
    
    def _decode_opus(self, opus_data: bytes) -> bytes | None:
        """
        Decode Opus audio data to PCM.
        
        Args:
            opus_data: Opus encoded audio bytes
            
        Returns:
            PCM audio bytes if successful, None otherwise
        """
        try:
            import opuslib_next
            
            # Create Opus decoder if not exists
            if not hasattr(self, '_opus_decoder'):
                self._opus_decoder = opuslib_next.Decoder(
                    fs=self.sample_rate,
                    channels=self.num_channels
                )
            
            # Decode Opus to PCM
            pcm_data = self._opus_decoder.decode(
                opus_data,
                frame_size=960  # 20ms at 48kHz, will be resampled
            )
            
            return pcm_data
        
        except ImportError:
            logging.error(
                f"[{self.session_id}] opuslib not installed, cannot decode Opus audio"
            )
            # Fall back: treat as raw PCM (may not work correctly)
            return opus_data
        
        except Exception as e:
            logging.error(
                f"[{self.session_id}] Error decoding Opus: {e}",
                exc_info=True
            )
            return None
    
    async def aclose(self):
        """Close the session and cleanup resources."""
        logging.info(f"[{self.session_id}] Closing session...")
        self._closing.set()
        
        # Wait for current user turn to complete (don't cancel it)
        if self._user_turn_completed_task and not self._user_turn_completed_task.done():
            logging.info(f"[{self.session_id}] Waiting for current user turn to complete...")
            try:
                await asyncio.wait_for(self._user_turn_completed_task, timeout=5.0)
            except asyncio.TimeoutError:
                logging.warning(f"[{self.session_id}] User turn task timeout, cancelling...")
                self._user_turn_completed_task.cancel()
                try:
                    await self._user_turn_completed_task
                except asyncio.CancelledError:
                    pass
            except Exception as e:
                logging.error(f"[{self.session_id}] Error waiting for user turn: {e}")
        
        # Close AudioRecognition
        if self.audio_recognition:
            try:
                await self.audio_recognition.aclose()
                self.audio_recognition = None
            except Exception as e:
                logging.error(f"[{self.session_id}] Error closing AudioRecognition: {e}")
        
        # Close audio output channel
        if self.audio_output_chan:
            try:
                self.audio_output_chan.close()
                self.audio_output_chan = None
            except Exception as e:
                logging.error(f"[{self.session_id}] Error closing audio channel: {e}")
        
        # Cancel background tasks
        if self._tasks:
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
        
        logging.info(f"[{self.session_id}] Session closed")
    
    def push_audio(self, frame: AudioFrame):
        """
        Push audio frame to the session for processing.
        
        Args:
            frame: Audio frame to process
        """
        self.audio_recognition.push_audio(frame)
    
    # ============================================================================
    # Pipeline Node Methods (Direct Implementation)
    # ============================================================================
    # These methods implement the full pipeline logic with automatic component injection
    
    async def stt_node(self, audio_input) -> AsyncIterable[SpeechEvent|None]:
        """
        STT node: audio frames -> speech events
        
        Wraps STT in StreamAdapter if not natively streaming.
        Creates a per-connection stream from the global STT component.
        
        Args:
            audio_input: AsyncIterable[AudioFrame] - audio input stream
            
        Yields:
            SpeechEvent: STT events (interim/final transcripts)
        """
        from core.stt.base import StreamAdapter
        
        stt = self.components.stt
        vad = self.components.vad
        
        # Wrap non-streaming STT with VAD-based StreamAdapter
        if not stt.capabilities.streaming:
            wrapped_stt = StreamAdapter(stt=stt, vad=vad)
        else:
            wrapped_stt = stt
        
        # Create per-connection stream
        async with wrapped_stt.stream() as stream:
            
            async def _forward_input() -> None:
                """Forward audio frames from input to STT stream"""
                try:
                    async for frame in audio_input:
                        if isinstance(frame, AudioFrame):
                            stream.push_frame(frame)
                except Exception as e:
                    logging.error(f"[{self.session_id}] Error forwarding audio to STT: {e}", exc_info=True)
            
            forward_task = asyncio.create_task(
                _forward_input(),
                name=f"Session.{self.session_id}.STT_forward"
            )
            
            try:
                # Yield speech events from STT stream
                async for event in stream:
                    yield event
            finally:
                # Cleanup: cancel forward task and wait
                forward_task.cancel()
                try:
                    await asyncio.wait_for(forward_task, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
    
    async def llm_node(self, chat_ctx, tools=None) -> AsyncIterable[ChatChunk|None]:
        """
        LLM node: chat context -> chat chunks
        
        Creates a per-request stream from the global LLM component.
        
        Args:
            chat_ctx: ChatContext - conversation context
            tools: Optional list of function call tools
            
        Yields:
            ChatChunk: LLM response chunks
        """
        llm = self.components.llm
        tools = tools or []
        
        # Create per-request chat stream
        async with llm.response_stream(
            chat_ctx=chat_ctx,
            tools=tools,
        ) as stream:
            async for chunk in stream:
                yield chunk
    
    async def tts_node(self, text_input) -> AsyncIterable[AudioFrame|None]:
        """
        TTS node: text chunks -> audio frames
        
        Wraps TTS in StreamAdapter if not natively streaming.
        Creates a per-synthesis stream from the global TTS component.
        
        Args:
            text_input: AsyncIterable[str] - text input stream
            
        Yields:
            AudioFrame: Synthesized audio frames
        """
        from core.tts.stream_adapter import StreamAdapter
        from core.tokenize import tokenize
        
        tts = self.components.tts
        
        # Wrap non-streaming TTS with sentence-based StreamAdapter
        if not tts.capabilities.streaming:
            wrapped_tts = StreamAdapter(
                tts=tts,
                sentence_tokenizer=tokenize.blingfire.SentenceTokenizer(retain_format=True),
            )
        else:
            wrapped_tts = tts
        
        # Create per-synthesis stream
        async with wrapped_tts.stream() as stream:
            
            async def _forward_input() -> None:
                """Forward text chunks to TTS stream"""
                try:
                    async for text in text_input:
                        if isinstance(text, str) and text:
                            stream.push_text(text)
                    # Signal end of input
                    stream.end_input()
                except Exception as e:
                    logging.error(f"[{self.session_id}] Error forwarding text to TTS: {e}", exc_info=True)
            
            forward_task = asyncio.create_task(
                _forward_input(),
                name=f"Session.{self.session_id}.TTS_forward"
            )
            
            try:
                # Yield audio frames from TTS stream
                async for synthesized_event in stream:
                    yield synthesized_event.frame
            finally:
                # Cleanup: cancel forward task and wait
                forward_task.cancel()
                try:
                    await asyncio.wait_for(forward_task, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
    
    # ============================================================================
    # RecognitionHooks Implementation
    # ============================================================================
    # These methods are called by AudioRecognition to report events
    
    def on_start_of_speech(self, ev) -> None:
        """Called when user starts speaking."""
        logging.debug(f"[{self.session_id}] User started speaking")
        self.is_speaking = True
        
        # TODO: Cancel ongoing TTS if any
        # TODO: Send event to client UI
    
    def on_end_of_speech(self, ev) -> None:
        """Called when user stops speaking."""
        logging.debug(
            f"[{self.session_id}] User stopped speaking "
            f"(speech_duration={ev.speech_duration:.2f}s)"
        )
        self.is_speaking = False
    
    def on_final_transcript(self, ev) -> None:
        """Called when final transcript is ready."""
        if not ev.alternatives:
            return
        
        transcript = ev.alternatives[0].text
        confidence = ev.alternatives[0].confidence
        
        logging.info(
            f"[{self.session_id}] Final transcript: '{transcript}' "
            f"(confidence={confidence:.2f})"
        )
        
        self.last_transcript = transcript
        
        # TODO: Send transcript to client UI
    
    def on_end_of_turn(self, info: EndOfTurnInfo) -> bool:
        """
        Called when user turn ends - this triggers LLM generation.
        
        Args:
            info: EndOfTurnInfo with transcript and metrics
            
        Returns:
            bool: True if turn was committed (LLM generation will start)
        """
        transcript = info.transcript
        confidence = info.confidence
        
        logging.info(
            f"[{self.session_id}] End of turn: transcript='{transcript}', "
            f"confidence={confidence:.2f}, "
            f"transcription_delay={info.transcription_delay:.2f}s, "
            f"eou_delay={info.end_of_utterance_delay:.2f}s"
        )
        
        # Validate transcript
        if not transcript or not transcript.strip():
            logging.warning(f"[{self.session_id}] Empty transcript, ignoring turn")
            return False
        
        # TODO: Check if user said exit command
        
        # Trigger LLM generation asynchronously with serialization
        # Save old task to ensure serial processing
        old_completed_task = self._user_turn_completed_task
        
        self._user_turn_completed_task = asyncio.create_task(
            self._handle_user_turn_completed(old_completed_task, transcript, confidence),
            name=f"Session.handle_turn_{self.session_id}"
        )
        
        return True  # Commit the turn
    
    async def _handle_user_turn_completed(
        self, 
        old_task: asyncio.Task | None, 
        transcript: str, 
        confidence: float
    ):
        """
        Serialized user turn handler that waits for previous turn to complete.
        
        This ensures that even if the user speaks multiple times in quick succession,
        the agent processes and responds to each turn in order.
        
        Based on livekit-agents' serialization mechanism:
        - New turns wait for old turns to complete
        - Prevents concurrent LLM+TTS executions
        - Maintains conversation coherence
        
        Args:
            old_task: Previous user turn task (if any)
            transcript: User's speech transcript
            confidence: Transcript confidence score
        """
        if old_task is not None:
            logging.info(
                f"[{self.session_id}] Waiting for previous user turn to complete..."
            )
            try:
                await old_task
                logging.info(
                    f"[{self.session_id}] Previous turn completed, processing new turn"
                )
            except Exception as e:
                logging.error(
                    f"[{self.session_id}] Previous turn failed: {e}",
                    exc_info=True
                )
        
        # Process current turn
        await self._handle_user_turn(transcript, confidence)
    
    async def _handle_user_turn(self, transcript: str, confidence: float):
        """
        Handle user turn by generating LLM response and synthesizing speech.
        
        This orchestrates the full pipeline:
        1. Build chat context
        2. Stream LLM response
        3. Stream TTS synthesis
        4. Send audio to client
        
        Args:
            transcript: User's speech transcript
            confidence: Transcript confidence score
        """
        if self._closing.is_set():
            return
        
        try:
            self.is_processing = True
            logging.info(f"[{self.session_id}] Processing user turn: '{transcript}'")
            
            # Build chat context (TODO: integrate history, memory, tools)
            chat_ctx = self._build_chat_context(transcript)
            
            # Create text channel for LLM -> TTS pipeline
            text_chan = Chan[str]()
            
            # Create LLM and TTS streams using instance methods
            llm_stream = self.llm_node(chat_ctx, tools=None)
            tts_stream = self.tts_node(text_chan)
            
            # Forward LLM chunks to TTS
            assistant_response = []
            
            async def _forward_llm():
                try:
                    async for chunk in llm_stream:
                        # Extract text content from chunk.delta
                        if chunk.delta and chunk.delta.content:
                            text_chan.send_nowait(chunk.delta.content)
                            assistant_response.append(chunk.delta.content)
                        
                        # TODO: Handle tool calls
                        # if chunk.delta and chunk.delta.tool_calls:
                        #     for tool_call in chunk.delta.tool_calls:
                        #         # Process tool call
                        #         pass
                    
                except Exception as e:
                    logging.error(f"[{self.session_id}] Error forwarding LLM: {e}")
                finally:
                    text_chan.close()
            
            # Forward TTS audio to client
            async def _forward_audio():
                try:
                    async for audio_frame in tts_stream:
                        await self._send_audio(audio_frame)
                    
                    logging.info(f"[{self.session_id}] TTS synthesis completed")
                    
                except Exception as e:
                    logging.error(f"[{self.session_id}] Error forwarding audio: {e}")
                    text_chan.close()
                    raise
            
            # Run both pipelines concurrently
            await asyncio.gather(_forward_llm(), _forward_audio())
            
            # Save assistant response to chat context
            if assistant_response:
                full_response = "".join(assistant_response)
                self.chat_ctx.add_message(role="assistant", content=full_response)
                logging.info(
                    f"[{self.session_id}] User turn processed successfully, "
                    f"response length: {len(full_response)}"
                )
            else:
                logging.warning(f"[{self.session_id}] No assistant response generated")
        
        except Exception as e:
            logging.error(f"[{self.session_id}] Error handling user turn: {e}", exc_info=True)
        
        finally:
            self.is_processing = False
    
    async def _send_audio(self, frame: AudioFrame):
        """
        Send audio frame to client via WebSocket.
        
        Args:
            frame: Audio frame to send
        """
        if not self.websocket or self._closing.is_set():
            return
        
        try:
            # TODO: Convert AudioFrame to appropriate format (opus, pcm, etc.)
            # For now, just send raw data
            audio_data = bytes(frame.data)
            await self.websocket.send(audio_data)
        
        except Exception as e:
            logging.error(f"[{self.session_id}] Error sending audio: {e}")
    
    def _build_chat_context(self, user_message: str):
        """
        Build chat context for LLM generation.
        
        Args:
            user_message: User's message to add to context
            
        Returns:
            ChatContext: Context with system prompt, history, and user message
        """
        # Add user message to chat context
        self.chat_ctx.add_message(role="user", content=user_message)
        
        # Return the chat context (already contains history)
        return self.chat_ctx


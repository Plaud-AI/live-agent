"""
Audio Recognition Module

Coordinates VAD and STT for audio recognition and turn detection.
Simplified version based on livekit-agents AudioRecognition.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterable
from dataclasses import dataclass
from typing import Protocol, Callable

from core.audio.audio_frame import AudioFrame
from core.vad.base import VAD, VADEvent, VADEventType
from core.stt.base import SpeechEvent, SpeechEventType
from core.utils.aio import Chan, cancel_and_wait


@dataclass
class EndOfTurnInfo:
    """Information about end of user turn"""
    transcript: str
    transcription_delay: float
    end_of_utterance_delay: float
    confidence: float
    last_speaking_time: float


class RecognitionHooks(Protocol):
    """
    Callback interface for AudioRecognition events.
    Simplified version with only essential hooks.
    """
    
    def on_start_of_speech(self, ev: VADEvent) -> None:
        """Called when user starts speaking"""
        ...
    
    def on_end_of_speech(self, ev: VADEvent) -> None:
        """Called when user stops speaking"""
        ...
    
    def on_final_transcript(self, ev: SpeechEvent) -> None:
        """Called when final transcript is ready"""
        ...
    
    def on_end_of_turn(self, info: EndOfTurnInfo) -> bool:
        """
        Called when user turn ends (trigger LLM).
        Returns True if turn was committed.
        """
        ...


class AudioRecognition:
    """
    Coordinates VAD and STT for audio recognition and turn detection.
    
    This is a per-connection instance that uses global VAD/STT components.
    Streams are created and managed within background tasks.
    
    Based on livekit-agents AudioRecognition, simplified for our use case.
    """
    
    def __init__(
        self,
        *,
        vad: VAD,
        stt_node: Callable[[AsyncIterable[AudioFrame]], AsyncIterable[SpeechEvent|None]],  # Pre-created STT stream
        min_endpointing_delay: float,
        max_endpointing_delay: float,
        hooks: RecognitionHooks,
        turn_detector=None,  # Reserved for future
    ):
        """
        Initialize AudioRecognition.
        
        Args:
            vad: Global VAD instance
            stt_stream: Pre-created STT stream (async iterable of SpeechEvent)
            min_endpointing_delay: Minimum delay before detecting end of turn (seconds)
            max_endpointing_delay: Maximum delay for end of turn detection (seconds)
            hooks: Callback interface for recognition events
            turn_detector: Optional turn detector for EOU prediction (reserved)
        """
        self._vad = vad
        self._stt_node = stt_node
        self._min_endpointing_delay = min_endpointing_delay
        self._max_endpointing_delay = max_endpointing_delay
        self._hooks = hooks
        self._turn_detector = turn_detector  # Reserved for future
        
        # Background tasks
        self._vad_atask: asyncio.Task | None = None
        self._stt_atask: asyncio.Task | None = None
        self._end_of_turn_task: asyncio.Task | None = None
        
        # Audio distribution channels
        self._vad_ch: Chan[AudioFrame] | None = None
        self._stt_ch: Chan[AudioFrame] | None = None
        
        # State tracking
        self._speaking = False
        self._last_speaking_time: float = 0.0
        self._last_final_transcript_time: float = 0.0
        self._audio_transcript = ""
        self._final_transcript_confidence: list[float] = []
        
        # Control
        self._started = False
        self._closing = asyncio.Event()
    
    def start(self) -> None:
        """Start audio recognition (create channels and tasks)"""
        if self._started:
            logging.warning("AudioRecognition already started")
            return
        
        logging.info("Starting AudioRecognition")
        
        # Create VAD channel and task
        self._vad_ch = Chan[AudioFrame]()
        self._vad_atask = asyncio.create_task(
            self._vad_task(self._vad, self._vad_ch),
            name="AudioRecognition._vad_task"
        )
        
        # Create STT task (uses pre-created stream)
        self._stt_ch = Chan[AudioFrame]()
        self._stt_atask = asyncio.create_task(
            self._stt_task(self._stt_node, self._stt_ch),
            name="AudioRecognition._stt_task"
        )
        
        self._started = True
        logging.info("AudioRecognition started successfully")
    
    def push_audio(self, frame: AudioFrame) -> None:
        """
        Push audio frame to VAD and STT.
        
        Args:
            frame: Audio frame to process
        """
        if not self._started:
            logging.warning("AudioRecognition not started, ignoring audio frame")
            return
        
        # Send to VAD
        if self._vad_ch is not None:
            self._vad_ch.send_nowait(frame)

        if self._stt_ch is not None:
            self._stt_ch.send_nowait(frame)


    
    async def aclose(self) -> None:
        """Cleanup resources"""
        logging.info("Closing AudioRecognition")
        self._closing.set()
        
        # Cancel VAD task
        if self._vad_atask:
            await cancel_and_wait(self._vad_atask)
            self._vad_atask = None
        
        # Cancel STT task
        if self._stt_atask:
            await cancel_and_wait(self._stt_atask)
            self._stt_atask = None
        
        # Cancel EOU task
        if self._end_of_turn_task:
            await cancel_and_wait(self._end_of_turn_task)
            self._end_of_turn_task = None
        
        logging.info("AudioRecognition closed successfully")
    
    async def _vad_task(
        self,
        vad: VAD,
        audio_input: AsyncIterable[AudioFrame],
    ) -> None:
        """
        Process VAD events.
        
        Creates a VAD stream, forwards audio frames, and processes VAD events.
        """
        try:
            # Create VAD stream (per-connection state)
            stream = vad.stream()
            
            async def _forward() -> None:
                """Forward audio frames from channel to VAD stream"""
                async for frame in audio_input:
                    stream.push_frame(frame)
            
            forward_task = asyncio.create_task(_forward(), name="VAD._forward")
            
            try:
                # Process VAD events
                async for event in stream:
                    await self._on_vad_event(event)
            finally:
                await cancel_and_wait(forward_task)
                await stream.aclose()
        
        except asyncio.CancelledError:
            logging.info("VAD task cancelled")
            raise
        except Exception as e:
            logging.error(f"VAD task error: {e}", exc_info=True)
            raise
    
    async def _stt_task(
        self,
        stt_node: Callable[[AsyncIterable[AudioFrame]], AsyncIterable[SpeechEvent|None]],
        audio_input: AsyncIterable[AudioFrame],
    ) -> None:
        """
        Process STT events.
        
        Consumes the pre-created STT stream and processes speech events.
        """
        stt = stt_node(audio_input)
        try:
            async for event in stt:
                await self._on_stt_event(event)
        except asyncio.CancelledError:
            logging.info("STT task cancelled")
            raise
        except Exception as e:
            logging.error(f"STT task error: {e}", exc_info=True)
            raise
    
    async def _on_vad_event(self, event: VADEvent) -> None:
        """
        Handle VAD events.
        
        Args:
            event: VAD event (START_OF_SPEECH, END_OF_SPEECH, etc.)
        """
        if event.type == VADEventType.START_OF_SPEECH:
            self._speaking = True
            self._last_speaking_time = time.time()
            
            # Notify hooks
            self._hooks.on_start_of_speech(event)
            
            # Cancel pending EOU detection
            if self._end_of_turn_task:
                self._end_of_turn_task.cancel()
                self._end_of_turn_task = None
            
            logging.debug("User started speaking")
        
        elif event.type == VADEventType.END_OF_SPEECH:
            self._speaking = False
            self._last_speaking_time = time.time() - event.silence_duration
            
            # Notify hooks
            self._hooks.on_end_of_speech(event)
            
            # Trigger EOU detection (VAD mode)
            self._run_eou_detection()
            
            logging.debug(
                f"User stopped speaking (speech_duration={event.speech_duration:.2f}s, "
                f"silence_duration={event.silence_duration:.2f}s)"
            )
    
    async def _on_stt_event(self, event: SpeechEvent) -> None:
        """
        Handle STT events.
        
        Args:
            event: Speech event (FINAL_TRANSCRIPT, INTERIM_TRANSCRIPT, etc.)
        """
        if event.type == SpeechEventType.FINAL_TRANSCRIPT:
            if not event.alternatives:
                return
            
            transcript = event.alternatives[0].text
            confidence = event.alternatives[0].confidence
            
            if not transcript:
                return
            
            logging.debug(f"Received final transcript: '{transcript}' (confidence={confidence:.2f})")
            
            # Update transcript
            self._last_final_transcript_time = time.time()
            self._audio_transcript += f" {transcript}"
            self._audio_transcript = self._audio_transcript.strip()
            self._final_transcript_confidence.append(confidence)
            
            # Notify hooks
            self._hooks.on_final_transcript(event)
            
            # If not speaking, trigger EOU detection
            if not self._speaking:
                self._run_eou_detection()
        
        elif event.type == SpeechEventType.INTERIM_TRANSCRIPT:
            # Log interim transcript for debugging
            if event.alternatives:
                interim_text = event.alternatives[0].text
                logging.debug(f"Interim transcript: '{interim_text}'")
    
    def _run_eou_detection(self) -> None:
        """
        Run end-of-utterance detection.
        
        This method is called when:
        1. VAD detects end of speech (END_OF_SPEECH event)
        2. STT produces final transcript while user is not speaking
        """
        if not self._audio_transcript:
            logging.debug("No transcript yet, skipping EOU detection")
            return
        
        async def _eou_task(last_speaking_time: float) -> None:
            """
            Asynchronous EOU detection task.
            
            Waits for endpointing delay, then triggers LLM generation.
            """
            # Determine endpointing delay
            endpointing_delay = self._min_endpointing_delay
            
            # TODO: Integrate turn_detector here in future
            # if self._turn_detector:
            #     chat_ctx = self._hooks.retrieve_chat_ctx().copy()
            #     chat_ctx.add_message(role="user", content=self._audio_transcript)
            #     probability = await self._turn_detector.predict_end_of_turn(chat_ctx)
            #     unlikely_threshold = await self._turn_detector.unlikely_threshold(language)
            #     
            #     if unlikely_threshold and probability < unlikely_threshold:
            #         endpointing_delay = self._max_endpointing_delay
            
            logging.debug(
                f"EOU detection: waiting {endpointing_delay:.2f}s "
                f"(transcript='{self._audio_transcript}')"
            )
            
            # Sleep until endpointing delay passes
            extra_sleep = last_speaking_time + endpointing_delay - time.time()
            if extra_sleep > 0:
                try:
                    await asyncio.wait_for(
                        self._closing.wait(),
                        timeout=extra_sleep
                    )
                    # If closing, exit early
                    return
                except asyncio.TimeoutError:
                    pass
            
            # Calculate metrics
            confidence_avg = (
                sum(self._final_transcript_confidence) / len(self._final_transcript_confidence)
                if self._final_transcript_confidence
                else 0.0
            )
            
            if last_speaking_time <= 0:
                transcription_delay = 0.0
                end_of_utterance_delay = 0.0
            else:
                transcription_delay = max(
                    self._last_final_transcript_time - last_speaking_time, 0
                )
                end_of_utterance_delay = time.time() - last_speaking_time
            
            logging.info(
                f"EOU detected: transcript='{self._audio_transcript}', "
                f"confidence={confidence_avg:.2f}, "
                f"transcription_delay={transcription_delay:.2f}s, "
                f"end_of_utterance_delay={end_of_utterance_delay:.2f}s"
            )
            
            # Create info object
            info = EndOfTurnInfo(
                transcript=self._audio_transcript,
                transcription_delay=transcription_delay,
                end_of_utterance_delay=end_of_utterance_delay,
                confidence=confidence_avg,
                last_speaking_time=last_speaking_time,
            )
            
            # Call hook to trigger LLM generation
            try:
                committed = self._hooks.on_end_of_turn(info)
                
                if committed:
                    logging.debug("User turn committed, clearing transcript")
                    # Clear transcript after successful commit
                    self._audio_transcript = ""
                    self._final_transcript_confidence = []
                else:
                    logging.debug("User turn not committed by hook")
            
            except Exception as e:
                logging.error(f"Error in on_end_of_turn hook: {e}", exc_info=True)
        
        # Cancel previous EOU task if any
        if self._end_of_turn_task:
            self._end_of_turn_task.cancel()
        
        # Start new EOU task (copy last_speaking_time to avoid race conditions)
        self._end_of_turn_task = asyncio.create_task(
            _eou_task(self._last_speaking_time),
            name="AudioRecognition._eou_task"
        )


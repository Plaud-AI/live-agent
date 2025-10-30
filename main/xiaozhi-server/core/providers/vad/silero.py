"""
Silero VAD Implementation using ONNX Runtime

Voice Activity Detection using Silero VAD model (ONNX version).
Based on livekit-plugins-silero implementation.
"""

from __future__ import annotations

import asyncio
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal

import numpy as np
import onnxruntime 

from config.logger import setup_logging
from core.audio.audio_frame import AudioFrame
from core.providers.vad.base import VAD, VADCapabilities, VADEvent, VADEventType, VADStream
from core.providers.vad import base
from core.providers.vad.onnx_model import OnnxModel, new_inference_session
from core.utils.exp_filter import ExpFilter

TAG = __name__
logger = setup_logging()

SLOW_INFERENCE_THRESHOLD = 0.2  # late by 200ms


@dataclass
class _VADOptions:
    min_speech_duration: float
    min_silence_duration: float
    prefix_padding_duration: float
    max_buffered_speech: float
    activation_threshold: float
    sample_rate: int


class VAD(base.VAD):
    """
    Silero Voice Activity Detection (VAD) class using ONNX Runtime.
    
    This class provides functionality to detect speech segments within audio data
    using the Silero VAD ONNX model.
    """
    
    @classmethod
    def load(
        cls,
        *,
        min_speech_duration: float = 0.05,
        min_silence_duration: float = 0.55,
        prefix_padding_duration: float = 0.5,
        max_buffered_speech: float = 60.0,
        activation_threshold: float = 0.5,
        sample_rate: Literal[8000, 16000] = 16000,
        force_cpu: bool = True,
    ) -> VAD:
        """
        Load and initialize the Silero VAD ONNX model.
        
        This method loads the ONNX model and prepares it for inference.
        
        Args:
            min_speech_duration: Minimum duration of speech to start a new speech chunk
            min_silence_duration: At the end of each speech, wait this duration before ending
            prefix_padding_duration: Duration of padding to add to the beginning of each speech chunk
            max_buffered_speech: Maximum duration of speech to keep in the buffer (in seconds)
            activation_threshold: Threshold to consider a frame as speech
            sample_rate: Sample rate for inference (only 8KHz and 16KHz are supported)
            force_cpu: Force the use of CPU for inference
        
        Returns:
            VAD: An instance of the VAD class ready for streaming
        
        Raises:
            ValueError: If an unsupported sample rate is provided
        """
        if sample_rate not in [8000, 16000]:
            raise ValueError("Silero VAD only supports 8KHz and 16KHz sample rates")
        
        logger.bind(tag=TAG).info("Loading Silero VAD ONNX model")
        
        session = new_inference_session(force_cpu=force_cpu)
        opts = _VADOptions(
            min_speech_duration=min_speech_duration,
            min_silence_duration=min_silence_duration,
            prefix_padding_duration=prefix_padding_duration,
            max_buffered_speech=max_buffered_speech,
            activation_threshold=activation_threshold,
            sample_rate=sample_rate,
        )
        return cls(session=session, opts=opts)
    
    def __init__(
        self,
        *,
        session: onnxruntime.InferenceSession,
        opts: _VADOptions,
    ) -> None:
        super().__init__(capabilities=VADCapabilities(update_interval=0.032))
        self._onnx_session = session
        self._opts = opts
        self._streams = weakref.WeakSet[VADStream]()
    
    @property
    def model(self) -> str:
        """Get the model name"""
        return "silero"
    
    @property
    def provider(self) -> str:
        """Get the provider name"""
        return "ONNX"
    
    def stream(self) -> VADStream:
        """
        Create a new VADStream for processing audio data.
        
        Returns:
            VADStream: A stream object for processing audio input and detecting speech.
        """
        stream = VADStream(
            vad=self,
            opts=self._opts,
            model=OnnxModel(
                onnx_session=self._onnx_session, sample_rate=self._opts.sample_rate
            ),
        )
        self._streams.add(stream)
        return stream
    
    def update_options(
        self,
        *,
        min_speech_duration: float | None = None,
        min_silence_duration: float | None = None,
        prefix_padding_duration: float | None = None,
        max_buffered_speech: float | None = None,
        activation_threshold: float | None = None,
    ) -> None:
        """
        Update the VAD options.
        
        This method allows you to update the VAD options after the VAD object has been created.
        
        Args:
            min_speech_duration: Minimum duration of speech to start a new speech chunk
            min_silence_duration: At the end of each speech, wait this duration before ending
            prefix_padding_duration: Duration of padding to add to the beginning of each speech chunk
            max_buffered_speech: Maximum duration of speech to keep in the buffer (in seconds)
            activation_threshold: Threshold to consider a frame as speech
        """
        if min_speech_duration is not None:
            self._opts.min_speech_duration = min_speech_duration
        if min_silence_duration is not None:
            self._opts.min_silence_duration = min_silence_duration
        if prefix_padding_duration is not None:
            self._opts.prefix_padding_duration = prefix_padding_duration
        if max_buffered_speech is not None:
            self._opts.max_buffered_speech = max_buffered_speech
        if activation_threshold is not None:
            self._opts.activation_threshold = activation_threshold
        
        for stream in self._streams:
            stream.update_options(
                min_speech_duration=min_speech_duration,
                min_silence_duration=min_silence_duration,
                prefix_padding_duration=prefix_padding_duration,
                max_buffered_speech=max_buffered_speech,
                activation_threshold=activation_threshold,
            )


class VADStream(base.VADStream):
    """Silero VAD streaming implementation using ONNX"""
    
    def __init__(self, vad: VAD, opts: _VADOptions, model: OnnxModel) -> None:
        super().__init__(vad)
        self._opts = opts
        self._model = model
        self._loop = asyncio.get_event_loop()
        
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._task.add_done_callback(lambda _: self._executor.shutdown(wait=False))
        self._exp_filter = ExpFilter(alpha=0.35)
        
        self._input_sample_rate = 0
        self._speech_buffer: np.ndarray | None = None
        self._speech_buffer_max_reached = False
        self._prefix_padding_samples = 0
    
    def update_options(
        self,
        *,
        min_speech_duration: float | None = None,
        min_silence_duration: float | None = None,
        prefix_padding_duration: float | None = None,
        max_buffered_speech: float | None = None,
        activation_threshold: float | None = None,
    ) -> None:
        """
        Update the VAD options.
        
        Args:
            min_speech_duration: Minimum duration of speech to start a new speech chunk
            min_silence_duration: At the end of each speech, wait this duration before ending
            prefix_padding_duration: Duration of padding to add to the beginning of each speech chunk
            max_buffered_speech: Maximum duration of speech to keep in the buffer (in seconds)
            activation_threshold: Threshold to consider a frame as speech
        """
        old_max_buffered_speech = self._opts.max_buffered_speech
        
        if min_speech_duration is not None:
            self._opts.min_speech_duration = min_speech_duration
        if min_silence_duration is not None:
            self._opts.min_silence_duration = min_silence_duration
        if prefix_padding_duration is not None:
            self._opts.prefix_padding_duration = prefix_padding_duration
        if max_buffered_speech is not None:
            self._opts.max_buffered_speech = max_buffered_speech
        if activation_threshold is not None:
            self._opts.activation_threshold = activation_threshold
        
        if self._input_sample_rate:
            assert self._speech_buffer is not None
            
            self._prefix_padding_samples = int(
                self._opts.prefix_padding_duration * self._input_sample_rate
            )
            
            self._speech_buffer.resize(
                int(self._opts.max_buffered_speech * self._input_sample_rate)
                + self._prefix_padding_samples
            )
            
            if self._opts.max_buffered_speech > old_max_buffered_speech:
                self._speech_buffer_max_reached = False
    
    async def _main_task(self) -> None:
        """Main VAD processing task"""
        inference_f32_data = np.empty(self._model.window_size_samples, dtype=np.float32)
        speech_buffer_index: int = 0
        
        # "pub_" means public, these values are exposed to the users through events
        pub_speaking = False
        pub_speech_duration = 0.0
        pub_silence_duration = 0.0
        pub_current_sample = 0
        pub_timestamp = 0.0
        
        speech_threshold_duration = 0.0
        silence_threshold_duration = 0.0
        
        input_frames: list[AudioFrame] = []
        inference_frames: list[AudioFrame] = []
        
        # TODO: Support resampling if input_sample_rate != model sample_rate
        # resampler: AudioResampler | None = None
        
        # used to avoid drift when the sample_rate ratio is not an integer
        input_copy_remaining_fract = 0.0
        
        extra_inference_time = 0.0
        
        async for input_frame in self._input_ch:
            if not isinstance(input_frame, AudioFrame):
                continue  # ignore flush sentinel for now
            
            if not self._input_sample_rate:
                self._input_sample_rate = input_frame.sample_rate
                
                # alloc the buffers now that we know the input sample rate
                self._prefix_padding_samples = int(
                    self._opts.prefix_padding_duration * self._input_sample_rate
                )
                
                self._speech_buffer = np.empty(
                    int(self._opts.max_buffered_speech * self._input_sample_rate)
                    + self._prefix_padding_samples,
                    dtype=np.int16,
                )
                
                # TODO: Support resampling if input_sample_rate != model sample_rate
                if self._input_sample_rate != self._opts.sample_rate:
                    logger.bind(tag=TAG).warning(
                        f"Input sample rate {self._input_sample_rate} != model sample rate "
                        f"{self._opts.sample_rate}. Resampling not yet supported."
                    )
            
            elif self._input_sample_rate != input_frame.sample_rate:
                logger.bind(tag=TAG).error(
                    f"A frame with another sample rate was already pushed: "
                    f"{input_frame.sample_rate} != {self._input_sample_rate}"
                )
                continue
            
            assert self._speech_buffer is not None
            
            input_frames.append(input_frame)
            # TODO: Add resampler support when implemented
            # if resampler is not None:
            #     inference_frames.extend(resampler.push(input_frame))
            # else:
            inference_frames.append(input_frame)
            
            while True:
                start_time = time.perf_counter()
                
                available_inference_samples = sum(
                    [frame.samples_per_channel for frame in inference_frames]
                )
                if available_inference_samples < self._model.window_size_samples:
                    break  # not enough samples to run inference
                
                # Combine frames for processing
                input_frame_combined = AudioFrame.combine_frames(input_frames)
                inference_frame_combined = AudioFrame.combine_frames(inference_frames)
                
                # Convert to float32 for model input
                audio_data = inference_frame_combined.data[: self._model.window_size_samples]
                audio_bytes = bytes(audio_data)
                np.divide(
                    np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32),
                    np.iinfo(np.int16).max,
                    out=inference_f32_data,
                )
                
                # Run the inference in executor (ONNX model handles RNN state internally)
                p = await self._loop.run_in_executor(
                    self._executor, self._model, inference_f32_data
                )
                p = self._exp_filter.apply(exp=1.0, sample=p)
                
                window_duration = self._model.window_size_samples / self._opts.sample_rate
                
                pub_current_sample += self._model.window_size_samples
                pub_timestamp += window_duration
                
                resampling_ratio = self._input_sample_rate / self._model.sample_rate
                to_copy = (
                    self._model.window_size_samples * resampling_ratio + input_copy_remaining_fract
                )
                to_copy_int = int(to_copy)
                input_copy_remaining_fract = to_copy - to_copy_int
                
                # Copy the inference window to the speech buffer
                available_space = len(self._speech_buffer) - speech_buffer_index
                to_copy_buffer = min(to_copy_int, available_space)
                if to_copy_buffer > 0:
                    input_data_bytes = bytes(input_frame_combined.data[:to_copy_buffer])
                    self._speech_buffer[
                        speech_buffer_index : speech_buffer_index + to_copy_buffer
                    ] = np.frombuffer(input_data_bytes, dtype=np.int16)
                    speech_buffer_index += to_copy_buffer
                elif not self._speech_buffer_max_reached:
                    # reached self._opts.max_buffered_speech (padding is included)
                    self._speech_buffer_max_reached = True
                    logger.bind(tag=TAG).warning(
                        "max_buffered_speech reached, ignoring further data for the current speech input"
                    )
                
                inference_duration = time.perf_counter() - start_time
                extra_inference_time = max(
                    0.0,
                    extra_inference_time + inference_duration - window_duration,
                )
                if inference_duration > SLOW_INFERENCE_THRESHOLD:
                    logger.bind(tag=TAG).warning(
                        "inference is slower than realtime",
                        extra={"delay": extra_inference_time},
                    )
                
                def _reset_write_cursor() -> None:
                    nonlocal speech_buffer_index
                    assert self._speech_buffer is not None
                    
                    if speech_buffer_index <= self._prefix_padding_samples:
                        return
                    
                    padding_data = self._speech_buffer[
                        speech_buffer_index - self._prefix_padding_samples : speech_buffer_index
                    ]
                    
                    self._speech_buffer_max_reached = False
                    self._speech_buffer[: self._prefix_padding_samples] = padding_data
                    speech_buffer_index = self._prefix_padding_samples
                
                def _copy_speech_buffer() -> AudioFrame:
                    """Copy the data from speech_buffer"""
                    assert self._speech_buffer is not None
                    speech_data = self._speech_buffer[:speech_buffer_index].tobytes()
                    
                    return AudioFrame(
                        data=speech_data,
                        sample_rate=self._input_sample_rate,
                        num_channels=1,
                        samples_per_channel=speech_buffer_index,
                    )
                
                if pub_speaking:
                    pub_speech_duration += window_duration
                else:
                    pub_silence_duration += window_duration
                
                # Emit INFERENCE_DONE event
                input_frame_copy = AudioFrame(
                    data=bytes(input_frame_combined.data[:to_copy_int]),
                    sample_rate=self._input_sample_rate,
                    num_channels=1,
                    samples_per_channel=to_copy_int,
                )
                
                self._event_ch.send_nowait(
                    VADEvent(
                        type=VADEventType.INFERENCE_DONE,
                        samples_index=pub_current_sample,
                        timestamp=pub_timestamp,
                        silence_duration=pub_silence_duration,
                        speech_duration=pub_speech_duration,
                        probability=p,
                        inference_duration=inference_duration,
                        frames=[input_frame_copy],
                        speaking=pub_speaking,
                        raw_accumulated_silence=silence_threshold_duration,
                        raw_accumulated_speech=speech_threshold_duration,
                    )
                )
                
                if p >= self._opts.activation_threshold:
                    speech_threshold_duration += window_duration
                    silence_threshold_duration = 0.0
                    
                    if not pub_speaking:
                        if speech_threshold_duration >= self._opts.min_speech_duration:
                            pub_speaking = True
                            pub_silence_duration = 0.0
                            pub_speech_duration = speech_threshold_duration
                            
                            self._event_ch.send_nowait(
                                VADEvent(
                                    type=VADEventType.START_OF_SPEECH,
                                    samples_index=pub_current_sample,
                                    timestamp=pub_timestamp,
                                    silence_duration=pub_silence_duration,
                                    speech_duration=pub_speech_duration,
                                    frames=[_copy_speech_buffer()],
                                    speaking=True,
                                )
                            )
                
                else:
                    silence_threshold_duration += window_duration
                    speech_threshold_duration = 0.0
                    
                    if not pub_speaking:
                        _reset_write_cursor()
                    
                    if (
                        pub_speaking
                        and silence_threshold_duration >= self._opts.min_silence_duration
                    ):
                        pub_speaking = False
                        pub_speech_duration = 0.0
                        pub_silence_duration = silence_threshold_duration
                        
                        self._event_ch.send_nowait(
                            VADEvent(
                                type=VADEventType.END_OF_SPEECH,
                                samples_index=pub_current_sample,
                                timestamp=pub_timestamp,
                                silence_duration=pub_silence_duration,
                                speech_duration=pub_speech_duration,
                                frames=[_copy_speech_buffer()],
                                speaking=False,
                            )
                        )
                        
                        _reset_write_cursor()
                
                # Remove processed samples from frames
                # Keep remaining data for next iteration
                input_frames = []
                inference_frames = []
                
                # Add remaining data if any
                if len(inference_frame_combined.data) - self._model.window_size_samples > 0:
                    remaining_data = inference_frame_combined.data[self._model.window_size_samples :]
                    remaining_bytes = bytes(remaining_data)
                    inference_frames.append(
                        AudioFrame(
                            data=remaining_bytes,
                            sample_rate=self._opts.sample_rate,
                            num_channels=1,
                            samples_per_channel=len(remaining_bytes) // 2,
                        )
                    )
                
                if len(input_frame_combined.data) - to_copy_int > 0:
                    remaining_data = input_frame_combined.data[to_copy_int:]
                    remaining_bytes = bytes(remaining_data)
                    input_frames.append(
                        AudioFrame(
                            data=remaining_bytes,
                            sample_rate=self._input_sample_rate,
                            num_channels=1,
                            samples_per_channel=len(remaining_bytes) // 2,
                        )
                    )

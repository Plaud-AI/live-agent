import os
import io
import wave
import uuid
import json
import time
import queue
import asyncio
import traceback
import threading
import opuslib_next
import concurrent.futures
from abc import ABC, abstractmethod
from config.logger import setup_logging
from typing import Optional, Tuple, List
from core.handle.receiveAudioHandle import startToChat
from core.handle.reportHandle import enqueue_asr_report
from core.utils.util import remove_punctuation_and_length
from core.handle.receiveAudioHandle import handleAudioMessage

TAG = __name__
logger = setup_logging()


class ASRProviderBase(ABC):
    def __init__(self):
        pass

    # 打开音频通道
    async def open_audio_channels(self, conn):
        conn.asr_priority_thread = threading.Thread(
            target=self.asr_text_priority_thread, args=(conn,), daemon=True
        )
        conn.asr_priority_thread.start()

    # 有序处理ASR音频
    def asr_text_priority_thread(self, conn):
        while not conn.stop_event.is_set():
            try:
                message = conn.asr_audio_queue.get(timeout=1)
                future = asyncio.run_coroutine_threadsafe(
                    handleAudioMessage(conn, message),
                    conn.loop,
                )
                future.result()
            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"处理ASR文本失败: {str(e)}, 类型: {type(e).__name__}, 堆栈: {traceback.format_exc()}"
                )
                continue

    # 接收音频
    async def receive_audio(self, conn, audio, audio_have_voice):
        if conn.client_listen_mode == "auto" or conn.client_listen_mode == "realtime":
            have_voice = audio_have_voice
        else:
            have_voice = conn.client_have_voice
        
        conn.asr_audio.append(audio)
        if not have_voice and not conn.client_have_voice:
            conn.asr_audio = conn.asr_audio[-10:]
            return

        if conn.client_voice_stop:
            asr_audio_task = conn.asr_audio.copy()
            conn.asr_audio.clear()
            conn.reset_vad_states()

            if len(asr_audio_task) > 15 or conn.client_listen_mode == "manual":
                await self.handle_voice_stop(conn, asr_audio_task)

    # 处理语音停止
    async def handle_voice_stop(self, conn, asr_audio_task: List[bytes]):
        """并行处理ASR和声纹识别"""
        try:
            total_start_time = time.monotonic()
            
            # 准备音频数据
            if conn.audio_format == "pcm":
                pcm_data = asr_audio_task
            else:
                pcm_data = self.decode_opus(asr_audio_task)
            
            combined_pcm_data = b"".join(pcm_data)
            
            # 预先准备WAV数据
            wav_data = None
            if conn.voiceprint_provider and combined_pcm_data:
                wav_data = self._pcm_to_wav(combined_pcm_data)
            
            # 定义ASR任务
            def run_asr():
                start_time = time.monotonic()
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            self.speech_to_text(asr_audio_task, conn.session_id, conn.audio_format)
                        )
                        end_time = time.monotonic()
                        logger.bind(tag=TAG).info(f"ASR耗时: {end_time - start_time:.3f}s")
                        return result
                    finally:
                        loop.close()
                except Exception as e:
                    end_time = time.monotonic()
                    logger.bind(tag=TAG).error(f"ASR失败: {e}")
                    return ("", None)
            
            # 定义声纹识别任务
            def run_voiceprint():
                if not wav_data:
                    return None
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        # 使用连接的声纹识别提供者
                        result = loop.run_until_complete(
                            conn.voiceprint_provider.identify_speaker(wav_data, conn.session_id)
                        )
                        return result
                    finally:
                        loop.close()
                except Exception as e:
                    logger.bind(tag=TAG).error(f"声纹识别失败: {e}")
                    return None
            
            # 使用线程池执行器并行运行
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as thread_executor:
                asr_future = thread_executor.submit(run_asr)
                
                if conn.voiceprint_provider and wav_data:
                    voiceprint_future = thread_executor.submit(run_voiceprint)
                    
                    # 等待两个线程都完成
                    asr_result = asr_future.result(timeout=15)
                    voiceprint_result = voiceprint_future.result(timeout=15)
                    
                    results = {"asr": asr_result, "voiceprint": voiceprint_result}
                else:
                    asr_result = asr_future.result(timeout=15)
                    results = {"asr": asr_result, "voiceprint": None}
            
            
            # 处理结果
            raw_text, _ = results.get("asr", ("", None))
            speaker_name = results.get("voiceprint", None)
            
            # 记录识别结果
            if raw_text:
                logger.bind(tag=TAG).info(f"识别文本: {raw_text}")
            if speaker_name:
                logger.bind(tag=TAG).info(f"识别说话人: {speaker_name}")
            
            # 性能监控
            total_time = time.monotonic() - total_start_time
            logger.bind(tag=TAG).info(f"总处理耗时: {total_time:.3f}s")
            
            # 检查文本长度
            text_len, _ = remove_punctuation_and_length(raw_text)
            self.stop_ws_connection()
            
            if text_len > 0:
                # 构建包含说话人信息的JSON字符串
                enhanced_text = self._build_enhanced_text(raw_text, speaker_name)
                
                # 使用自定义模块进行上报
                await startToChat(conn, enhanced_text)
                enqueue_asr_report(conn, enhanced_text, asr_audio_task)
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"处理语音停止失败: {e}")
            import traceback
            logger.bind(tag=TAG).debug(f"异常详情: {traceback.format_exc()}")

    def _build_enhanced_text(self, text: str, speaker_name: Optional[str]) -> str:
        """构建包含说话人信息的文本"""
        if speaker_name and speaker_name.strip():
            return json.dumps({
                "speaker": speaker_name,
                "content": text
            }, ensure_ascii=False)
        else:
            return text

    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """将PCM数据转换为WAV格式"""
        if len(pcm_data) == 0:
            logger.bind(tag=TAG).warning("PCM数据为空，无法转换WAV")
            return b""
        
        # 确保数据长度是偶数（16位音频）
        if len(pcm_data) % 2 != 0:
            pcm_data = pcm_data[:-1]
        
        # 创建WAV文件头
        wav_buffer = io.BytesIO()
        try:
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)      # 单声道
                wav_file.setsampwidth(2)      # 16位
                wav_file.setframerate(16000)  # 16kHz采样率
                wav_file.writeframes(pcm_data)
            
            wav_buffer.seek(0)
            wav_data = wav_buffer.read()
            
            return wav_data
        except Exception as e:
            logger.bind(tag=TAG).error(f"WAV转换失败: {e}")
            return b""

    def stop_ws_connection(self):
        pass

    def save_audio_to_file(self, pcm_data: List[bytes], session_id: str) -> str:
        """PCM数据保存为WAV文件"""
        module_name = __name__.split(".")[-1]
        file_name = f"asr_{module_name}_{session_id}_{uuid.uuid4()}.wav"
        file_path = os.path.join(self.output_dir, file_name)

        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes = 16-bit
            wf.setframerate(16000)
            wf.writeframes(b"".join(pcm_data))

        return file_path

    @abstractmethod
    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, audio_format="opus"
    ) -> Tuple[Optional[str], Optional[str]]:
        """将语音数据转换为文本"""
        pass

    @staticmethod
    def decode_opus(opus_data: List[bytes]) -> List[bytes]:
        """将Opus音频数据解码为PCM数据"""
        try:
            decoder = opuslib_next.Decoder(16000, 1)
            pcm_data = []
            buffer_size = 960  # 每次处理960个采样点 (60ms at 16kHz)
            
            for i, opus_packet in enumerate(opus_data):
                try:
                    if not opus_packet or len(opus_packet) == 0:
                        continue
                    
                    pcm_frame = decoder.decode(opus_packet, buffer_size)
                    if pcm_frame and len(pcm_frame) > 0:
                        pcm_data.append(pcm_frame)
                        
                except opuslib_next.OpusError as e:
                    logger.bind(tag=TAG).warning(f"Opus解码错误，跳过数据包 {i}: {e}")
                except Exception as e:
                    logger.bind(tag=TAG).error(f"音频处理错误，数据包 {i}: {e}")
            
            return pcm_data
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"音频解码过程发生错误: {e}")
            return []


# ============================================================================
# Streaming ASR Base Classes
# ============================================================================
# 
# The following classes provide a modern streaming ASR interface similar to
# LiveKit Agents design. These classes are completely independent from the
# legacy ASRProviderBase above.
# ============================================================================

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum, unique
from types import TracebackType
from typing import Literal, Union, Any, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from core.audio.audio_frame import AudioFrame
from core.utils.aio import Chan, cancel_and_wait
from core.utils.types import (
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    NotGivenOr,
    is_given,
)
from core.utils.errors import APIConnectionError, APIError
from core.utils.short_uuid import shortuuid

# Type alias for audio buffer
AudioBuffer = Union[list[AudioFrame], AudioFrame]

# Type alias for VAD (to avoid circular imports)
# Providers should import VAD from their respective modules
if TYPE_CHECKING:
    VAD = Any
else:
    VAD = None


@unique
class SpeechEventType(str, Enum):
    START_OF_SPEECH = "start_of_speech"
    """indicate the start of speech
    if the ASR doesn't support this event, this will be emitted as the same time as the first INTERIM_TRANSCRIPT"""
    INTERIM_TRANSCRIPT = "interim_transcript"
    """interim transcript, useful for real-time transcription"""
    PREFLIGHT_TRANSCRIPT = "preflight_transcript"
    """preflight transcript, emitted when the ASR is confident enough that a certain
    portion of speech will not change. This is different from final transcript in that
    the same transcript may still be updated; but it is stable enough to be used for
    preemptive generation"""
    FINAL_TRANSCRIPT = "final_transcript"
    """final transcript, emitted when the ASR is confident enough that a certain
    portion of speech will not change"""
    RECOGNITION_USAGE = "recognition_usage"
    """usage event, emitted periodically to indicate usage metrics"""
    END_OF_SPEECH = "end_of_speech"
    """indicate the end of speech, emitted when the user stops speaking"""


@dataclass
class SpeechData:
    language: str
    text: str
    start_time: float = 0.0
    end_time: float = 0.0
    confidence: float = 0.0  # [0, 1]
    speaker_id: str | None = None
    is_primary_speaker: bool | None = None


@dataclass
class RecognitionUsage:
    audio_duration: float


@dataclass
class SpeechEvent:
    type: SpeechEventType
    request_id: str = ""
    alternatives: list[SpeechData] = field(default_factory=list)
    recognition_usage: RecognitionUsage | None = None


@dataclass
class ASRCapabilities:
    streaming: bool
    interim_results: bool


class ASRError(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: Literal["asr_error"] = "asr_error"
    timestamp: float
    label: str
    error: Exception = Field(..., exclude=True)
    recoverable: bool


class ASR(ABC):
    """
    Base class for Automatic Speech Recognition (ASR) providers.
    
    This is a modern, async-first ASR interface inspired by LiveKit's design.
    Providers should inherit from this class and implement the required methods.
    """
    
    def __init__(self, *, capabilities: ASRCapabilities) -> None:
        """
        Initialize ASR provider.
        
        Args:
            capabilities: ASR capabilities (streaming support, interim results, etc.)
        """
        self._capabilities = capabilities
        self._label = f"{type(self).__module__}.{type(self).__name__}"
    
    @property
    def label(self) -> str:
        """Get the ASR provider label (module.ClassName)"""
        return self._label
    
    @property
    def model(self) -> str:
        """
        Get the model name/identifier for this ASR instance.
        
        Returns:
            The model name if available, "unknown" otherwise.
        
        Note:
            Providers should override this property to provide their model information.
        """
        return "unknown"
    
    @property
    def provider(self) -> str:
        """
        Get the provider name/identifier for this ASR instance.
        
        Returns:
            The provider name if available, "unknown" otherwise.
        
        Note:
            Providers should override this property to provide their provider information.
        """
        return "unknown"
    
    @property
    def capabilities(self) -> ASRCapabilities:
        """Get ASR capabilities"""
        return self._capabilities
    
    @abstractmethod
    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> SpeechEvent:
        """
        Provider-specific recognition implementation.
        
        This method should be implemented by ASR providers to perform
        the actual speech recognition on the provided audio buffer.
        
        Args:
            buffer: Audio buffer (list of AudioFrame or single AudioFrame)
            language: Optional language code for recognition
            conn_options: Connection options for API calls
        
        Returns:
            SpeechEvent: Recognition result with transcript and metadata
        """
        ...
    
    async def recognize(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> SpeechEvent:
        """
        Recognize speech from audio buffer (non-streaming).
        
        This method provides retry logic and error handling around _recognize_impl().
        
        Args:
            buffer: Audio buffer (list of AudioFrame or single AudioFrame)
            language: Optional language code for recognition
            conn_options: Connection options for API calls
        
        Returns:
            SpeechEvent: Recognition result with transcript and metadata
        """
        for i in range(conn_options.max_retry + 1):
            try:
                event = await self._recognize_impl(
                    buffer, language=language, conn_options=conn_options
                )
                return event
            
            except APIError as e:
                retry_interval = conn_options.retry_interval
                if conn_options.max_retry == 0:
                    self._emit_error(e, recoverable=False)
                    raise
                elif i == conn_options.max_retry:
                    self._emit_error(e, recoverable=False)
                    raise APIConnectionError(
                        f"failed to recognize speech after {conn_options.max_retry + 1} attempts"
                    ) from e
                else:
                    self._emit_error(e, recoverable=True)
                    logger.bind(tag=TAG).warning(
                        f"failed to recognize speech, retrying in {retry_interval}s",
                        exc_info=e,
                        extra={
                            "asr": self._label,
                            "attempt": i + 1,
                            "streamed": False,
                        },
                    )
                
                await asyncio.sleep(retry_interval)
            
            except Exception as e:
                self._emit_error(e, recoverable=False)
                raise
        
        raise RuntimeError("unreachable")
    
    def _emit_error(self, api_error: Exception, recoverable: bool) -> None:
        """Emit an error event (placeholder for future event emitter support)"""
        logger.bind(tag=TAG).error(
            f"ASR error: {api_error}",
            extra={"asr": self._label, "recoverable": recoverable},
            exc_info=api_error,
        )
    
    def stream(
        self,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "RecognizeStream":
        """
        Create a streaming recognition session.
        
        This method creates a stream that allows audio frames to be pushed incrementally.
        Audio frames can be added via push_frame() and the stream will transcribe as audio arrives.
        
        Args:
            language: Optional language code for recognition (e.g., "en", "zh", "multi")
            conn_options: Connection options for the API (timeout, retry, etc.)
        
        Returns:
            RecognizeStream: A streaming recognition session
        
        Raises:
            NotImplementedError: If streaming is not supported by this ASR
        """
        raise NotImplementedError(
            "streaming is not supported by this ASR, "
            "please use a different ASR or use a StreamAdapter"
        )
    
    def prewarm(self) -> None:
        """
        Pre-warm connection to the ASR service.
        
        This method can be called to establish connections or initialize
        resources before actual recognition begins, reducing latency.
        """
        pass
    
    async def aclose(self) -> None:
        """
        Close the ASR provider and clean up resources.
        
        This method should be called when the ASR provider is no longer needed.
        It will close all active streams and release any held resources.
        """
        pass
    
    async def __aenter__(self) -> "ASR":
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


class RecognizeStream(ABC):
    """
    Base class for streaming recognition (push audio frames incrementally).
    
    This class handles:
    1. Input audio frame channel (for incremental audio input)
    2. Output speech event channel (for recognition results)
    3. Flush/end_input semantics
    4. Error handling and retry logic
    
    Providers should inherit from this class and implement _run().
    """
    
    class _FlushSentinel:
        """Sentinel to mark segment boundaries"""
        pass
    
    def __init__(
        self,
        *,
        asr: ASR,
        conn_options: APIConnectOptions,
        sample_rate: NotGivenOr[int] = NOT_GIVEN,
        language: NotGivenOr[str] = NOT_GIVEN,
    ) -> None:
        """
        Initialize RecognizeStream.
        
        Args:
            asr: The ASR provider instance
            conn_options: Connection options for API calls
            sample_rate: Optional desired sample rate (for future resampling support)
            language: Optional language code for recognition
        """
        self._asr = asr
        self._conn_options = conn_options
        self._language = language
        self._needed_sr = sample_rate if is_given(sample_rate) else None
        self._pushed_sr = 0
        
        self._input_ch: Chan[Union[AudioFrame, RecognizeStream._FlushSentinel]] = Chan()
        self._event_ch: Chan[SpeechEvent] = Chan()
        
        # TODO: If metrics monitoring is needed in the future, the event channel should be teed
        #       to allow multiple consumers (main stream and metrics monitor)
        #       Example: self._event_aiter, monitor_aiter = tee(self._event_ch, 2)
        self._event_aiter = self._event_ch
        self._task = asyncio.create_task(self._main_task(), name="RecognizeStream._main_task")
        self._task.add_done_callback(lambda _: self._event_ch.close())
        
        self._num_retries = 0
    
    @abstractmethod
    async def _run(self) -> None:
        """
        Provider-specific streaming recognition implementation.
        
        This method should:
        1. Set up parallel tasks to:
           - Read from self._input_ch and process audio frames
           - Call ASR API and push recognition results to self._event_ch
           - Handle flush signals and end_of_input
        
        The method should push SpeechEvent objects to self._event_ch as recognition
        results become available.
        """
        ...
    
    async def _main_task(self) -> None:
        """Main task to orchestrate streaming recognition with retry logic"""
        max_retries = self._conn_options.max_retry
        
        while self._num_retries <= max_retries:
            try:
                return await self._run()
            except APIError as e:
                if max_retries == 0:
                    self._emit_error(e, recoverable=False)
                    raise
                elif self._num_retries == max_retries:
                    self._emit_error(e, recoverable=False)
                    raise APIConnectionError(
                        f"failed to recognize speech after {self._num_retries + 1} attempts"
                    ) from e
                else:
                    self._emit_error(e, recoverable=True)
                    
                    retry_interval = self._conn_options.retry_interval
                    logger.bind(tag=TAG).warning(
                        f"failed to recognize speech, retrying in {retry_interval}s",
                        extra={
                            "asr": self._asr._label,
                            "attempt": self._num_retries + 1,
                            "streamed": True,
                        },
                    )
                    await asyncio.sleep(retry_interval)
                
                self._num_retries += 1
            
            except Exception as e:
                self._emit_error(e, recoverable=False)
                raise
    
    def _emit_error(self, api_error: Exception, recoverable: bool) -> None:
        """Emit an error event (placeholder for future event emitter support)"""
        logger.bind(tag=TAG).error(
            f"ASR error: {api_error}",
            extra={"asr": self._asr._label, "recoverable": recoverable},
            exc_info=api_error,
        )
    
    def push_frame(self, frame: AudioFrame) -> None:
        """Push audio frame to be recognized"""
        self._check_input_not_ended()
        self._check_not_closed()
        
        if self._pushed_sr and self._pushed_sr != frame.sample_rate:
            raise ValueError("the sample rate of the input frames must be consistent")
        
        self._pushed_sr = frame.sample_rate
        
        # TODO: Implement resampling if _needed_sr is set and differs from frame.sample_rate
        # For now, just pass through the frame
        
        self._input_ch.send_nowait(frame)
    
    def flush(self) -> None:
        """Mark the end of the current segment"""
        self._check_input_not_ended()
        self._check_not_closed()
        
        self._input_ch.send_nowait(self._FlushSentinel())
    
    def end_input(self) -> None:
        """Mark the end of input, no more audio will be pushed"""
        self.flush()
        self._input_ch.close()
    
    async def aclose(self) -> None:
        """Close the stream immediately"""
        self._input_ch.close()
        await cancel_and_wait(self._task)
        self._event_ch.close()
    
    async def __anext__(self) -> SpeechEvent:
        try:
            val = await self._event_aiter.__anext__()
        except StopAsyncIteration:
            if not self._task.cancelled() and (exc := self._task.exception()):
                raise exc  # noqa: B904
            
            raise StopAsyncIteration from None
        
        return val
    
    def __aiter__(self) -> AsyncIterator[SpeechEvent]:
        return self
    
    def _check_not_closed(self) -> None:
        if self._event_ch.closed:
            cls = type(self)
            raise RuntimeError(f"{cls.__module__}.{cls.__name__} is closed")
    
    def _check_input_not_ended(self) -> None:
        if self._input_ch.closed:
            cls = type(self)
            raise RuntimeError(f"{cls.__module__}.{cls.__name__} input ended")
    
    async def __aenter__(self) -> "RecognizeStream":
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


class StreamAdapter(ASR):
    """
    Wrap a non-streaming ASR to provide streaming interface.
    
    This adapter enables any ASR that supports non-streaming recognition
    (via speech_to_text method) to be used with the streaming API.
    It handles:
    - Audio frame buffering
    - VAD-based segmentation (when VAD is available)
    - Sequential recognition of audio segments
    - Streaming recognition results
    
    Example:
        # Wrap a non-streaming ASR
        base_asr = SomeASR(...)
        streaming_asr = StreamAdapter(
            asr=base_asr,
            vad=vad_instance  # Optional VAD for segmentation
        )
        
        # Now use it as a streaming ASR
        stream = streaming_asr.stream()
        stream.push_frame(frame1)
        stream.push_frame(frame2)
        stream.end_input()
        
        async for event in stream:
            # Process recognition events
            pass
    """
    
    def __init__(
        self,
        *,
        asr: "ASR",
        vad: "VAD | None" = None,
    ) -> None:
        """
        Initialize StreamAdapter.
        
        Args:
            asr: The non-streaming ASR to wrap
            vad: Optional VAD for automatic segmentation.
                 If provided, VAD will be used to detect speech boundaries.
                 If not provided, manual flush() calls are required.
        """
        super().__init__(
            capabilities=ASRCapabilities(
                streaming=True,
                interim_results=False,  # Non-streaming ASR doesn't support interim results
            )
        )
        self._wrapped_asr = asr
        self._vad = vad
    
    @property
    def model(self) -> str:
        """Get the model from wrapped ASR"""
        return self._wrapped_asr.model
    
    @property
    def provider(self) -> str:
        """Get the provider from wrapped ASR"""
        return self._wrapped_asr.provider
    
    def stream(
        self,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "StreamAdapterWrapper":
        """
        Create a streaming recognition session.
        
        Args:
            language: Optional language code for recognition
            conn_options: Connection options for API calls
        
        Returns:
            StreamAdapterWrapper: A streaming wrapper around the non-streaming ASR
        """
        return StreamAdapterWrapper(
            asr=self,
            wrapped_asr=self._wrapped_asr,
            vad=self._vad,
            language=language,
            conn_options=conn_options,
        )
    
    async def aclose(self) -> None:
        """Close the wrapped ASR"""
        await self._wrapped_asr.aclose()


class StreamAdapterWrapper(RecognizeStream):
    """
    Streaming wrapper that recognizes audio segments sequentially.
    
    This class orchestrates:
    1. Reading audio frames from input channel
    2. Buffering frames until segmentation boundary (VAD or flush)
    3. Calling wrapped ASR's speech_to_text for each segment
    4. Streaming recognition results
    """
    
    def __init__(
        self,
        *,
        asr: StreamAdapter,
        wrapped_asr: ASR,
        vad: "VAD | None",
        language: NotGivenOr[str],
        conn_options: APIConnectOptions,
    ) -> None:
        """
        Initialize StreamAdapterWrapper.
        
        Args:
            asr: The StreamAdapter instance
            wrapped_asr: The wrapped non-streaming ASR
            vad: Optional VAD for segmentation
            language: Optional language code
            conn_options: Connection options
        """
        super().__init__(asr=asr, conn_options=conn_options, language=language)
        self._stream_adapter = asr
        self._wrapped_asr = wrapped_asr
        self._vad = vad
    
    async def _run(self) -> None:
        """
        Main streaming recognition logic.
        
        This method:
        1. Buffers audio frames
        2. Uses VAD (if available) or flush signals to segment audio
        3. Calls wrapped ASR for each segment
        4. Streams recognition results
        """
        from core.audio.audio_frame import AudioFrame
        
        request_id = shortuuid("asr_request_")
        audio_buffer: list[AudioFrame] = []
        
        # If VAD is available, use it for segmentation
        if self._vad:
            await self._run_with_vad(request_id, audio_buffer)
        else:
            await self._run_without_vad(request_id, audio_buffer)
    
    async def _run_with_vad(
        self, request_id: str, audio_buffer: list[AudioFrame]
    ) -> None:
        """Run recognition with VAD-based segmentation"""
        # TODO: Implement VAD-based segmentation
        # This will require:
        # 1. Forwarding audio frames to VAD stream
        # 2. Listening for VAD events (START_OF_SPEECH, END_OF_SPEECH)
        # 3. Buffering frames during speech
        # 4. Recognizing complete segments on END_OF_SPEECH
        # 5. StreamAdapter from livekit-agents provides a good reference
        
        raise NotImplementedError(
            "VAD-based segmentation is not yet implemented. "
            "Please use manual flush() calls or implement VAD support."
        )
    
    async def _run_without_vad(
        self, request_id: str, audio_buffer: list[AudioFrame]
    ) -> None:
        """Run recognition with manual flush-based segmentation"""
        from core.audio.audio_frame import AudioFrame
        
        async def _forward_input() -> None:
            """Forward audio frames from input channel to buffer"""
            async for data in self._input_ch:
                if isinstance(data, self._FlushSentinel):
                    # Flush signal - recognize current buffer
                    if audio_buffer:
                        await self._recognize_segment(request_id, audio_buffer)
                        audio_buffer.clear()
                    continue
                
                if isinstance(data, AudioFrame):
                    audio_buffer.append(data)
            
            # End of input - recognize any remaining buffer
            if audio_buffer:
                await self._recognize_segment(request_id, audio_buffer)
        
        await _forward_input()
    
    async def _recognize_segment(
        self, request_id: str, frames: list[AudioFrame]
    ) -> None:
        """
        Recognize a segment of audio frames using the wrapped ASR.
        
        Args:
            request_id: Request ID for this recognition segment
            frames: List of audio frames to recognize
        """
        if not frames:
            return
        
        # Use recognize() method from ASR base class
        # Convert frames list to AudioBuffer (list[AudioFrame])
        try:
            event = await self._wrapped_asr.recognize(
                buffer=frames,
                language=self._language if is_given(self._language) else NOT_GIVEN,
                conn_options=self._conn_options,
            )
            
            # Update request_id if needed
            if event.request_id != request_id:
                event.request_id = request_id
            
            # Emit the recognition event
            self._event_ch.send_nowait(event)
            
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Recognition failed: {e}",
                extra={
                    "asr": self._wrapped_asr._label,
                    "request_id": request_id,
                },
                exc_info=e,
            )
            raise APIError(f"Recognition failed: {e}") from e

from __future__ import annotations


import os
import re
import time
import uuid
import queue
import asyncio
import threading
import traceback
from dataclasses import dataclass
from core.utils import p3
from datetime import datetime
from core.utils import textUtils
from typing import Callable, Any, Union, AsyncIterator
from types import TracebackType
from abc import ABC, abstractmethod
from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.utils.output_counter import add_device_output
from core.handle.reportHandle import enqueue_tts_report
from core.handle.sendAudioHandle import sendAudioMessage
from core.utils.util import audio_bytes_to_data_stream, audio_to_data_stream
from core.providers.tts.dto.dto import (
    TTSMessageDTO,
    SentenceType,
    ContentType,
    InterfaceType,
)
import core.audio as audio


TAG = __name__
logger = setup_logging()


class TTSProviderBase(ABC):
    def __init__(self, config, delete_audio_file):
        self.interface_type = InterfaceType.NON_STREAM
        self.conn = None
        self.delete_audio_file = delete_audio_file
        self.audio_file_type = "wav"
        self.output_file = config.get("output_dir", "tmp/")
        self.tts_text_queue = queue.Queue()
        self.tts_audio_queue = queue.Queue()
        self.tts_audio_first_sentence = True
        self.before_stop_play_files = []

        self.tts_text_buff = []
        self.punctuations = (
            "。",
            "？",
            "?",
            "！",
            "!",
            "；",
            ";",
            "：",
        )
        self.first_sentence_punctuations = (
            "，",
            "~",
            "、",
            ",",
            "。",
            "？",
            "?",
            "！",
            "!",
            "；",
            ";",
            "：",
        )
        self.tts_stop_request = False
        self.processed_chars = 0
        self.is_first_sentence = True

    def generate_filename(self, extension=".wav"):
        return os.path.join(
            self.output_file,
            f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}",
        )

    def handle_opus(self, opus_data: bytes):
        logger.bind(tag=TAG).debug(f"推送数据到队列里面帧数～～ {len(opus_data)}")
        self.tts_audio_queue.put((SentenceType.MIDDLE, opus_data, None))

    def handle_audio_file(self, file_audio: bytes, text):
        self.before_stop_play_files.append((file_audio, text))

    def to_tts_stream(self, text, opus_handler: Callable[[bytes], None] = None) -> None:
        text = MarkdownCleaner.clean_markdown(text)
        max_repeat_time = 5
        if self.delete_audio_file:
            # 需要删除文件的直接转为音频数据
            while max_repeat_time > 0:
                try:
                    audio_bytes = asyncio.run(self.text_to_speak(text, None))
                    if audio_bytes:
                        self.tts_audio_queue.put((SentenceType.FIRST, None, text))
                        audio_bytes_to_data_stream(
                            audio_bytes,
                            file_type=self.audio_file_type,
                            is_opus=True,
                            callback=opus_handler,
                        )
                        break
                    else:
                        max_repeat_time -= 1
                except Exception as e:
                    logger.bind(tag=TAG).warning(
                        f"语音生成失败{5 - max_repeat_time + 1}次: {text}，错误: {e}"
                    )
                    max_repeat_time -= 1
            if max_repeat_time > 0:
                logger.bind(tag=TAG).info(
                    f"语音生成成功: {text}，重试{5 - max_repeat_time}次"
                )
            else:
                logger.bind(tag=TAG).error(
                    f"语音生成失败: {text}，请检查网络或服务是否正常"
                )
            return None
        else:
            tmp_file = self.generate_filename()
            try:
                while not os.path.exists(tmp_file) and max_repeat_time > 0:
                    try:
                        asyncio.run(self.text_to_speak(text, tmp_file))
                    except Exception as e:
                        logger.bind(tag=TAG).warning(
                            f"语音生成失败{5 - max_repeat_time + 1}次: {text}，错误: {e}"
                        )
                        # 未执行成功，删除文件
                        if os.path.exists(tmp_file):
                            os.remove(tmp_file)
                        max_repeat_time -= 1

                if max_repeat_time > 0:
                    logger.bind(tag=TAG).info(
                        f"语音生成成功: {text}:{tmp_file}，重试{5 - max_repeat_time}次"
                    )
                else:
                    logger.bind(tag=TAG).error(
                        f"语音生成失败: {text}，请检查网络或服务是否正常"
                    )
                    self.tts_audio_queue.put((SentenceType.FIRST, None, text))
                self._process_audio_file_stream(tmp_file, callback=opus_handler)
            except Exception as e:
                logger.bind(tag=TAG).error(f"Failed to generate TTS file: {e}")
                return None
    
    def to_tts(self, text):
        text = MarkdownCleaner.clean_markdown(text)
        max_repeat_time = 5
        if self.delete_audio_file:
            # 需要删除文件的直接转为音频数据
            while max_repeat_time > 0:
                try:
                    audio_bytes = asyncio.run(self.text_to_speak(text, None))
                    if audio_bytes:
                        audio_datas = []
                        audio_bytes_to_data_stream(
                            audio_bytes,
                            file_type=self.audio_file_type,
                            is_opus=True,
                            callback=lambda data: audio_datas.append(data)
                        )
                        return audio_datas
                    else:
                        max_repeat_time -= 1
                except Exception as e:
                    logger.bind(tag=TAG).warning(
                        f"语音生成失败{5 - max_repeat_time + 1}次: {text}，错误: {e}"
                    )
                    max_repeat_time -= 1
            if max_repeat_time > 0:
                logger.bind(tag=TAG).info(
                    f"语音生成成功: {text}，重试{5 - max_repeat_time}次"
                )
            else:
                logger.bind(tag=TAG).error(
                    f"语音生成失败: {text}，请检查网络或服务是否正常"
                )
            return None
        else:
            tmp_file = self.generate_filename()
            try:
                while not os.path.exists(tmp_file) and max_repeat_time > 0:
                    try:
                        asyncio.run(self.text_to_speak(text, tmp_file))
                    except Exception as e:
                        logger.bind(tag=TAG).warning(
                            f"语音生成失败{5 - max_repeat_time + 1}次: {text}，错误: {e}"
                        )
                        # 未执行成功，删除文件
                        if os.path.exists(tmp_file):
                            os.remove(tmp_file)
                        max_repeat_time -= 1

                if max_repeat_time > 0:
                    logger.bind(tag=TAG).info(
                        f"语音生成成功: {text}:{tmp_file}，重试{5 - max_repeat_time}次"
                    )
                else:
                    logger.bind(tag=TAG).error(
                        f"语音生成失败: {text}，请检查网络或服务是否正常"
                    )

                return tmp_file
            except Exception as e:
                logger.bind(tag=TAG).error(f"Failed to generate TTS file: {e}")
                return None

    @abstractmethod
    async def text_to_speak(self, text, output_file):
        pass

    def audio_to_pcm_data_stream(
        self, audio_file_path, callback: Callable[[Any], Any] = None
    ):
        """音频文件转换为PCM编码"""
        return audio_to_data_stream(audio_file_path, is_opus=False, callback=callback)

    def audio_to_opus_data_stream(
        self, audio_file_path, callback: Callable[[Any], Any] = None
    ):
        """音频文件转换为Opus编码"""
        return audio_to_data_stream(audio_file_path, is_opus=True, callback=callback)

    def tts_one_sentence(
        self,
        conn,
        content_type,
        content_detail=None,
        content_file=None,
        sentence_id=None,
    ):
        """发送一句话"""
        if not sentence_id:
            if conn.sentence_id:
                sentence_id = conn.sentence_id
            else:
                sentence_id = str(uuid.uuid4().hex)
                conn.sentence_id = sentence_id
        # 对于单句的文本，进行分段处理
        segments = re.split(r"([。！？!?；;\n])", content_detail)
        for seg in segments:
            self.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=sentence_id,
                    sentence_type=SentenceType.MIDDLE,
                    content_type=content_type,
                    content_detail=seg,
                    content_file=content_file,
                )
            )

    async def open_audio_channels(self, conn):
        self.conn = conn
        # tts 消化线程
        self.tts_priority_thread = threading.Thread(
            target=self.tts_text_priority_thread, daemon=True
        )
        self.tts_priority_thread.start()

        # 音频播放 消化线程
        self.audio_play_priority_thread = threading.Thread(
            target=self._audio_play_priority_thread, daemon=True
        )
        self.audio_play_priority_thread.start()

    # 这里默认是非流式的处理方式
    # 流式处理方式请在子类中重写
    def tts_text_priority_thread(self):
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("收到打断信息，终止TTS文本处理线程")
                    continue
                if message.sentence_type == SentenceType.FIRST:
                    # 初始化参数
                    self.tts_stop_request = False
                    self.processed_chars = 0
                    self.tts_text_buff = []
                    self.is_first_sentence = True
                    self.tts_audio_first_sentence = True
                elif ContentType.TEXT == message.content_type:
                    self.tts_text_buff.append(message.content_detail)
                    segment_text = self._get_segment_text()
                    if segment_text:
                        self.to_tts_stream(segment_text, opus_handler=self.handle_opus)
                elif ContentType.FILE == message.content_type:
                    self._process_remaining_text_stream(opus_handler=self.handle_opus)
                    tts_file = message.content_file
                    if tts_file and os.path.exists(tts_file):
                        self._process_audio_file_stream(
                            tts_file, callback=self.handle_opus
                        )
                if message.sentence_type == SentenceType.LAST:
                    self._process_remaining_text_stream(opus_handler=self.handle_opus)
                    self.tts_audio_queue.put(
                        (message.sentence_type, [], message.content_detail)
                    )

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"处理TTS文本失败: {str(e)}, 类型: {type(e).__name__}, 堆栈: {traceback.format_exc()}"
                )
                continue

    def _audio_play_priority_thread(self):
        # 需要上报的文本和音频列表
        enqueue_text = None
        enqueue_audio = None
        while not self.conn.stop_event.is_set():
            text = None
            try:
                try:
                    sentence_type, audio_datas, text = self.tts_audio_queue.get(
                        timeout=0.1
                    )
                except queue.Empty:
                    if self.conn.stop_event.is_set():
                        break
                    continue

                if self.conn.client_abort:
                    logger.bind(tag=TAG).debug("收到打断信号，跳过当前音频数据")
                    enqueue_text, enqueue_audio = None, []
                    continue

                # 收到下一个文本开始或会话结束时进行上报
                if sentence_type is not SentenceType.MIDDLE:
                    # 上报TTS数据
                    if enqueue_text is not None and enqueue_audio is not None:
                        enqueue_tts_report(self.conn, enqueue_text, enqueue_audio)
                    enqueue_audio = []
                    enqueue_text = text

                # 收集上报音频数据
                if isinstance(audio_datas, bytes) and enqueue_audio is not None:
                    enqueue_audio.append(audio_datas)

                # 发送音频
                future = asyncio.run_coroutine_threadsafe(
                    sendAudioMessage(self.conn, sentence_type, audio_datas, text),
                    self.conn.loop,
                )
                future.result()

                # 记录输出和报告
                if self.conn.max_output_size > 0 and text:
                    add_device_output(self.conn.headers.get("device-id"), len(text))

            except Exception as e:
                logger.bind(tag=TAG).error(f"audio_play_priority_thread: {text} {e}")

    async def start_session(self, session_id):
        pass

    async def finish_session(self, session_id):
        pass

    async def close(self):
        """资源清理方法"""
        if hasattr(self, "ws") and self.ws:
            await self.ws.close()

    def _get_segment_text(self):
        # 合并当前全部文本并处理未分割部分
        full_text = "".join(self.tts_text_buff)
        current_text = full_text[self.processed_chars :]  # 从未处理的位置开始
        last_punct_pos = -1

        # 根据是否是第一句话选择不同的标点符号集合
        punctuations_to_use = (
            self.first_sentence_punctuations
            if self.is_first_sentence
            else self.punctuations
        )

        for punct in punctuations_to_use:
            pos = current_text.rfind(punct)
            if (pos != -1 and last_punct_pos == -1) or (
                pos != -1 and pos < last_punct_pos
            ):
                last_punct_pos = pos

        if last_punct_pos != -1:
            segment_text_raw = current_text[: last_punct_pos + 1]
            segment_text = textUtils.get_string_no_punctuation_or_emoji(
                segment_text_raw
            )
            self.processed_chars += len(segment_text_raw)  # 更新已处理字符位置

            # 如果是第一句话，在找到第一个逗号后，将标志设置为False
            if self.is_first_sentence:
                self.is_first_sentence = False

            return segment_text
        elif self.tts_stop_request and current_text:
            segment_text = current_text
            self.is_first_sentence = True  # 重置标志
            return segment_text
        else:
            return None

    def _process_audio_file_stream(
        self, tts_file, callback: Callable[[Any], Any]
    ) -> None:
        """处理音频文件并转换为指定格式

        Args:
            tts_file: 音频文件路径
            callback: 文件处理函数
        """
        if tts_file.endswith(".p3"):
            p3.decode_opus_from_file_stream(tts_file, callback=callback)
        elif self.conn.audio_format == "pcm":
            self.audio_to_pcm_data_stream(tts_file, callback=callback)
        else:
            self.audio_to_opus_data_stream(tts_file, callback=callback)

        if (
            self.delete_audio_file
            and tts_file is not None
            and os.path.exists(tts_file)
            and tts_file.startswith(self.output_file)
        ):
            os.remove(tts_file)

    def _process_before_stop_play_files(self):
        for audio_datas, text in self.before_stop_play_files:
            self.tts_audio_queue.put((SentenceType.MIDDLE, audio_datas, text))
        self.before_stop_play_files.clear()
        self.tts_audio_queue.put((SentenceType.LAST, [], None))

    def _process_remaining_text_stream(
        self, opus_handler: Callable[[bytes], None] = None
    ):
        """处理剩余的文本并生成语音

        Returns:
            bool: 是否成功处理了文本
        """
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars :]
        if remaining_text:
            segment_text = textUtils.get_string_no_punctuation_or_emoji(remaining_text)
            if segment_text:
                self.to_tts_stream(segment_text, opus_handler=opus_handler)
                self.processed_chars += len(full_text)
                return True
        return False


# ============================================================================
# TTS Stream Basic Data Structures
# ============================================================================
@dataclass
class SynthesizedAudio:
    """
    Represents synthesized audio output from the TTS pipeline.
    
    This is the standard output format for the streaming TTS pipeline,
    containing audio data along with metadata for tracking and synchronization.
    
    Attributes:
        frame: The audio frame containing PCM audio data
        request_id: Unique identifier for the TTS request
        segment_id: Unique identifier for the segment (multiple frames can belong to one segment)
        is_final: Whether this is the final frame of the current segment
        delta_text: The text fragment corresponding to this audio frame (for subtitle sync)
    """
    frame: audio.AudioFrame
    request_id: str
    segment_id: str = ""
    is_final: bool = False
    delta_text: str = ""


@dataclass
class TTSCapabilities:
    """TTS capabilities descriptor"""
    streaming: bool
    """Whether this TTS supports streaming (generally using websockets)"""


# ============================================================================
# TTS Base Classes
# ============================================================================

class TTS(ABC):
    """
    Base class for Text-to-Speech providers.
    
    This is a modern, async-first TTS interface inspired by LiveKit's design.
    Providers should inherit from this class and implement the required methods.
    """
    
    def __init__(
        self,
        *,
        capabilities: TTSCapabilities,
        sample_rate: int,
        num_channels: int,
    ) -> None:
        """
        Initialize TTS provider.
        
        Args:
            capabilities: TTS capabilities (streaming support, etc.)
            sample_rate: Audio sample rate (e.g., 16000, 24000)
            num_channels: Number of audio channels (1=mono, 2=stereo)
        """
        self._capabilities = capabilities
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._label = f"{type(self).__module__}.{type(self).__name__}"
    
    @property
    def label(self) -> str:
        """Get the TTS provider label (module.ClassName)"""
        return self._label
    
    @property
    def model(self) -> str:
        """
        Get the model name/identifier for this TTS instance.
        
        Returns:
            The model name if available, "unknown" otherwise.
        
        Note:
            Providers should override this property to provide their model information.
        """
        return "unknown"
    
    @property
    def provider(self) -> str:
        """
        Get the provider name/identifier for this TTS instance.
        
        Returns:
            The provider name if available, "unknown" otherwise.
        
        Note:
            Providers should override this property to provide their provider information.
        """
        return "unknown"
    
    @property
    def capabilities(self) -> TTSCapabilities:
        """Get TTS capabilities"""
        return self._capabilities
    
    @property
    def sample_rate(self) -> int:
        """Get audio sample rate"""
        return self._sample_rate
    
    @property
    def num_channels(self) -> int:
        """Get number of audio channels"""
        return self._num_channels
    
    @abstractmethod
    def synthesize(self, text: str) -> 'ChunkedStream':
        """
        Synthesize speech from text (non-streaming).
        
        This method creates a stream that synthesizes the entire text at once.
        The text is provided upfront and cannot be modified during synthesis.
        
        Args:
            text: The text to synthesize
        
        Returns:
            ChunkedStream: An async iterator that yields SynthesizedAudio frames
        """
        ...
    
    def stream(self) -> 'SynthesizeStream':
        """
        Create a streaming synthesis session.
        
        This method creates a stream that allows text to be pushed incrementally.
        Text can be added via push_text() and the stream will synthesize as text arrives.
        
        Returns:
            SynthesizeStream: A streaming synthesis session
        
        Raises:
            NotImplementedError: If streaming is not supported by this TTS
        """
        raise NotImplementedError(
            "streaming is not supported by this TTS, "
            "please use a different TTS or use a StreamAdapter"
        )
    
    def prewarm(self) -> None:
        """
        Pre-warm connection to the TTS service.
        
        This method can be called to establish connections or initialize
        resources before actual synthesis begins, reducing latency.
        """
        pass
    
    async def aclose(self) -> None:
        """
        Close the TTS provider and cleanup resources.
        
        This method should be called when the TTS provider is no longer needed.
        It should close any open connections, cancel pending tasks, and release resources.
        """
        pass
    
    async def __aenter__(self) -> 'TTS':
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


class ChunkedStream(ABC):
    """
    Base class for non-streaming synthesis (synthesize full text at once).
    
    This class handles the orchestration of:
    1. Creating an AudioEmitter
    2. Calling the provider's _run() method to synthesize
    3. Managing the output event channel
    4. Cleanup and error handling
    
    Providers should inherit from this class and implement _run().
    """
    
    def __init__(
        self,
        *,
        tts: TTS,
        input_text: str,
    ) -> None:
        """
        Initialize ChunkedStream.
        
        Args:
            tts: The TTS provider instance
            input_text: The text to synthesize
        """
        from core.utils.aio import Chan
        
        self._input_text = input_text
        self._tts = tts
        self._event_ch: Chan[SynthesizedAudio] = Chan()
        self._synthesize_task = asyncio.create_task(
            self._main_task(), 
            name="ChunkedStream._main_task"
        )
        self._synthesize_task.add_done_callback(lambda _: self._event_ch.close())
    
    @property
    def input_text(self) -> str:
        """Get the input text"""
        return self._input_text
    
    @property
    def done(self) -> bool:
        """Check if synthesis is complete"""
        return self._synthesize_task.done()
    
    @property
    def exception(self) -> BaseException | None:
        """Get exception if synthesis failed"""
        return self._synthesize_task.exception()
    
    @abstractmethod
    async def _run(self, output_emitter: Any) -> None:
        """
        Provider-specific synthesis implementation.
        
        This method should:
        1. Initialize the output_emitter
        2. Call the TTS API to synthesize the input text
        3. Push audio data to output_emitter using output_emitter.push()
        4. Call output_emitter.flush() when done
        
        Args:
            output_emitter: AudioEmitter to push synthesized audio to
        """
        ...
    
    async def _main_task(self) -> None:
        """Main task to orchestrate synthesis"""
        from .emitter import AudioEmitter
        
        output_emitter = AudioEmitter(label=self._tts.label, dst_ch=self._event_ch)
        try:
            await self._run(output_emitter)
            output_emitter.end_input()
            await output_emitter.join()
        finally:
            await output_emitter.aclose()
    
    async def collect(self) -> audio.AudioFrame:
        """
        Utility method to collect all frames into a single AudioFrame.
        
        Returns:
            Combined AudioFrame containing all synthesized audio
        """
        frames = []
        async for ev in self:
            frames.append(ev.frame)
        
        return audio.AudioFrame.combine_frames(frames)
    
    async def aclose(self) -> None:
        """Close the stream and cleanup resources"""
        from core.utils.aio import cancel_and_wait
        
        await cancel_and_wait(self._synthesize_task)
        self._event_ch.close()
    
    async def __anext__(self) -> SynthesizedAudio:
        try:
            val = await self._event_ch.recv()
        except Exception:
            # Check if there was an exception in the synthesis task
            if not self._synthesize_task.cancelled() and (exc := self._synthesize_task.exception()):
                raise exc
            raise StopAsyncIteration from None
        
        return val
    
    def __aiter__(self) -> AsyncIterator[SynthesizedAudio]:
        return self
    
    async def __aenter__(self) -> 'ChunkedStream':
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


class SynthesizeStream(ABC):
    """
    Base class for streaming synthesis (push text incrementally).
    
    This class handles:
    1. Input text channel (for incremental text input)
    2. Output audio channel (for synthesized audio)
    3. Orchestration of AudioEmitter
    4. Flush/end_input semantics
    
    Providers should inherit from this class and implement _run().
    """
    
    class _FlushSentinel:
        """Sentinel to mark segment boundaries"""
        pass
    
    def __init__(self, *, tts: TTS) -> None:
        """
        Initialize SynthesizeStream.
        
        Args:
            tts: The TTS provider instance
        """
        from core.utils.aio import Chan
        
        self._tts = tts
        self._input_ch: Chan[Union[str, SynthesizeStream._FlushSentinel]] = Chan()
        self._event_ch: Chan[SynthesizedAudio] = Chan()
        
        self._task = asyncio.create_task(self._main_task(), name="SynthesizeStream._main_task")
        self._task.add_done_callback(lambda _: self._event_ch.close())
    
    @abstractmethod
    async def _run(self, output_emitter: Any) -> None:
        """
        Provider-specific streaming synthesis implementation.
        
        This method should:
        1. Initialize output_emitter
        2. Create tokenizer/pacer (if needed)
        3. Set up parallel tasks to:
           - Read from self._input_ch and feed to tokenizer
           - Process tokenized text and call TTS API
           - Push audio from TTS to output_emitter
        
        Args:
            output_emitter: AudioEmitter to push synthesized audio to
        """
        ...
    
    async def _main_task(self) -> None:
        """Main task to orchestrate streaming synthesis"""
        from .emitter import AudioEmitter
        
        output_emitter = AudioEmitter(label=self._tts.label, dst_ch=self._event_ch)
        try:
            await self._run(output_emitter)
            output_emitter.end_input()
            await output_emitter.join()
        finally:
            await output_emitter.aclose()
    
    def push_text(self, token: str) -> None:
        """
        Push a text fragment to be synthesized.
        
        Text fragments will be accumulated and processed according to
        the tokenizer/pacer configuration (if any).
        
        Args:
            token: Text fragment to synthesize
        """
        if not token or self._input_ch.closed:
            return
        
        self._input_ch.send_nowait(token)
    
    def flush(self) -> None:
        """
        Mark the end of the current segment.
        
        This signals that all text for the current segment has been pushed.
        The TTS will finish synthesizing the current segment before starting the next.
        """
        if self._input_ch.closed:
            return
        
        self._input_ch.send_nowait(self._FlushSentinel())
    
    def end_input(self) -> None:
        """
        Mark the end of input.
        
        This signals that no more text will be pushed. The TTS will finish
        synthesizing any remaining text and close the stream.
        """
        self.flush()
        self._input_ch.close()
    
    async def aclose(self) -> None:
        """Close the stream immediately and cleanup resources"""
        from core.utils.aio import cancel_and_wait
        
        await cancel_and_wait(self._task)
        self._event_ch.close()
        self._input_ch.close()
    
    async def __anext__(self) -> SynthesizedAudio:
        try:
            val = await self._event_ch.recv()
        except Exception:
            if not self._task.cancelled() and (exc := self._task.exception()):
                raise exc
            raise StopAsyncIteration from None
        
        return val
    
    def __aiter__(self) -> AsyncIterator[SynthesizedAudio]:
        return self
    
    async def __aenter__(self) -> 'SynthesizeStream':
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


# Factory function for creating TTS instances from configuration

async def create_from_config(config, audio_params) -> TTS:
    """
    Factory function to create TTS instance from configuration.
    
    Args:
        config: TTS configuration object (from config.components.tts)
        audio_params: Audio parameters with sample_rate, channels, format
        
    Returns:
        Initialized TTS instance
        
    Raises:
        ValueError: If the specified provider is not supported
        
    Example:
        config = load_config("config.yaml")
        tts = await create_from_config(config.components.tts, config.audio_params)
    """
    import logging
    
    provider = config.provider.lower()
    logging.info(f"Creating TTS: provider={provider}, model={config.model.name}")
    
    if provider == "elevenlabs":
        from core.tts.elevenlabs.tts import TTS as ElevenLabsTTS
        return await ElevenLabsTTS.from_config(config, audio_params)
    elif provider == "cartesia":
        from core.tts.cartesia.tts import TTS as CartesiaTTS
        return await CartesiaTTS.from_config(config, audio_params)
    else:
        raise ValueError(f"Unsupported TTS provider: {provider}")

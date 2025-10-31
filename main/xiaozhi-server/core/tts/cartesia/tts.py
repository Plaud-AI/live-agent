"""
Cartesia TTS Implementation

Provides WebSocket-based streaming text-to-speech using Cartesia's API.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import weakref
from dataclasses import dataclass
from typing import Any

import aiohttp
import logging
from core.tokenize import SentenceTokenizer, blingfire
from core.utils.aio import cancel_and_wait
from core.utils.short_uuid import shortuuid
from core.utils.connection_pool import ConnectionPool
from core.utils.http_context import http_session
from core.utils.errors import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
)
from core.utils.types import (
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS,
)

import core.tts.base as base
from core.tts.base import TTSCapabilities
from ..emitter import AudioEmitter
from ..pacer import SentenceStreamPacer
from .models import API_BASE_URL, API_VERSION, DEFAULT_VOICE_ID, TTSEncoding, TTSModels


"""
TODO: change api to cartesia SDK using streaming API
"""
@dataclass
class _TTSOptions:
    """Internal configuration for Cartesia TTS"""
    model: TTSModels | str
    encoding: TTSEncoding
    sample_rate: int
    voice: str | list[float]
    api_key: str
    language: str
    base_url: str
    api_version: str
    
    def get_ws_url(self) -> str:
        """Get WebSocket URL with API key"""
        base = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        return f"{base}/tts/websocket?api_key={self.api_key}&cartesia_version={self.api_version}"


class TTS(base.TTS):
    """
    Cartesia TTS Provider
    
    Provides high-quality, low-latency text-to-speech with voice cloning support.
    
    Example:
        tts = cartesia.TTS(
            api_key="your-api-key",
            model="sonic-3",
            voice="default-voice-id",
            sample_rate=24000,
        )
        
        # Streaming synthesis
        stream = tts.stream()
        stream.push_text("Hello world!")
        stream.end_input()
        
        async for audio in stream:
            # Process audio
            pass
    """
    
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: TTSModels | str = "sonic-3",
        language: str = "en",
        encoding: TTSEncoding = "pcm_s16le",
        voice: str | list[float] = DEFAULT_VOICE_ID,
        sample_rate: int = 24000,
        sentence_tokenizer: SentenceTokenizer | None = None,
        text_pacing: bool | SentenceStreamPacer = False,
        base_url: str = API_BASE_URL,
        api_version: str = API_VERSION,
    ) -> None:
        """
        Initialize Cartesia TTS.
        
        Args:
            api_key: Cartesia API key. If not provided, reads from CARTESIA_API_KEY env var
            model: TTS model to use (default: "sonic-2")
            language: Language code (default: "en")
            encoding: Audio encoding format (default: "pcm_s16le")
            voice: Voice ID string or embedding array
            sample_rate: Audio sample rate in Hz (default: 24000)
            http_session: Optional aiohttp session for HTTP requests
            sentence_tokenizer: Sentence tokenizer (default: blingfire)
            text_pacing: Enable smart pacing (True/False/SentenceStreamPacer instance)
            base_url: API base URL (default: https://api.cartesia.ai)
            api_version: API version (default: 2025-04-16)
        """
        super().__init__(
            capabilities=TTSCapabilities(streaming=True),
            sample_rate=sample_rate,
            num_channels=1,
        )
        
        # Validate API key
        cartesia_api_key = api_key or os.environ.get("CARTESIA_API_KEY")
        if not cartesia_api_key:
            raise ValueError(
                "Cartesia API key is required. "
                "Provide via api_key parameter or set CARTESIA_API_KEY environment variable"
            )
        
        # Store options
        self._opts = _TTSOptions(
            model=model,
            language=language,
            encoding=encoding,
            sample_rate=sample_rate,
            voice=voice,
            api_key=cartesia_api_key,
            base_url=base_url,
            api_version=api_version,
        )
        
        
        # WebSocket connection pool
        self._pool = ConnectionPool[aiohttp.ClientWebSocketResponse](
            connect_cb=self._connect_ws,
            close_cb=self._close_ws,
            max_session_duration=300,  # 5 minutes
            mark_refreshed_on_get=True,
        )
    
    @classmethod
    async def from_config(cls, config, audio_params) -> TTS:
        """
        Create Cartesia TTS instance from configuration.
        
        Args:
            config: TTS configuration object with structure:
                - provider: "cartesia"
                - model:
                    - name: model name (e.g., "sonic-3")
                    - base_url: optional custom base URL
                - options: optional dict with:
                    - api_key: API key (or from env CARTESIA_API_KEY)
                    - voice: voice ID string or embedding array
                    - language: language code (default: "en")
                    - api_version: API version (default: "2025-04-16")
                    - text_pacing: enable smart pacing (default: False)
            audio_params: Audio parameters with:
                - sample_rate: desired sample rate (e.g., 16000, 24000)
                - channels: number of channels (must be 1)
                - format: audio format (e.g., "opus", "pcm")
        
        Returns:
            Initialized Cartesia TTS instance
        """
        options = config.options or {}
        
        # Validate audio parameters
        sample_rate = audio_params.sample_rate
        if audio_params.channels != 1:
            logging.warning(
                f"Cartesia only supports mono audio, "
                f"but channels={audio_params.channels}. Using mono."
            )
        
        # Cartesia encoding is always pcm_s16le (16-bit signed PCM little-endian)
        encoding: TTSEncoding = "pcm_s16le"
        
        instance = cls(
            api_key=options.get("api_key"),  # Will read from env if not provided
            model=config.model.name,
            language=options.get("language", "en"),
            encoding=encoding,
            voice=options.get("voice", DEFAULT_VOICE_ID),
            sample_rate=sample_rate,
            sentence_tokenizer=None,  # Will use default (blingfire)
            text_pacing=options.get("text_pacing", False),
            base_url=config.model.base_url if config.model.base_url else API_BASE_URL,
            api_version=options.get("api_version", API_VERSION),
        )
        
        logging.info(
            f"✓ Cartesia TTS loaded: model={config.model.name}, "
            f"voice={instance._opts.voice}, "
            f"sample_rate={sample_rate}, "
            f"language={instance._opts.language}"
        )
        
        return instance
        
        # Track active streams for cleanup
        self._streams: weakref.WeakSet[SynthesizeStream] = weakref.WeakSet()
        
        # Tokenizer and pacer
        self._sentence_tokenizer = (
            sentence_tokenizer if sentence_tokenizer else blingfire.SentenceTokenizer()
        )
        
        self._stream_pacer: SentenceStreamPacer | None = None
        if text_pacing is True:
            self._stream_pacer = SentenceStreamPacer()
        elif isinstance(text_pacing, SentenceStreamPacer):
            self._stream_pacer = text_pacing
    
    @property
    def model(self) -> str:
        """Get the model name"""
        return self._opts.model
    
    @property
    def provider(self) -> str:
        """Get the provider name"""
        return "Cartesia"
    
    def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists"""
        return http_session()
    
    async def _connect_ws(self, timeout: float) -> aiohttp.ClientWebSocketResponse:
        """Connect to Cartesia WebSocket (for ConnectionPool)"""
        session = self._ensure_session()
        url = self._opts.get_ws_url()
        
        try:
            return await asyncio.wait_for(session.ws_connect(url), timeout)
        except asyncio.TimeoutError as e:
            raise APITimeoutError(
                f"Connection to Cartesia WebSocket timed out after {timeout}s",
                timeout=timeout,
            ) from e
        except aiohttp.ClientError as e:
            raise APIConnectionError(
                f"Failed to connect to Cartesia WebSocket: {e}",
                url=url,
            ) from e
    
    async def _close_ws(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        """Close WebSocket connection (for ConnectionPool)"""
        await ws.close()
    
    def prewarm(self) -> None:
        """Prewarm WebSocket connection pool"""
        self._pool.prewarm()
    
    def stream(self, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> SynthesizeStream:
        """
        Create a streaming synthesis session.
        
        Returns:
            SynthesizeStream for incremental text input
        """
        stream = SynthesizeStream(tts=self, conn_options=conn_options)
        self._streams.add(stream)
        return stream
    
    async def aclose(self) -> None:
        """Close TTS provider and cleanup resources"""
        # Close all active streams
        for stream in list(self._streams):
            await stream.aclose()
        self._streams.clear()
        
        # Close connection pool
        await self._pool.aclose()

class SynthesizeStream(base.SynthesizeStream):
    """Streaming synthesis using WebSocket"""
    
    def __init__(self, *, tts: TTS, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> None:
        super().__init__(tts=tts, conn_options=conn_options)
        self._tts: TTS = tts
    
    async def _run(self, output_emitter: AudioEmitter) -> None:
        """
        Streaming synthesis implementation.
        
        This method:
        1. Connects to Cartesia WebSocket
        2. Sets up tokenizer (+ optional pacer)
        3. Runs three parallel tasks:
           - _input_task: Reads from input_ch → tokenizer
           - _sentence_task: Tokenizer → WebSocket
           - _recv_task: WebSocket → output_emitter
        """
        opts = self._tts._opts
        request_id = shortuuid()
        
        # Initialize output emitter
        output_emitter.initialize(
            request_id=request_id,
            sample_rate=opts.sample_rate,
            num_channels=1,
            stream=True,
        )
        input_sent_event = asyncio.Event()

        # Create tokenizer stream
        sent_stream = self._tts._sentence_tokenizer.stream()
        
        # Optionally wrap with pacer
        if self._tts._stream_pacer:
            sent_stream = self._tts._stream_pacer.wrap(
                sent_stream=sent_stream,
                audio_emitter=output_emitter,
            )
        
        async def _input_task() -> None:
            """Forward input from input_ch to tokenizer"""
            try:
                async for data in self._input_ch:
                    if isinstance(data, self._FlushSentinel):
                        sent_stream.flush()
                        continue
                    sent_stream.push_text(data)
            finally:
                sent_stream.end_input()
        
        async def _sentence_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            """Send tokenized sentences to WebSocket"""
            context_id = shortuuid()
            base_packet = _to_cartesia_options(opts, streaming=True)
            try:
                async for sentence_ev in sent_stream:
                    # Prepare packet with sentence text
                    packet = base_packet.copy()
                    packet["context_id"] = context_id
                    packet["transcript"] = sentence_ev.token + " "
                    packet["continue"] = True
                    
                    # Send to WebSocket
                    await ws.send_str(json.dumps(packet))
                    input_sent_event.set()
                
                # Send final packet to end synthesis
                end_packet = base_packet.copy()
                end_packet["context_id"] = context_id
                end_packet["transcript"] = " "
                end_packet["continue"] = False
                await ws.send_str(json.dumps(end_packet))
                input_sent_event.set()
            
            except Exception as e:
                logging.error(f"Sentence task error: {e}")
                raise
        
        async def _recv_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            """Receive audio from WebSocket and push to emitter"""

            try:
                current_segment_id: str | None = None
                # Wait for first input
                await input_sent_event.wait()
                
                while True:
                    msg = await ws.receive(timeout=30)
                    
                    if msg.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSE,
                        aiohttp.WSMsgType.CLOSING,
                    ):
                        raise APIStatusError(
                        "Cartesia connection closed unexpectedly", request_id=request_id
                    )
                    
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        logging.warning(f"Unexpected message type: {msg.type}")
                        continue
                    
                    # Parse response
                    response = json.loads(msg.data)
                    segment_id = response.get("context_id")
                    if current_segment_id is None:
                        current_segment_id = segment_id
                        output_emitter.start_segment(segment_id=segment_id)
                    if response.get("data"):
                        b64data = base64.b64decode(response["data"])
                        output_emitter.push(b64data)
                    elif response.get("done"):
                        if sent_stream.closed:
                            output_emitter.end_input()
                            break
            
            except asyncio.TimeoutError:
                logging.error("Cartesia WebSocket receive timeout")
                raise
            except Exception as e:
                logging.error(f"Receive task error: {e}")
                raise
        
        # Get WebSocket from pool and run tasks
        try:
            async with self._tts._pool.connection(timeout=10) as ws:
                tasks = [
                    asyncio.create_task(_input_task(), name="cartesia_input"),
                    asyncio.create_task(_sentence_task(ws), name="cartesia_sentence"),
                    asyncio.create_task(_recv_task(ws), name="cartesia_recv"),
                ]
                
                try:
                    await asyncio.gather(*tasks)
                finally:
                    input_sent_event.set()  # Ensure all tasks can proceed
                    await sent_stream.aclose()
                    await cancel_and_wait(*tasks)
        
        except Exception as e:
            logging.error(f"Cartesia WebSocket error: {e}")
            raise

def _to_cartesia_options(opts: _TTSOptions) -> dict[str, Any]:
    """Convert options to Cartesia API format"""
    voice: dict[str, Any] = {}
    if isinstance(opts.voice, str):
        voice["mode"] = "id"
        voice["id"] = opts.voice
    else:
        voice["mode"] = "embedding"
        voice["embedding"] = opts.voice

    return {
        "model_id": opts.model,
        "voice": voice,
        "output_format": {
            "container": "raw",
            "encoding": opts.encoding,
            "sample_rate": opts.sample_rate,
        },
        "language": opts.language,
    }
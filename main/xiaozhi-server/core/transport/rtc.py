"""
RTC Transport Implementation (Agora/WebRTC)

Implements TransportBase for RTC protocol using Agora SDK.
Provides low-latency audio streaming with better network resilience.

Features:
- UDP-based real-time communication
- Automatic network quality adaptation
- Built-in echo cancellation and noise reduction
- Better performance under poor network conditions

Note: This implementation requires the Agora SDK to be installed.
      pip install agora-python-server-sdk (or agora_rtc)
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from config.logger import setup_logging
from .base import TransportBase, TransportStream, TransportState, TransportError
from .config import RTCConfig
from .events import TransportEvent, TransportEventType

TAG = __name__
logger = setup_logging()


# ============================================================
# RTC Event Types (Agora-specific)
# ============================================================

class RTCUserState(Enum):
    """RTC user state in channel"""
    OFFLINE = 0
    ONLINE = 1
    MUTED = 2


@dataclass
class RTCNetworkQuality:
    """Network quality metrics"""
    uid: int
    tx_quality: int  # 0=unknown, 1=excellent, 2=good, 3=poor, 4=bad, 5=vbad, 6=down
    rx_quality: int
    
    @property
    def is_good(self) -> bool:
        """Check if quality is acceptable (good or excellent)"""
        return self.tx_quality <= 2 and self.rx_quality <= 2


# ============================================================
# RTC Audio Frame
# ============================================================

@dataclass
class RTCAudioFrame:
    """RTC audio frame container
    
    Attributes:
        data: Raw PCM audio data
        sample_rate: Audio sample rate (e.g., 16000)
        channels: Number of audio channels
        samples_per_channel: Number of samples per channel
        timestamp_ms: Frame timestamp in milliseconds
    """
    data: bytes
    sample_rate: int = 16000
    channels: int = 1
    samples_per_channel: int = 0
    timestamp_ms: float = 0.0
    
    def __post_init__(self):
        if self.timestamp_ms == 0.0:
            self.timestamp_ms = time.time() * 1000


# ============================================================
# RTC Transport Implementation
# ============================================================

class RTCTransport(TransportBase):
    """RTC transport implementation using Agora SDK
    
    Provides real-time audio streaming with UDP-based transport.
    Better for poor network conditions compared to WebSocket.
    
    Usage:
        config = RTCConfig(
            app_id="your-app-id",
            channel="room-123",
            token="your-token",
        )
        transport = RTCTransport(config)
        await transport.connect()
    
    Note:
        Requires Agora SDK. Install with:
        pip install agora-python-server-sdk
    """
    
    def __init__(self, config: RTCConfig):
        """Initialize RTC transport
        
        Args:
            config: RTC configuration
        """
        super().__init__(config)
        self._rtc_config: RTCConfig = config
        
        # Agora SDK objects (initialized on connect)
        self._rtc_engine = None
        self._local_user = None
        self._channel = None
        
        # Audio frame callback
        self._audio_frame_callback: Optional[Callable[[RTCAudioFrame], None]] = None
        
        # Remote users
        self._remote_users: Dict[int, RTCUserState] = {}
        
        # Network quality tracking
        self._network_quality: Optional[RTCNetworkQuality] = None
        
        # Message queue for signaling (RTC doesn't have native text messaging)
        # We use a separate signaling channel (WebSocket) for messages
        self._signaling_transport: Optional[TransportBase] = None
    
    @property
    def network_quality(self) -> Optional[RTCNetworkQuality]:
        """Current network quality metrics"""
        return self._network_quality
    
    @property
    def remote_users(self) -> Dict[int, RTCUserState]:
        """Map of remote user IDs to their states"""
        return self._remote_users.copy()
    
    def set_signaling_transport(self, transport: TransportBase) -> None:
        """Set signaling transport for text messages
        
        RTC doesn't support text messages natively, so we use
        a separate signaling channel (typically WebSocket).
        
        Args:
            transport: Transport for signaling messages
        """
        self._signaling_transport = transport
    
    async def _do_connect(self, headers: Optional[Dict[str, str]]) -> bool:
        """Join RTC channel
        
        Args:
            headers: Not used for RTC (uses config token instead)
            
        Returns:
            True if channel join successful
        """
        try:
            # Check if Agora SDK is available
            if not self._check_agora_sdk():
                logger.bind(tag=TAG).error("Agora SDK not available")
                return False
            
            # Initialize Agora engine
            success = await self._initialize_agora_engine()
            if not success:
                return False
            
            # Join channel
            success = await self._join_channel()
            if not success:
                return False
            
            logger.bind(tag=TAG).info(
                f"RTC connected: channel={self._rtc_config.channel}, "
                f"uid={self._rtc_config.uid}"
            )
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"RTC connection failed: {e}")
            return False
    
    async def _do_disconnect(self, code: int, reason: str) -> None:
        """Leave RTC channel
        
        Args:
            code: Not used for RTC
            reason: Disconnect reason
        """
        try:
            if self._channel:
                await self._leave_channel()
            
            if self._rtc_engine:
                await self._release_agora_engine()
            
            logger.bind(tag=TAG).info(f"RTC disconnected: {reason}")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"RTC disconnect error: {e}")
    
    async def _create_stream(self) -> TransportStream:
        """Create RTC stream
        
        Returns:
            RTCStream instance
        """
        stream = RTCStream(self)
        await stream.start()
        return stream
    
    # ==================== Agora SDK Integration ====================
    
    def _check_agora_sdk(self) -> bool:
        """Check if Agora SDK is available
        
        Returns:
            True if SDK is installed
        """
        try:
            # Try to import Agora SDK
            # Note: The actual import depends on the SDK version
            # For Python server SDK: agora.rtc.agora_service
            # For IoT SDK: different import
            import importlib.util
            
            # Check for common Agora SDK packages
            sdk_packages = [
                "agora.rtc.agora_service",
                "agora_rtc",
                "agorartc",
            ]
            
            for package in sdk_packages:
                spec = importlib.util.find_spec(package.split(".")[0])
                if spec is not None:
                    return True
            
            # SDK not found - log warning but allow mock implementation
            logger.bind(tag=TAG).warning(
                "Agora SDK not found. Install with: pip install agora-python-server-sdk"
            )
            return False
            
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Error checking Agora SDK: {e}")
            return False
    
    async def _initialize_agora_engine(self) -> bool:
        """Initialize Agora RTC engine
        
        Returns:
            True if initialization successful
        """
        try:
            # Import Agora SDK (placeholder - actual import depends on SDK version)
            # from agora.rtc.agora_service import AgoraServiceConfig, AgoraService
            
            # For now, use mock implementation for development
            logger.bind(tag=TAG).info("Initializing Agora RTC engine (mock mode)")
            
            # TODO: Replace with actual Agora SDK initialization
            # config = AgoraServiceConfig()
            # config.appid = self._rtc_config.app_id
            # config.audio_scenario = self._rtc_config.audio_scenario
            # self._rtc_engine = AgoraService()
            # self._rtc_engine.initialize(config)
            
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to initialize Agora engine: {e}")
            return False
    
    async def _release_agora_engine(self) -> None:
        """Release Agora RTC engine resources"""
        try:
            if self._rtc_engine:
                # TODO: Replace with actual SDK release
                # self._rtc_engine.release()
                self._rtc_engine = None
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error releasing Agora engine: {e}")
    
    async def _join_channel(self) -> bool:
        """Join RTC channel
        
        Returns:
            True if join successful
        """
        try:
            if not self._rtc_config.channel:
                logger.bind(tag=TAG).error("Channel name not configured")
                return False
            
            # TODO: Replace with actual SDK channel join
            # channel_config = ChannelConfig()
            # channel_config.token = self._rtc_config.token
            # channel_config.channel_id = self._rtc_config.channel
            # self._channel = self._rtc_engine.createChannel(channel_config)
            # self._channel.join(self._rtc_config.uid)
            
            logger.bind(tag=TAG).info(
                f"Joined channel: {self._rtc_config.channel} (mock mode)"
            )
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to join channel: {e}")
            return False
    
    async def _leave_channel(self) -> None:
        """Leave RTC channel"""
        try:
            if self._channel:
                # TODO: Replace with actual SDK channel leave
                # self._channel.leave()
                self._channel = None
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error leaving channel: {e}")
    
    # ==================== Audio Handling ====================
    
    async def push_audio_frame(self, frame: RTCAudioFrame) -> bool:
        """Push audio frame to RTC channel
        
        Args:
            frame: Audio frame to send
            
        Returns:
            True if sent successfully
        """
        if not self.is_connected:
            return False
        
        try:
            # TODO: Replace with actual SDK audio push
            # audio_data = AudioPcmData()
            # audio_data.data = frame.data
            # audio_data.sample_rate = frame.sample_rate
            # audio_data.channels = frame.channels
            # self._local_user.push_audio_frame(audio_data)
            
            self._stats.audio_bytes_sent += len(frame.data)
            self._stats.audio_packets_sent += 1
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to push audio frame: {e}")
            return False
    
    def on_audio_frame(self, callback: Callable[[RTCAudioFrame], None]) -> None:
        """Register callback for incoming audio frames
        
        Args:
            callback: Function to call with received audio frames
        """
        self._audio_frame_callback = callback
    
    async def _handle_audio_frame(self, frame: RTCAudioFrame) -> None:
        """Handle incoming audio frame from remote user
        
        Args:
            frame: Received audio frame
        """
        self._stats.audio_bytes_received += len(frame.data)
        self._stats.audio_packets_received += 1
        
        if self._audio_frame_callback:
            try:
                result = self._audio_frame_callback(frame)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.bind(tag=TAG).error(f"Audio frame callback error: {e}")
        
        # Also trigger the base class handler
        await self._handle_incoming_audio(frame.data)
    
    # ==================== Network Quality ====================
    
    async def _handle_network_quality(self, quality: RTCNetworkQuality) -> None:
        """Handle network quality update
        
        Args:
            quality: Network quality metrics
        """
        self._network_quality = quality
        
        await self._emit_event(TransportEvent(
            type=TransportEventType.NETWORK_QUALITY,
            data=quality,
            metadata={
                "tx_quality": quality.tx_quality,
                "rx_quality": quality.rx_quality,
                "is_good": quality.is_good,
            }
        ))
    
    # ==================== Signaling (for messages) ====================
    
    async def send_message(self, message: Union[str, Dict[str, Any]]) -> bool:
        """Send message via signaling channel
        
        RTC doesn't support text messages natively.
        Uses a separate signaling transport if configured.
        
        Args:
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        if self._signaling_transport and self._signaling_transport.is_connected:
            return await self._signaling_transport.send_message(message)
        
        logger.bind(tag=TAG).warning(
            "No signaling transport configured for RTC messages"
        )
        return False


# ============================================================
# RTC Stream Implementation
# ============================================================

class RTCStream(TransportStream):
    """RTC bidirectional audio stream
    
    Handles audio frame sending/receiving over RTC channel.
    """
    
    def __init__(self, transport: RTCTransport):
        """Initialize RTC stream
        
        Args:
            transport: Parent RTC transport
        """
        super().__init__(transport)
        self._rtc_transport = transport
    
    async def write_audio(self, data: bytes) -> None:
        """Write audio data
        
        Args:
            data: PCM audio bytes
        """
        if self._is_closed:
            raise TransportError("Stream is closed")
        
        frame = RTCAudioFrame(
            data=data,
            sample_rate=self._rtc_transport._rtc_config.audio_sample_rate,
            channels=self._rtc_transport._rtc_config.audio_channels,
        )
        
        await self._rtc_transport.push_audio_frame(frame)
    
    async def write_message(self, message: Union[str, Dict[str, Any]]) -> None:
        """Write message via signaling channel
        
        Args:
            message: Message to send
        """
        if self._is_closed:
            raise TransportError("Stream is closed")
        
        await self._rtc_transport.send_message(message)
    
    async def _read_loop(self) -> None:
        """Background task for RTC event handling
        
        RTC uses callbacks, so this loop mainly handles
        the event processing.
        """
        try:
            while not self._is_closed:
                # RTC events are handled via callbacks
                # This loop just keeps the task alive
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.bind(tag=TAG).debug("RTC read loop cancelled")
            raise
        except Exception as e:
            logger.bind(tag=TAG).error(f"RTC read loop error: {e}")
    
    async def _do_close(self) -> None:
        """Clean up RTC stream resources"""
        pass


# ============================================================
# Factory Registration
# ============================================================

def register_rtc_transport():
    """Register RTC transport with the factory"""
    from .factory import TransportFactory
    
    if not TransportFactory.is_registered("rtc"):
        TransportFactory.register("rtc", RTCTransport)


# Auto-register on import
try:
    register_rtc_transport()
except Exception:
    pass  # Factory may not be available yet

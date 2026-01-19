"""
Transport Layer Configuration

Defines configuration data classes for different transport types.
Uses dataclass for immutability and type safety.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class TransportType(Enum):
    """Supported transport types"""
    WEBSOCKET = "websocket"
    RTC = "rtc"  # WebRTC / Agora RTC


@dataclass(frozen=True)
class TransportConfig:
    """Base transport configuration
    
    Frozen dataclass ensures immutability after creation.
    Subclasses add transport-specific configuration.
    
    Attributes:
        transport_type: Type of transport (websocket/rtc)
        timeout_ms: Connection timeout in milliseconds
        reconnect_enabled: Whether to auto-reconnect on disconnect
        reconnect_max_attempts: Maximum reconnection attempts
        reconnect_delay_ms: Delay between reconnection attempts
    """
    transport_type: TransportType
    timeout_ms: int = 30000
    reconnect_enabled: bool = True
    reconnect_max_attempts: int = 3
    reconnect_delay_ms: int = 1000
    
    # Audio configuration
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_format: str = "opus"  # opus / pcm
    
    # Extra configuration (for extensibility)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WebSocketConfig(TransportConfig):
    """WebSocket-specific configuration
    
    Attributes:
        url: WebSocket server URL
        headers: HTTP headers for connection
        ping_interval: Ping interval in seconds
        ping_timeout: Ping timeout in seconds
        close_timeout: Close handshake timeout in seconds
        max_message_size: Maximum message size in bytes
    """
    transport_type: TransportType = TransportType.WEBSOCKET
    
    # WebSocket specific
    url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    ping_interval: int = 30
    ping_timeout: int = 20
    close_timeout: int = 10
    max_message_size: int = 10 * 1024 * 1024  # 10MB
    
    # TLS configuration
    ssl_verify: bool = True
    ssl_cert_path: Optional[str] = None


@dataclass(frozen=True)
class RTCConfig(TransportConfig):
    """RTC-specific configuration (Agora/WebRTC)
    
    Attributes:
        app_id: Agora App ID
        channel: RTC channel name
        token: RTC token for authentication
        uid: User ID in the channel
        enable_audio: Enable audio streaming
        enable_video: Enable video streaming (future)
        audio_profile: Audio quality profile
        audio_scenario: Audio scenario (e.g., chatroom)
    """
    transport_type: TransportType = TransportType.RTC
    
    # Agora specific
    app_id: Optional[str] = None
    channel: Optional[str] = None
    token: Optional[str] = None
    uid: int = 0
    
    # Audio/Video settings
    enable_audio: bool = True
    enable_video: bool = False
    
    # Audio profile (Agora specific)
    audio_profile: str = "speech_standard"  # speech_standard / music_standard
    audio_scenario: str = "chatroom"  # chatroom / game_streaming
    
    # Network quality settings
    enable_network_quality_monitoring: bool = True
    min_bitrate: int = 12000  # bps
    max_bitrate: int = 64000  # bps


def create_config(
    transport_type: str,
    **kwargs
) -> TransportConfig:
    """Factory function to create transport configuration
    
    Args:
        transport_type: Transport type string ("websocket" or "rtc")
        **kwargs: Configuration parameters
        
    Returns:
        TransportConfig subclass instance
        
    Raises:
        ValueError: If transport_type is not supported
    
    Example:
        >>> config = create_config("websocket", url="wss://api.example.com/ws")
        >>> config = create_config("rtc", app_id="xxx", channel="room1")
    """
    transport_type_enum = TransportType(transport_type.lower())
    
    if transport_type_enum == TransportType.WEBSOCKET:
        return WebSocketConfig(**kwargs)
    elif transport_type_enum == TransportType.RTC:
        return RTCConfig(**kwargs)
    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")

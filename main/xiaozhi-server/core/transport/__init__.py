"""
Transport Layer Abstraction for Live-Agent

This module provides a unified transport layer abstraction that supports
both WebSocket and RTC (WebRTC/Agora) transport mechanisms.

"""

from .base import TransportBase, TransportStream, TransportState, TransportStats
from .events import TransportEvent, TransportEventType
from .config import TransportConfig, WebSocketConfig, RTCConfig, TransportType, create_config
from .factory import TransportFactory

# Import implementations to trigger auto-registration
from .websocket import WebSocketTransport
from .rtc import RTCTransport, RTCAudioFrame, RTCNetworkQuality
from .adapter import TransportAdapter, TransportOptions, create_transport_adapter

__all__ = [
    # Base classes
    "TransportBase",
    "TransportStream",
    "TransportState",
    "TransportStats",
    # Events
    "TransportEvent",
    "TransportEventType",
    # Configuration
    "TransportConfig",
    "TransportType",
    "WebSocketConfig",
    "RTCConfig",
    "create_config",
    # Factory
    "TransportFactory",
    # Implementations
    "WebSocketTransport",
    "RTCTransport",
    "RTCAudioFrame",
    "RTCNetworkQuality",
    # Adapter
    "TransportAdapter",
    "TransportOptions",
    "create_transport_adapter",
]

"""
Transport Layer Events

Defines event types and event objects for transport layer communication.
Follows the Observer pattern for loose coupling between transport and handlers.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional
import time


class TransportEventType(Enum):
    """Transport event types
    
    Events are categorized into:
    - Connection lifecycle events
    - Audio events  
    - Message events
    - Error events
    """
    # Connection lifecycle
    CONNECTED = auto()
    DISCONNECTED = auto()
    RECONNECTING = auto()
    RECONNECTED = auto()
    
    # Audio events
    AUDIO_RECEIVED = auto()
    AUDIO_SENT = auto()
    AUDIO_ERROR = auto()
    
    # Message events (JSON/Text)
    MESSAGE_RECEIVED = auto()
    MESSAGE_SENT = auto()
    MESSAGE_ERROR = auto()
    
    # Error events
    CONNECTION_ERROR = auto()
    TRANSPORT_ERROR = auto()
    TIMEOUT_ERROR = auto()
    
    # Quality events (for RTC)
    QUALITY_CHANGED = auto()
    NETWORK_QUALITY = auto()


@dataclass
class TransportEvent:
    """Transport event object
    
    Immutable event object carrying event data.
    Uses dataclass for clean initialization and comparison.
    
    Attributes:
        type: Event type enum
        timestamp_ms: Event timestamp in milliseconds
        data: Optional event payload (audio bytes, message dict, etc.)
        error: Optional error information
        metadata: Additional metadata (session_id, device_id, etc.)
    
    Example:
        >>> event = TransportEvent(
        ...     type=TransportEventType.AUDIO_RECEIVED,
        ...     data=b"\\x00\\x01\\x02",
        ...     metadata={"session_id": "abc123"}
        ... )
    """
    type: TransportEventType
    timestamp_ms: float = field(default_factory=lambda: time.time() * 1000)
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error event"""
        return self.type in (
            TransportEventType.CONNECTION_ERROR,
            TransportEventType.TRANSPORT_ERROR,
            TransportEventType.TIMEOUT_ERROR,
            TransportEventType.AUDIO_ERROR,
            TransportEventType.MESSAGE_ERROR,
        )
    
    @property
    def is_audio(self) -> bool:
        """Check if this is an audio event"""
        return self.type in (
            TransportEventType.AUDIO_RECEIVED,
            TransportEventType.AUDIO_SENT,
            TransportEventType.AUDIO_ERROR,
        )
    
    @property
    def is_message(self) -> bool:
        """Check if this is a message event"""
        return self.type in (
            TransportEventType.MESSAGE_RECEIVED,
            TransportEventType.MESSAGE_SENT,
            TransportEventType.MESSAGE_ERROR,
        )
    
    @property
    def is_connection(self) -> bool:
        """Check if this is a connection lifecycle event"""
        return self.type in (
            TransportEventType.CONNECTED,
            TransportEventType.DISCONNECTED,
            TransportEventType.RECONNECTING,
            TransportEventType.RECONNECTED,
        )


# Type alias for event callback
EventCallback = type[lambda event: None]

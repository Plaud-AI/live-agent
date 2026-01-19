"""
Transport Layer Base Classes

Defines abstract base classes for transport layer implementation.
Follows SOLID principles for clean architecture.

Design:
- TransportBase: Manages transport lifecycle and event routing
- TransportStream: Handles bidirectional audio/message streaming

"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Union,
)
import time

from config.logger import setup_logging
from .config import TransportConfig
from .events import TransportEvent, TransportEventType

if TYPE_CHECKING:
    pass

TAG = __name__
logger = setup_logging()


class TransportState(Enum):
    """Transport connection state machine
    
    State transitions:
        DISCONNECTED -> CONNECTING -> CONNECTED
        CONNECTED -> DISCONNECTING -> DISCONNECTED
        CONNECTED -> RECONNECTING -> CONNECTED
        Any state -> ERROR (terminal or recoverable)
    """
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    DISCONNECTING = auto()
    RECONNECTING = auto()
    ERROR = auto()


# Type aliases for callbacks
AudioCallback = Callable[[bytes], None]
MessageCallback = Callable[[Union[str, Dict[str, Any]]], None]
EventCallback = Callable[[TransportEvent], None]


class TransportBase(ABC):
    """Abstract base class for transport implementations
    
    Manages the transport lifecycle and provides event-driven communication.
    Subclasses implement protocol-specific logic (WebSocket, RTC, etc.).
    
    Responsibilities:
    - Connection lifecycle management (connect/disconnect/reconnect)
    - Event callback registration and dispatch
    - State machine management
    - Error handling and recovery
    
    Usage:
        class WebSocketTransport(TransportBase):
            async def _do_connect(self) -> bool:
                # Implementation
                
        transport = WebSocketTransport(config)
        transport.on_audio(handle_audio)
        transport.on_message(handle_message)
        await transport.connect()
    
    Thread Safety:
        This class is designed for asyncio single-threaded concurrency.
        External synchronization needed for multi-threaded access.
    """
    
    def __init__(self, config: TransportConfig):
        """Initialize transport with configuration
        
        Args:
            config: Transport configuration (immutable)
        """
        self._config = config
        self._state = TransportState.DISCONNECTED
        self._stream: Optional[TransportStream] = None
        
        # Event callbacks (multiple callbacks per event type)
        self._event_callbacks: Dict[TransportEventType, List[EventCallback]] = {}
        self._audio_callbacks: List[AudioCallback] = []
        self._message_callbacks: List[MessageCallback] = []
        
        # Connection metadata
        self._session_id: Optional[str] = None
        self._device_id: Optional[str] = None
        self._connect_time: Optional[float] = None
        
        # Reconnection state
        self._reconnect_attempts = 0
        self._reconnect_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = TransportStats()
    
    @property
    def state(self) -> TransportState:
        """Current transport state (read-only)"""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Check if transport is connected"""
        return self._state == TransportState.CONNECTED
    
    @property
    def config(self) -> TransportConfig:
        """Transport configuration (read-only)"""
        return self._config
    
    @property
    def session_id(self) -> Optional[str]:
        """Current session ID"""
        return self._session_id
    
    @property
    def stats(self) -> "TransportStats":
        """Transport statistics"""
        return self._stats
    
    # ==================== Event Registration ====================
    
    def on_event(self, event_type: TransportEventType, callback: EventCallback) -> None:
        """Register callback for specific event type
        
        Args:
            event_type: Event type to listen for
            callback: Callback function (async or sync)
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback)
    
    def on_audio(self, callback: AudioCallback) -> None:
        """Register callback for incoming audio data
        
        Args:
            callback: Function called with audio bytes
        """
        self._audio_callbacks.append(callback)
    
    def on_message(self, callback: MessageCallback) -> None:
        """Register callback for incoming messages
        
        Args:
            callback: Function called with message data
        """
        self._message_callbacks.append(callback)
    
    def off_event(self, event_type: TransportEventType, callback: EventCallback) -> bool:
        """Unregister event callback
        
        Args:
            event_type: Event type
            callback: Callback to remove
            
        Returns:
            True if callback was removed, False if not found
        """
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
                return True
            except ValueError:
                pass
        return False
    
    # ==================== Lifecycle Management ====================
    
    async def connect(
        self,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Connect to the remote endpoint
        
        Args:
            session_id: Optional session identifier
            device_id: Optional device identifier
            headers: Optional connection headers
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            TransportError: On unrecoverable connection error
        """
        if self._state == TransportState.CONNECTED:
            logger.bind(tag=TAG).warning("Already connected, ignoring connect request")
            return True
        
        if self._state == TransportState.CONNECTING:
            logger.bind(tag=TAG).warning("Connection in progress, ignoring")
            return False
        
        self._session_id = session_id
        self._device_id = device_id
        self._state = TransportState.CONNECTING
        
        try:
            success = await self._do_connect(headers)
            
            if success:
                self._state = TransportState.CONNECTED
                self._connect_time = time.time() * 1000
                self._reconnect_attempts = 0
                self._stats.connections += 1
                
                # Create stream for bidirectional communication
                self._stream = await self._create_stream()
                
                # Emit connected event
                await self._emit_event(TransportEvent(
                    type=TransportEventType.CONNECTED,
                    metadata={
                        "session_id": session_id,
                        "device_id": device_id,
                    }
                ))
                
                logger.bind(tag=TAG).info(
                    f"Transport connected: session={session_id}, device={device_id}"
                )
                return True
            else:
                self._state = TransportState.DISCONNECTED
                await self._emit_event(TransportEvent(
                    type=TransportEventType.CONNECTION_ERROR,
                    error="Connection failed",
                ))
                return False
                
        except Exception as e:
            self._state = TransportState.ERROR
            self._stats.errors += 1
            await self._emit_event(TransportEvent(
                type=TransportEventType.CONNECTION_ERROR,
                error=str(e),
            ))
            logger.bind(tag=TAG).error(f"Connection error: {e}")
            raise
    
    async def disconnect(self, code: int = 1000, reason: str = "Normal closure") -> None:
        """Disconnect from the remote endpoint
        
        Args:
            code: Close code (WebSocket-style, default 1000 = normal)
            reason: Close reason string
        """
        if self._state in (TransportState.DISCONNECTED, TransportState.DISCONNECTING):
            return
        
        self._state = TransportState.DISCONNECTING
        
        try:
            # Cancel any pending reconnection
            if self._reconnect_task and not self._reconnect_task.done():
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass
            
            # Close the stream
            if self._stream:
                await self._stream.close()
                self._stream = None
            
            # Perform transport-specific disconnect
            await self._do_disconnect(code, reason)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error during disconnect: {e}")
        finally:
            self._state = TransportState.DISCONNECTED
            await self._emit_event(TransportEvent(
                type=TransportEventType.DISCONNECTED,
                metadata={"code": code, "reason": reason},
            ))
            logger.bind(tag=TAG).info(f"Transport disconnected: code={code}, reason={reason}")
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect
        
        Returns:
            True if reconnection successful
        """
        if not self._config.reconnect_enabled:
            logger.bind(tag=TAG).warning("Reconnection disabled")
            return False
        
        if self._reconnect_attempts >= self._config.reconnect_max_attempts:
            logger.bind(tag=TAG).error(
                f"Max reconnection attempts ({self._config.reconnect_max_attempts}) reached"
            )
            return False
        
        self._state = TransportState.RECONNECTING
        self._reconnect_attempts += 1
        
        await self._emit_event(TransportEvent(
            type=TransportEventType.RECONNECTING,
            metadata={"attempt": self._reconnect_attempts},
        ))
        
        # Wait before reconnecting
        await asyncio.sleep(self._config.reconnect_delay_ms / 1000)
        
        try:
            success = await self._do_connect(None)
            
            if success:
                self._state = TransportState.CONNECTED
                self._stream = await self._create_stream()
                self._stats.reconnections += 1
                
                await self._emit_event(TransportEvent(
                    type=TransportEventType.RECONNECTED,
                    metadata={"attempts": self._reconnect_attempts},
                ))
                
                self._reconnect_attempts = 0
                logger.bind(tag=TAG).info("Reconnection successful")
                return True
            else:
                # Retry
                return await self.reconnect()
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Reconnection error: {e}")
            return await self.reconnect()
    
    # ==================== Data Transmission ====================
    
    async def send_audio(self, data: bytes) -> bool:
        """Send audio data to remote
        
        Args:
            data: Audio bytes (opus or pcm depending on config)
            
        Returns:
            True if sent successfully
        """
        if not self.is_connected or not self._stream:
            logger.bind(tag=TAG).warning("Cannot send audio: not connected")
            return False
        
        try:
            await self._stream.write_audio(data)
            self._stats.audio_bytes_sent += len(data)
            self._stats.audio_packets_sent += 1
            return True
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to send audio: {e}")
            await self._emit_event(TransportEvent(
                type=TransportEventType.AUDIO_ERROR,
                error=str(e),
            ))
            return False
    
    async def send_message(self, message: Union[str, Dict[str, Any]]) -> bool:
        """Send message to remote
        
        Args:
            message: Text message or JSON-serializable dict
            
        Returns:
            True if sent successfully
        """
        if not self.is_connected or not self._stream:
            logger.bind(tag=TAG).warning("Cannot send message: not connected")
            return False
        
        try:
            await self._stream.write_message(message)
            self._stats.messages_sent += 1
            return True
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to send message: {e}")
            await self._emit_event(TransportEvent(
                type=TransportEventType.MESSAGE_ERROR,
                error=str(e),
            ))
            return False
    
    # ==================== Abstract Methods ====================
    
    @abstractmethod
    async def _do_connect(self, headers: Optional[Dict[str, str]]) -> bool:
        """Perform transport-specific connection
        
        Args:
            headers: Optional connection headers
            
        Returns:
            True if connection successful
        """
        ...
    
    @abstractmethod
    async def _do_disconnect(self, code: int, reason: str) -> None:
        """Perform transport-specific disconnection
        
        Args:
            code: Close code
            reason: Close reason
        """
        ...
    
    @abstractmethod
    async def _create_stream(self) -> "TransportStream":
        """Create transport stream for bidirectional communication
        
        Returns:
            TransportStream instance
        """
        ...
    
    # ==================== Internal Methods ====================
    
    async def _emit_event(self, event: TransportEvent) -> None:
        """Dispatch event to registered callbacks
        
        Args:
            event: Event to dispatch
        """
        # Dispatch to type-specific callbacks
        if event.type in self._event_callbacks:
            for callback in self._event_callbacks[event.type]:
                try:
                    result = callback(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Event callback error: {e}")
        
        # Dispatch audio events
        if event.type == TransportEventType.AUDIO_RECEIVED and event.data:
            for callback in self._audio_callbacks:
                try:
                    result = callback(event.data)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Audio callback error: {e}")
        
        # Dispatch message events
        if event.type == TransportEventType.MESSAGE_RECEIVED and event.data:
            for callback in self._message_callbacks:
                try:
                    result = callback(event.data)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Message callback error: {e}")
    
    async def _handle_incoming_audio(self, data: bytes) -> None:
        """Handle incoming audio data from stream
        
        Args:
            data: Audio bytes
        """
        self._stats.audio_bytes_received += len(data)
        self._stats.audio_packets_received += 1
        
        await self._emit_event(TransportEvent(
            type=TransportEventType.AUDIO_RECEIVED,
            data=data,
        ))
    
    async def _handle_incoming_message(self, message: Union[str, Dict[str, Any]]) -> None:
        """Handle incoming message from stream
        
        Args:
            message: Text or JSON message
        """
        self._stats.messages_received += 1
        
        await self._emit_event(TransportEvent(
            type=TransportEventType.MESSAGE_RECEIVED,
            data=message,
        ))


class TransportStream(ABC):
    """Abstract bidirectional stream for transport communication
    
    Handles the actual reading and writing of data over the transport.
    Each transport implementation provides its own stream implementation.
    
    Responsibilities:
    - Bidirectional audio streaming
    - Message (JSON/text) transmission
    - Stream lifecycle management
    """
    
    def __init__(self, transport: TransportBase):
        """Initialize stream with parent transport
        
        Args:
            transport: Parent transport instance
        """
        self._transport = transport
        self._is_closed = False
        self._read_task: Optional[asyncio.Task] = None
    
    @property
    def is_closed(self) -> bool:
        """Check if stream is closed"""
        return self._is_closed
    
    async def start(self) -> None:
        """Start the stream read loop
        
        Must be called after transport connection is established.
        Starts background task for reading incoming data.
        """
        if self._read_task is not None:
            logger.bind(tag=TAG).warning("Stream already started")
            return
        
        self._read_task = asyncio.create_task(self._read_loop())
        logger.bind(tag=TAG).debug("Transport stream started")
    
    async def close(self) -> None:
        """Close the stream
        
        Cancels read task and performs cleanup.
        """
        if self._is_closed:
            return
        
        self._is_closed = True
        
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        await self._do_close()
        logger.bind(tag=TAG).debug("Transport stream closed")
    
    @abstractmethod
    async def write_audio(self, data: bytes) -> None:
        """Write audio data to stream
        
        Args:
            data: Audio bytes to send
        """
        ...
    
    @abstractmethod
    async def write_message(self, message: Union[str, Dict[str, Any]]) -> None:
        """Write message to stream
        
        Args:
            message: Text or JSON message
        """
        ...
    
    @abstractmethod
    async def _read_loop(self) -> None:
        """Background task for reading incoming data
        
        Should call:
        - self._transport._handle_incoming_audio() for audio
        - self._transport._handle_incoming_message() for messages
        """
        ...
    
    @abstractmethod
    async def _do_close(self) -> None:
        """Perform stream-specific cleanup"""
        ...


@dataclass
class TransportStats:
    """Transport statistics for monitoring
    
    Tracks connection, audio, and message statistics.
    Thread-safe counters using simple increments.
    """
    # Connection stats
    connections: int = 0
    reconnections: int = 0
    errors: int = 0
    
    # Audio stats
    audio_bytes_sent: int = 0
    audio_bytes_received: int = 0
    audio_packets_sent: int = 0
    audio_packets_received: int = 0
    
    # Message stats
    messages_sent: int = 0
    messages_received: int = 0
    
    def reset(self) -> None:
        """Reset all statistics"""
        self.connections = 0
        self.reconnections = 0
        self.errors = 0
        self.audio_bytes_sent = 0
        self.audio_bytes_received = 0
        self.audio_packets_sent = 0
        self.audio_packets_received = 0
        self.messages_sent = 0
        self.messages_received = 0
    
    def to_dict(self) -> Dict[str, int]:
        """Convert stats to dictionary"""
        return {
            "connections": self.connections,
            "reconnections": self.reconnections,
            "errors": self.errors,
            "audio_bytes_sent": self.audio_bytes_sent,
            "audio_bytes_received": self.audio_bytes_received,
            "audio_packets_sent": self.audio_packets_sent,
            "audio_packets_received": self.audio_packets_received,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
        }


class TransportError(Exception):
    """Base exception for transport errors"""
    pass


class ConnectionError(TransportError):
    """Connection-related errors"""
    pass


class StreamError(TransportError):
    """Stream-related errors"""
    pass

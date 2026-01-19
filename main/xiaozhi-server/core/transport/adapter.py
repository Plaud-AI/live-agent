"""
Transport Adapter for ConnectionHandler Integration

Provides adapter classes to bridge the new transport layer with
the existing ConnectionHandler implementation.

This allows gradual migration from direct WebSocket usage to
the abstracted transport layer.

Design Pattern: Adapter
- TransportAdapter wraps TransportBase for ConnectionHandler
- Maintains backward compatibility with existing code
- Enables A/B testing between WebSocket and RTC
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Union
from dataclasses import dataclass

from config.logger import setup_logging
from .base import TransportBase, TransportState
from .websocket import WebSocketTransport
from .rtc import RTCTransport
from .config import WebSocketConfig, RTCConfig, TransportType
from .events import TransportEvent, TransportEventType

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
    from websockets.server import WebSocketServerProtocol

TAG = __name__
logger = setup_logging()


@dataclass
class TransportOptions:
    """Options for transport adapter creation"""
    # Primary transport type
    transport_type: str = "websocket"  # "websocket" or "rtc"
    
    # WebSocket options
    ws_ping_interval: int = 30
    ws_ping_timeout: int = 20
    ws_close_timeout: int = 10
    
    # RTC options
    rtc_app_id: Optional[str] = None
    rtc_channel: Optional[str] = None
    rtc_token: Optional[str] = None
    rtc_uid: int = 0
    
    # Feature flags
    enable_reconnect: bool = True
    reconnect_max_attempts: int = 3
    
    # Audio format
    audio_format: str = "opus"


class TransportAdapter:
    """Adapter for integrating transport layer with ConnectionHandler
    
    Wraps TransportBase and provides a compatible interface for
    the existing ConnectionHandler implementation.
    
    Usage:
        # Server mode (accepting incoming WebSocket)
        adapter = TransportAdapter.from_websocket(
            websocket, 
            session_id="xxx", 
            device_id="xxx"
        )
        
        # Client mode
        adapter = TransportAdapter(options)
        await adapter.connect(url="wss://...", headers={...})
    
    Attributes:
        _transport: Underlying transport instance
        _conn: Reference to ConnectionHandler (set after binding)
    """
    
    def __init__(
        self,
        options: Optional[TransportOptions] = None,
        transport: Optional[TransportBase] = None,
    ):
        """Initialize transport adapter
        
        Args:
            options: Transport options (for creating new transport)
            transport: Existing transport instance (for wrapping)
        """
        self._options = options or TransportOptions()
        self._transport = transport
        self._conn: Optional["ConnectionHandler"] = None
        
        # Callback references for cleanup
        self._registered_callbacks = []
    
    @classmethod
    def from_websocket(
        cls,
        websocket: "WebSocketServerProtocol",
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        options: Optional[TransportOptions] = None,
    ) -> "TransportAdapter":
        """Create adapter from existing WebSocket connection
        
        Used in server mode when accepting incoming connections.
        
        Args:
            websocket: Incoming WebSocket connection
            session_id: Session identifier
            device_id: Device identifier
            options: Optional transport options
            
        Returns:
            Initialized TransportAdapter
        """
        opts = options or TransportOptions()
        
        # Create WebSocket config
        config = WebSocketConfig(
            ping_interval=opts.ws_ping_interval,
            ping_timeout=opts.ws_ping_timeout,
            close_timeout=opts.ws_close_timeout,
            reconnect_enabled=opts.enable_reconnect,
            reconnect_max_attempts=opts.reconnect_max_attempts,
            audio_format=opts.audio_format,
        )
        
        # Wrap the existing WebSocket
        transport = WebSocketTransport.from_websocket(
            websocket,
            config,
            session_id=session_id,
            device_id=device_id,
        )
        
        return cls(options=opts, transport=transport)
    
    @classmethod
    def from_rtc(
        cls,
        app_id: str,
        channel: str,
        token: Optional[str] = None,
        uid: int = 0,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        options: Optional[TransportOptions] = None,
    ) -> "TransportAdapter":
        """Create adapter for RTC transport
        
        Args:
            app_id: Agora App ID
            channel: RTC channel name
            token: Optional RTC token
            uid: User ID
            session_id: Session identifier
            device_id: Device identifier
            options: Optional transport options
            
        Returns:
            TransportAdapter configured for RTC
        """
        opts = options or TransportOptions(transport_type="rtc")
        
        config = RTCConfig(
            app_id=app_id,
            channel=channel,
            token=token,
            uid=uid,
            reconnect_enabled=opts.enable_reconnect,
            reconnect_max_attempts=opts.reconnect_max_attempts,
            audio_format=opts.audio_format,
        )
        
        transport = RTCTransport(config)
        transport._session_id = session_id
        transport._device_id = device_id
        
        return cls(options=opts, transport=transport)
    
    @property
    def transport(self) -> Optional[TransportBase]:
        """Get underlying transport"""
        return self._transport
    
    @property
    def is_connected(self) -> bool:
        """Check if transport is connected"""
        return self._transport is not None and self._transport.is_connected
    
    @property
    def transport_type(self) -> str:
        """Get transport type string"""
        if self._transport is None:
            return self._options.transport_type
        return self._transport.config.transport_type.value
    
    @property
    def session_id(self) -> Optional[str]:
        """Get session ID"""
        if self._transport:
            return self._transport.session_id
        return None
    
    def bind_connection(self, conn: "ConnectionHandler") -> None:
        """Bind adapter to ConnectionHandler
        
        Sets up event routing from transport to connection handler.
        
        Args:
            conn: ConnectionHandler to bind
        """
        self._conn = conn
        
        if self._transport is None:
            return
        
        # Route audio events
        def on_audio(data: bytes):
            if self._conn:
                # Queue audio for processing
                self._conn.asr_audio_queue.put(data)
        
        self._transport.on_audio(on_audio)
        self._registered_callbacks.append(("audio", on_audio))
        
        # Route message events
        async def on_message(msg):
            if self._conn:
                # Handle incoming JSON message
                from core.handle.textHandle import handleTextMessage
                if isinstance(msg, dict):
                    await handleTextMessage(self._conn, json.dumps(msg))
                else:
                    await handleTextMessage(self._conn, str(msg))
        
        self._transport.on_message(on_message)
        self._registered_callbacks.append(("message", on_message))
        
        # Route disconnect events
        def on_disconnect(event: TransportEvent):
            if self._conn:
                logger.bind(tag=TAG).info(
                    f"Transport disconnected: {event.metadata}"
                )
                # Trigger connection cleanup
                asyncio.create_task(self._conn.close())
        
        self._transport.on_event(TransportEventType.DISCONNECTED, on_disconnect)
        self._registered_callbacks.append((TransportEventType.DISCONNECTED, on_disconnect))
        
        logger.bind(tag=TAG).info("Transport adapter bound to ConnectionHandler")
    
    async def initialize(self) -> None:
        """Initialize transport stream (for server mode)
        
        Must be called after from_websocket() to start the stream.
        """
        if isinstance(self._transport, WebSocketTransport):
            await self._transport.initialize_from_websocket()
    
    async def connect(
        self,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> bool:
        """Connect transport (client mode)
        
        Args:
            url: WebSocket URL (for WebSocket transport)
            headers: Connection headers
            session_id: Session identifier
            device_id: Device identifier
            
        Returns:
            True if connection successful
        """
        if self._transport is None:
            # Create transport based on options
            if self._options.transport_type == "websocket":
                config = WebSocketConfig(
                    url=url,
                    headers=headers or {},
                    ping_interval=self._options.ws_ping_interval,
                    ping_timeout=self._options.ws_ping_timeout,
                    close_timeout=self._options.ws_close_timeout,
                    reconnect_enabled=self._options.enable_reconnect,
                    audio_format=self._options.audio_format,
                )
                self._transport = WebSocketTransport(config)
            elif self._options.transport_type == "rtc":
                config = RTCConfig(
                    app_id=self._options.rtc_app_id,
                    channel=self._options.rtc_channel,
                    token=self._options.rtc_token,
                    uid=self._options.rtc_uid,
                    reconnect_enabled=self._options.enable_reconnect,
                    audio_format=self._options.audio_format,
                )
                self._transport = RTCTransport(config)
            else:
                raise ValueError(f"Unknown transport type: {self._options.transport_type}")
        
        return await self._transport.connect(
            session_id=session_id,
            device_id=device_id,
            headers=headers,
        )
    
    async def disconnect(self, code: int = 1000, reason: str = "Normal closure") -> None:
        """Disconnect transport
        
        Args:
            code: Close code
            reason: Close reason
        """
        if self._transport:
            await self._transport.disconnect(code, reason)
    
    async def send_audio(self, data: bytes) -> bool:
        """Send audio data
        
        Args:
            data: Audio bytes
            
        Returns:
            True if sent successfully
        """
        if self._transport:
            return await self._transport.send_audio(data)
        return False
    
    async def send_message(self, message: Union[str, Dict[str, Any]]) -> bool:
        """Send message
        
        Args:
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        if self._transport:
            return await self._transport.send_message(message)
        return False
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON message (convenience method)
        
        Args:
            data: JSON-serializable dict
            
        Returns:
            True if sent successfully
        """
        return await self.send_message(data)
    
    async def close(self) -> None:
        """Close adapter and cleanup resources"""
        # Cleanup callbacks
        self._registered_callbacks.clear()
        
        # Disconnect transport
        if self._transport:
            await self._transport.disconnect()
            self._transport = None
        
        self._conn = None


def create_transport_adapter(
    transport_type: str = "websocket",
    **kwargs
) -> TransportAdapter:
    """Factory function to create transport adapter
    
    Args:
        transport_type: Type of transport ("websocket" or "rtc")
        **kwargs: Transport-specific options
        
    Returns:
        Configured TransportAdapter
        
    Example:
        # WebSocket adapter
        adapter = create_transport_adapter("websocket")
        
        # RTC adapter
        adapter = create_transport_adapter(
            "rtc",
            rtc_app_id="xxx",
            rtc_channel="room1"
        )
    """
    options = TransportOptions(transport_type=transport_type, **kwargs)
    return TransportAdapter(options=options)

"""
WebSocket Transport Implementation

Implements TransportBase for WebSocket protocol.
Supports bidirectional audio and message streaming over WebSocket.

Features:
- Full-duplex communication
- Automatic ping/pong keepalive
- Reconnection with exponential backoff
- Binary (audio) and text (JSON) message support
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import websockets
from websockets.exceptions import ConnectionClosed, InvalidMessage

from config.logger import setup_logging
from .base import TransportBase, TransportStream, TransportState, TransportError
from .config import WebSocketConfig
from .events import TransportEvent, TransportEventType

if TYPE_CHECKING:
    from websockets.client import WebSocketClientProtocol
    from websockets.server import WebSocketServerProtocol

TAG = __name__
logger = setup_logging()


class WebSocketTransport(TransportBase):
    """WebSocket transport implementation
    
    Provides bidirectional streaming over WebSocket protocol.
    Supports both client and server modes.
    
    Client Mode:
        transport = WebSocketTransport(config)
        await transport.connect()
        
    Server Mode (accepting incoming connection):
        transport = WebSocketTransport.from_websocket(ws, config)
    
    Attributes:
        _ws: Underlying WebSocket connection
        _config: WebSocket-specific configuration
    """
    
    def __init__(self, config: WebSocketConfig):
        """Initialize WebSocket transport
        
        Args:
            config: WebSocket configuration
        """
        super().__init__(config)
        self._ws_config: WebSocketConfig = config
        self._ws: Optional[Union[WebSocketClientProtocol, WebSocketServerProtocol]] = None
        self._headers: Optional[Dict[str, str]] = None
    
    @classmethod
    def from_websocket(
        cls,
        websocket: Union["WebSocketClientProtocol", "WebSocketServerProtocol"],
        config: Optional[WebSocketConfig] = None,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> "WebSocketTransport":
        """Create transport from existing WebSocket connection
        
        Used in server mode when accepting incoming connections.
        
        Args:
            websocket: Existing WebSocket connection
            config: Optional configuration (uses defaults if not provided)
            session_id: Session identifier
            device_id: Device identifier
            
        Returns:
            Initialized WebSocketTransport in CONNECTED state
        """
        if config is None:
            config = WebSocketConfig()
        
        transport = cls(config)
        transport._ws = websocket
        transport._session_id = session_id
        transport._device_id = device_id
        transport._state = TransportState.CONNECTED
        
        return transport
    
    async def initialize_from_websocket(self) -> None:
        """Initialize stream for server-mode transport
        
        Must be called after from_websocket() to start the stream.
        """
        if self._ws is None:
            raise TransportError("WebSocket not set")
        
        self._stream = await self._create_stream()
        self._stats.connections += 1
        
        await self._emit_event(TransportEvent(
            type=TransportEventType.CONNECTED,
            metadata={
                "session_id": self._session_id,
                "device_id": self._device_id,
            }
        ))
    
    @property
    def websocket(self) -> Optional[Union["WebSocketClientProtocol", "WebSocketServerProtocol"]]:
        """Get underlying WebSocket connection"""
        return self._ws
    
    async def _do_connect(self, headers: Optional[Dict[str, str]]) -> bool:
        """Establish WebSocket connection
        
        Args:
            headers: HTTP headers for connection
            
        Returns:
            True if connection successful
        """
        if not self._ws_config.url:
            logger.bind(tag=TAG).error("WebSocket URL not configured")
            return False
        
        # Merge config headers with provided headers
        all_headers = dict(self._ws_config.headers)
        if headers:
            all_headers.update(headers)
        
        self._headers = all_headers
        
        try:
            self._ws = await websockets.connect(
                self._ws_config.url,
                additional_headers=all_headers,
                ping_interval=self._ws_config.ping_interval,
                ping_timeout=self._ws_config.ping_timeout,
                close_timeout=self._ws_config.close_timeout,
                max_size=self._ws_config.max_message_size,
            )
            
            logger.bind(tag=TAG).info(f"WebSocket connected: {self._ws_config.url}")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"WebSocket connection failed: {e}")
            return False
    
    async def _do_disconnect(self, code: int, reason: str) -> None:
        """Close WebSocket connection
        
        Args:
            code: WebSocket close code
            reason: Close reason
        """
        if self._ws is None:
            return
        
        try:
            # Check if already closed
            is_closed = False
            if hasattr(self._ws, "closed"):
                is_closed = self._ws.closed
            elif hasattr(self._ws, "state"):
                is_closed = self._ws.state.name == "CLOSED"
            
            if not is_closed:
                await self._ws.close(code=code, reason=reason)
                logger.bind(tag=TAG).info(f"WebSocket closed: code={code}")
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Error closing WebSocket: {e}")
        finally:
            self._ws = None
    
    async def _create_stream(self) -> TransportStream:
        """Create WebSocket stream
        
        Returns:
            WebSocketStream instance
        """
        if self._ws is None:
            raise TransportError("WebSocket not connected")
        
        stream = WebSocketStream(self, self._ws)
        await stream.start()
        return stream
    
    async def send_raw(self, data: Union[str, bytes]) -> bool:
        """Send raw data over WebSocket
        
        Low-level method for sending data directly.
        Prefer send_audio() and send_message() for typed data.
        
        Args:
            data: Raw data to send
            
        Returns:
            True if sent successfully
        """
        if not self.is_connected or self._ws is None:
            return False
        
        try:
            await self._ws.send(data)
            return True
        except Exception as e:
            logger.bind(tag=TAG).error(f"WebSocket send error: {e}")
            return False


class WebSocketStream(TransportStream):
    """WebSocket bidirectional stream
    
    Handles reading and writing over WebSocket connection.
    Supports both binary (audio) and text (JSON) messages.
    """
    
    def __init__(
        self,
        transport: WebSocketTransport,
        websocket: Union["WebSocketClientProtocol", "WebSocketServerProtocol"],
    ):
        """Initialize WebSocket stream
        
        Args:
            transport: Parent transport
            websocket: WebSocket connection
        """
        super().__init__(transport)
        self._ws = websocket
        self._ws_transport = transport
    
    async def write_audio(self, data: bytes) -> None:
        """Write audio data (binary)
        
        Args:
            data: Audio bytes
        """
        if self._is_closed or self._ws is None:
            raise TransportError("Stream is closed")
        
        await self._ws.send(data)
    
    async def write_message(self, message: Union[str, Dict[str, Any]]) -> None:
        """Write message (text/JSON)
        
        Args:
            message: Text or JSON-serializable dict
        """
        if self._is_closed or self._ws is None:
            raise TransportError("Stream is closed")
        
        if isinstance(message, dict):
            await self._ws.send(json.dumps(message))
        else:
            await self._ws.send(message)
    
    async def _read_loop(self) -> None:
        """Background task for reading incoming data
        
        Reads from WebSocket and dispatches to appropriate handlers.
        """
        try:
            async for message in self._ws:
                if self._is_closed:
                    break
                
                if isinstance(message, bytes):
                    # Binary message = audio data
                    await self._transport._handle_incoming_audio(message)
                elif isinstance(message, str):
                    # Text message = JSON or plain text
                    try:
                        json_msg = json.loads(message)
                        await self._transport._handle_incoming_message(json_msg)
                    except json.JSONDecodeError:
                        # Plain text message
                        await self._transport._handle_incoming_message(message)
                        
        except ConnectionClosed as cc:
            logger.bind(tag=TAG).info(
                f"WebSocket connection closed: code={cc.code}, reason={cc.reason}"
            )
            # Emit disconnect event
            await self._transport._emit_event(TransportEvent(
                type=TransportEventType.DISCONNECTED,
                metadata={"code": cc.code, "reason": cc.reason},
            ))
            
            # Attempt reconnection if enabled
            if (
                self._transport._config.reconnect_enabled
                and self._transport._state != TransportState.DISCONNECTING
            ):
                asyncio.create_task(self._transport.reconnect())
                
        except asyncio.CancelledError:
            logger.bind(tag=TAG).debug("WebSocket read loop cancelled")
            raise
        except Exception as e:
            logger.bind(tag=TAG).error(f"WebSocket read error: {e}")
            await self._transport._emit_event(TransportEvent(
                type=TransportEventType.TRANSPORT_ERROR,
                error=str(e),
            ))
    
    async def _do_close(self) -> None:
        """Clean up stream resources"""
        self._ws = None


# Register WebSocket transport with factory
def register_websocket_transport():
    """Register WebSocket transport with the factory"""
    from .factory import TransportFactory
    
    if not TransportFactory.is_registered("websocket"):
        TransportFactory.register("websocket", WebSocketTransport)


# Auto-register on import
try:
    register_websocket_transport()
except Exception:
    pass  # Factory may not be available yet

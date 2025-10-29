"""
Connection Pool

Manages persistent connections (like WebSockets) with automatic reconnection,
health checking, and session duration limits.

Based on LiveKit's ConnectionPool implementation.
"""

from __future__ import annotations

import asyncio
import time
import weakref
from collections.abc import AsyncGenerator, Awaitable
from contextlib import asynccontextmanager
from typing import Callable, Generic, TypeVar

from .aio import cancel_and_wait

T = TypeVar("T")


class ConnectionPool(Generic[T]):
    """
    Helper class to manage persistent connections like websockets.
    
    Features:
    - Connection pooling and reuse
    - Automatic reconnection after max duration
    - Graceful connection cleanup
    - Prewarm support for faster first requests
    
    Example:
        async def create_ws(timeout: float) -> WebSocket:
            return await websockets.connect(url, timeout=timeout)
        
        async def close_ws(ws: WebSocket) -> None:
            await ws.close()
        
        pool = ConnectionPool[WebSocket](
            connect_cb=create_ws,
            close_cb=close_ws,
            max_session_duration=300,  # 5 minutes
        )
        
        # Use with context manager
        async with pool.connection(timeout=10) as ws:
            await ws.send("hello")
        
        # Or manually get/put
        conn = await pool.get(timeout=10)
        try:
            # use conn
            pass
        finally:
            pool.put(conn)
    """
    
    def __init__(
        self,
        *,
        connect_cb: Callable[[float], Awaitable[T]] | None = None,
        close_cb: Callable[[T], Awaitable[None]] | None = None,
        max_session_duration: float | None = None,
        mark_refreshed_on_get: bool = False,
        connect_timeout: float = 10.0,
    ) -> None:
        """
        Initialize the connection pool.
        
        Args:
            connect_cb: Async callback to create new connections. Receives timeout parameter.
            close_cb: Async callback to close connections
            max_session_duration: Maximum duration in seconds before forcing reconnection.
                                 If None, connections are never expired.
            mark_refreshed_on_get: If True, the session timestamp is updated when get() is called.
                                  Only used when max_session_duration is set.
            connect_timeout: Default timeout for connection attempts
        """
        self._connect_cb = connect_cb
        self._close_cb = close_cb
        self._max_session_duration = max_session_duration
        self._mark_refreshed_on_get = mark_refreshed_on_get
        self._connect_timeout = connect_timeout
        
        # Connection tracking
        self._connections: dict[T, float] = {}  # conn -> connected_at timestamp
        self._available: set[T] = set()  # Connections available for reuse
        self._to_close: set[T] = set()  # Connections queued for closing
        
        # Prewarm task
        self._prewarm_task: weakref.ref[asyncio.Task[None]] | None = None
    
    async def _connect(self, timeout: float) -> T:
        """
        Create a new connection.
        
        Args:
            timeout: Connection timeout in seconds
        
        Returns:
            The new connection object
        
        Raises:
            NotImplementedError: If no connect callback was provided
        """
        if self._connect_cb is None:
            raise NotImplementedError("Must provide connect_cb to ConnectionPool")
        
        connection = await self._connect_cb(timeout)
        self._connections[connection] = time.time()
        return connection
    
    async def _drain_to_close(self) -> None:
        """Drain and close all connections queued for closing"""
        for conn in list(self._to_close):
            await self._maybe_close_connection(conn)
        self._to_close.clear()
    
    @asynccontextmanager
    async def connection(self, *, timeout: float | None = None) -> AsyncGenerator[T, None]:
        """
        Get a connection from the pool and automatically return it when done.
        
        This is the recommended way to use the pool as it ensures connections
        are properly returned or removed on errors.
        
        Args:
            timeout: Connection timeout (defaults to connect_timeout)
        
        Yields:
            An active connection object
        
        Example:
            async with pool.connection(timeout=10) as conn:
                await conn.send("hello")
        """
        if timeout is None:
            timeout = self._connect_timeout
        
        conn = await self.get(timeout=timeout)
        try:
            yield conn
        except BaseException:
            # On error, remove connection from pool
            self.remove(conn)
            raise
        else:
            # On success, return connection to pool
            self.put(conn)
    
    async def get(self, *, timeout: float | None = None) -> T:
        """
        Get an available connection or create a new one if needed.
        
        This method:
        1. Drains any pending connection closures
        2. Tries to reuse an available non-expired connection
        3. Creates a new connection if none are available
        
        Args:
            timeout: Connection timeout (defaults to connect_timeout)
        
        Returns:
            An active connection object
        
        Example:
            conn = await pool.get(timeout=10)
            try:
                # use conn
                pass
            finally:
                pool.put(conn)
        """
        if timeout is None:
            timeout = self._connect_timeout
        
        await self._drain_to_close()
        now = time.time()
        
        # Try to reuse an available connection that hasn't expired
        while self._available:
            conn = self._available.pop()
            
            # Check if connection is still valid
            if (
                self._max_session_duration is None
                or now - self._connections[conn] <= self._max_session_duration
            ):
                # Connection is valid, optionally refresh timestamp
                if self._mark_refreshed_on_get:
                    self._connections[conn] = now
                return conn
            
            # Connection expired, mark for closing
            self.remove(conn)
        
        # No available connections, create a new one
        return await self._connect(timeout)
    
    def put(self, conn: T) -> None:
        """
        Mark a connection as available for reuse.
        
        If the connection has been removed from the pool (via remove()),
        it will not be added back.
        
        Args:
            conn: The connection to make available
        """
        if conn in self._connections:
            self._available.add(conn)
    
    async def _maybe_close_connection(self, conn: T) -> None:
        """
        Close a connection if close_cb is provided.
        
        Args:
            conn: The connection to close
        """
        if self._close_cb is not None:
            try:
                await self._close_cb(conn)
            except Exception:
                # Ignore errors during close
                pass
    
    def remove(self, conn: T) -> None:
        """
        Remove a specific connection from the pool.
        
        Marks the connection to be closed during the next drain cycle.
        This is useful when a connection encounters an error and should not be reused.
        
        Args:
            conn: The connection to remove
        """
        self._available.discard(conn)
        if conn in self._connections:
            self._to_close.add(conn)
            self._connections.pop(conn, None)
    
    def invalidate(self) -> None:
        """
        Clear all existing connections.
        
        Marks all current connections to be closed during the next drain cycle.
        Useful when you need to force reconnection of all connections.
        """
        for conn in list(self._connections.keys()):
            self._to_close.add(conn)
        self._connections.clear()
        self._available.clear()
    
    def prewarm(self) -> None:
        """
        Initiate prewarming of the connection pool without blocking.
        
        This method starts a background task that creates a new connection if none exist.
        This can reduce latency on the first actual request.
        The task automatically cleans itself up when the pool is closed.
        
        Example:
            pool = ConnectionPool(...)
            pool.prewarm()  # Start warming up in background
            # ... later ...
            conn = await pool.get()  # May use prewarmed connection
        """
        # Don't prewarm if already have connections or prewarm in progress
        if self._prewarm_task is not None or self._connections:
            return
        
        async def _prewarm_impl() -> None:
            """Background task to create initial connection"""
            if not self._connections:
                conn = await self._connect(timeout=self._connect_timeout)
                self._available.add(conn)
        
        task = asyncio.create_task(_prewarm_impl())
        self._prewarm_task = weakref.ref(task)
    
    async def aclose(self) -> None:
        """
        Close all connections and cleanup resources.
        
        This will:
        1. Cancel any prewarm task
        2. Invalidate all connections
        3. Drain and close all pending closures
        """
        # Cancel prewarm task if running
        if self._prewarm_task is not None:
            task = self._prewarm_task()
            if task and not task.done():
                await cancel_and_wait(task)
        
        # Invalidate and close all connections
        self.invalidate()
        await self._drain_to_close()


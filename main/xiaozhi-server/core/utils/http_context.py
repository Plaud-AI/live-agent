"""
HTTP Context Management

Provides a shared aiohttp.ClientSession for efficient HTTP requests.

Key Points:
- aiohttp.ClientSession has built-in connection pooling (limit_per_host=30, keepalive_timeout=15s)
- Creating one global session is sufficient for most use cases
- Session is created lazily on first use
- Should be closed on application shutdown
"""

from __future__ import annotations

import asyncio

import aiohttp

# Global shared session
_global_session: aiohttp.ClientSession | None = None
_session_lock = asyncio.Lock()


def http_session() -> aiohttp.ClientSession:
    """
    Get or create the global shared HTTP session.
    
    This function provides a singleton aiohttp.ClientSession that:
    - Has built-in connection pooling (reuses TCP connections)
    - Handles Keep-Alive automatically
    - Is thread/coroutine-safe
    
    Returns:
        A shared aiohttp.ClientSession instance
    
    Example:
        session = http_session()
        async with session.get(url) as resp:
            data = await resp.json()
    
    Note:
        The session is NOT automatically closed. Call cleanup_http_session()
        on application shutdown.
    """
    global _global_session
    
    if _global_session is None or _global_session.closed:
        # Create new global session with optimized settings
        connector = aiohttp.TCPConnector(
            limit_per_host=50,      # Max connections per host (default: 30)
            keepalive_timeout=120,  # Keep connections alive longer (default: 15s)
        )
        _global_session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),
        )
    
    return _global_session


async def cleanup_http_session() -> None:
    """
    Close and cleanup the global HTTP session.
    
    This should be called on application shutdown to ensure all resources
    are properly released.
    
    Example:
        # On application shutdown
        await cleanup_http_session()
    """
    global _global_session
    
    async with _session_lock:
        if _global_session and not _global_session.closed:
            await _global_session.close()
            _global_session = None


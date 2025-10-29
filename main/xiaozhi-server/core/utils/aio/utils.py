"""
Async Utilities

Provides utility functions for async task management.
"""

import asyncio
import functools
from typing import Any


async def cancel_and_wait(*futures: asyncio.Future[Any]) -> None:
    """
    Cancel multiple futures/tasks and wait for them to complete.
    
    This function properly handles:
    - Race conditions between checking done() and cancelling
    - Cleanup of callbacks to prevent memory leaks
    - Parallel waiting for all futures
    
    Args:
        *futures: Variable number of asyncio.Future or asyncio.Task objects to cancel
        
    Example:
        await cancel_and_wait(task1, task2, task3)
    """
    loop = asyncio.get_running_loop()
    waiters = []

    for fut in futures:
        waiter = loop.create_future()
        cb = functools.partial(_release_waiter, waiter)
        waiters.append((waiter, cb))
        fut.add_done_callback(cb)  # Register callback first
        fut.cancel()                # Then cancel

    try:
        for waiter, _ in waiters:
            await waiter
    finally:
        # Clean up callbacks to prevent memory leaks
        for i, fut in enumerate(futures):
            _, cb = waiters[i]
            fut.remove_done_callback(cb)


def _release_waiter(waiter: asyncio.Future[Any], *_: Any) -> None:
    """
    Internal helper to release a waiter future.
    
    Args:
        waiter: The future to release
        *_: Ignored arguments (from done callback)
    """
    if not waiter.done():
        waiter.set_result(None)


gracefully_cancel = cancel_and_wait


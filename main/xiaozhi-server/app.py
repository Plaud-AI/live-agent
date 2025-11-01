import sys
import signal
import asyncio
import logging
from aioconsole import ainput
from config.config_loader import load_config
from core.websocket_server import WebSocketServer
from core.utils.util import check_ffmpeg_installed

config = load_config()
log_config = config.log
logging.basicConfig(
    # filename=log_config.log_file, 
    level=log_config.log_level,
    format=log_config.log_format,
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def wait_for_exit() -> None:
    """
    Block until Ctrl‑C / SIGTERM is received.
    - Unix: use add_signal_handler
    - Windows: depend on KeyboardInterrupt
    """
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    if sys.platform != "win32":  # Unix / macOS
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await stop_event.wait()
    else:
        # Windows: await a forever pending future,
        # let KeyboardInterrupt bubble up to asyncio.run, to eliminate the problem of process exit blocking caused by legacy ordinary threads
        try:
            await asyncio.Future()
        except KeyboardInterrupt:  # Ctrl‑C
            pass


async def monitor_stdin():
    """monitor standard input, consume enter key"""
    while True:
        await ainput()  # async wait for input, consume enter key


async def main():
    check_ffmpeg_installed()

    global config

    # add stdin monitor task
    stdin_task = asyncio.create_task(monitor_stdin())

    # Create WebSocket server with async component initialization
    # This initializes VAD, STT, LLM, TTS in parallel for faster startup
    logging.info("Initializing WebSocket server with AI components...")
    ws_server = await WebSocketServer.create(config)
    
    # Start WebSocket server
    ws_task = asyncio.create_task(ws_server.start())

    try:
        await wait_for_exit()  # Block until exit signal received
    except asyncio.CancelledError:
        logging.error("Task cancelled, cleaning up resources...")
    finally:
        # Cancel all tasks (critical fix point)
        stdin_task.cancel()
        ws_task.cancel()

        # Wait for tasks to terminate (must add timeout)
        await asyncio.wait(
            [stdin_task, ws_task],
            timeout=3.0,
            return_when=asyncio.ALL_COMPLETED,
        )
        
        # Cleanup components
        if hasattr(ws_server, 'components'):
            logging.info("Shutting down AI components...")
            try:
                components = ws_server.components
                await components.aclose()
            except Exception as e:
                logging.error(f"Error shutting down components: {e}")
        
        logging.info("Server closed, program exited.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Manual interruption, program terminated.")

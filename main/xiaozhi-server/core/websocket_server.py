"""
WebSocket server implementation.

This module handles WebSocket connections and manages the server lifecycle.
"""

from __future__ import annotations

import asyncio
import logging
import websockets
from core.session import Session
from core.auth import AuthManager, AuthenticationError
from core.components import Components
from core.utils.util import check_vad_update, check_asr_update
from config.models import Config



class WebSocketServer:
    """
    WebSocket server for handling real-time audio connections.
    
    Use the create() factory method to instantiate with initialized components.
    
    Example:
        config = load_config()
        server = await WebSocketServer.create(config)
        await server.start()
    """
    
    @classmethod
    async def create(cls, config: Config) -> WebSocketServer:
        """
        Async factory method to create WebSocketServer with initialized components.
        
        This method initializes all AI components in parallel before creating the server,
        ensuring components are fully ready when the first connection arrives.
        
        Args:
            config: Application configuration (validated by Pydantic)
            
        Returns:
            Initialized WebSocketServer instance with all components ready
            
        Raises:
            RuntimeError: If component initialization fails
            
        Example:
            config = load_config("config.yaml")
            server = await WebSocketServer.create(config)
            await server.start()
        """
        logging.info("Creating WebSocket server with async component initialization...")
        
        # Initialize all components in parallel (VAD, STT, LLM, TTS)
        components = await Components.initialize(config)
        
        # Create server instance with initialized components
        server = cls(config, components)
        
        logging.info("✅ WebSocket server created successfully")
        return server
    
    def __init__(self, config: Config, components: Components):
        """
        Private constructor - use create() factory method instead.
        
        Args:
            config: Application configuration
            components: Pre-initialized AI components
        """
        self.config = config
        self.config_lock = asyncio.Lock()
        
        # Store global components (shared across all connections)
        self.components = components
        
        # Legacy attribute access for backward compatibility
        # TODO: Remove these once all code uses self.components
        self._vad = components.vad
        self._stt = components.stt
        self._llm = components.llm
        self._tts = components.tts
        
        # Legacy components (not yet migrated to new protocol)
        # TODO: Migrate Memory and Intent to new protocol
        self._memory = None  # Will be initialized if needed
        self._intent = None  # Will be initialized if needed

        self.active_connections: set[Session] = set()

        # auth_config = self.config.server.auth
        # self.auth_enable = auth_config.enabled
        # # Device whitelist
        # self.allowed_devices = set(auth_config.allowed_devices)
        # secret_key = self.config.server.auth_key
        # expire_seconds = auth_config.get("expire_seconds", None)
        # self.auth = AuthManager(secret_key=secret_key, expire_seconds=expire_seconds)
        
        # logging.info("WebSocket server instance initialized")

    async def start(self):
        server_config = self.config.server
        host = server_config.ip
        port = int(server_config.port)

        logging.info(f"Starting WebSocket server on {host}:{port}")
        async with websockets.serve(
            self._handle_connection, host, port, process_request=self._http_response
        ):
            await asyncio.Future()

    async def _handle_connection(self, websocket):
        """
        Handle connection using new protocol (Session-based).
        
        This is a clean, new implementation separate from the legacy handler.
        """
        try:
            from core.session import Session
            
            # Create session
            session = Session(
                components=self.components,
                config=self.config,
                websocket=websocket
            )
            
            # Run session (blocks until connection closes)
            await session.run()
        
        except Exception as e:
            logging.error(f"Session error: {e}", exc_info=True)

    # async def _handle_connection(self, websocket):
    #     """
    #     Legacy connection handler (existing implementation).
        
    #     TODO: Gradually migrate to _handle_new_protocol_connection
    #     """
    #     headers = dict(websocket.request.headers)
    #     if headers.get("device-id", None) is None:
    #         # 尝试从 URL 的查询参数中获取 device-id
    #         from urllib.parse import parse_qs, urlparse

    #         # 从 WebSocket 请求中获取路径
    #         request_path = websocket.request.path
    #         if not request_path:
    #             logging.error("Cannot get request path")
    #             await websocket.close()
    #             return
    #         parsed_url = urlparse(request_path)
    #         query_params = parse_qs(parsed_url.query)
    #         if "device-id" not in query_params:
    #             await websocket.send("端口正常，如需测试连接，请使用test_page.html")
    #             await websocket.close()
    #             return
    #         else:
    #             websocket.request.headers["device-id"] = query_params["device-id"][0]
    #         if "client-id" in query_params:
    #             websocket.request.headers["client-id"] = query_params["client-id"][0]
    #         if "authorization" in query_params:
    #             websocket.request.headers["authorization"] = query_params[
    #                 "authorization"
    #             ][0]

    #     """Handle new connection, each time create a separate ConnectionHandler"""
    #     # 先认证，后建立连接
    #     try:
    #         await self._handle_auth(websocket)
    #     except AuthenticationError:
    #         await websocket.send("认证失败")
    #         await websocket.close()
    #         return
    #     # Create ConnectionHandler with server instance
    #     # Note: ConnectionHandler will use server.components for new protocol
    #     handler = ConnectionHandler(
    #         self.config,
    #         self._vad,
    #         self._stt,  # Using _stt instead of _asr for consistency
    #         self._llm,
    #         self._memory,
    #         self._intent,
    #         self,  # Pass server instance
    #     )
    #     self.active_connections.add(handler)
    #     try:
    #         await handler.handle_connection(websocket)
    #     except Exception as e:
    #         logging.error(f"Error handling connection: {e}")
    #     finally:
    #         # Ensure the connection is removed from the active connections set
    #         self.active_connections.discard(handler)
    #         # Force close the connection (if not already closed)
    #         try:
    #             # Safely check the WebSocket state and close it
    #             if hasattr(websocket, "closed") and not websocket.closed:
    #                 await websocket.close()
    #             elif hasattr(websocket, "state") and websocket.state.name != "CLOSED":
    #                 await websocket.close()
    #             else:
    #                 # 如果没有closed属性，直接尝试关闭
    #                 await websocket.close()
    #         except Exception as close_error:
    #             logging.error(
    #                 f"Error forcing close connection: {close_error}"
    #             )

    async def _http_response(self, websocket, request_headers):
        # 检查是否为 WebSocket 升级请求
        logging.info(f"checking Request headers: {request_headers}")
        if request_headers.headers.get("connection", "").lower() == "upgrade":
            # 如果是 WebSocket 请求，返回 None 允许握手继续
            return None
        else:
            # 如果是普通 HTTP 请求，返回 "server is running"
            return websocket.respond(200, "Server is running\n")

    async def update_config(self) -> bool:
        """Update the server config and re-initialize the components

        Returns:
            bool: Whether the update is successful
        """
        try:
            async with self.config_lock:
                logging.info(f"Successfully got new config")
                # 检查 VAD 和 ASR 类型是否需要更新
                update_vad = check_vad_update(self.config, new_config)
                update_asr = check_asr_update(self.config, new_config)
                logging.info(
                    f"Check if VAD and ASR types need to be updated: {update_vad} {update_asr}"
                )
                # Update the config
                self.config = new_config
                # Re-initialize the components
                components = await Components.initialize(new_config)
                
                # Update components
                self.components = components
                self._vad = components.vad
                self._stt = components.stt
                self._llm = components.llm
                self._tts = components.tts
                
                # TODO: Re-initialize legacy components (Memory, Intent) if needed
                logging.info(f"Successfully updated the config")
                return True
        except Exception as e:
            logging.error(f"Failed to update the server config: {str(e)}")
            return False

    async def _handle_auth(self, websocket):
        # Authenticate first, then establish the connection
        if self.auth_enable:
            headers = dict(websocket.request.headers)
            device_id = headers.get("device-id", None)
            client_id = headers.get("client-id", None)
            if self.allowed_devices and device_id in self.allowed_devices:
                # 如果属于白名单内的设备，不校验token，直接放行
                return
            else:
                # 否则校验token
                token = headers.get("authorization", "")
                if token.startswith("Bearer "):
                    token = token[7:]  # 移除'Bearer '前缀
                else:
                    raise AuthenticationError("Missing or invalid Authorization header")
                # 进行认证
                auth_success = self.auth.verify_token(
                    token, client_id=client_id, username=device_id
                )
                if not auth_success:
                    raise AuthenticationError("Invalid token")

import asyncio
import json
import time

import websockets
from websockets.exceptions import ConnectionClosed, InvalidMessage
from config.logger import setup_logging
from core.connection import ConnectionHandler
from config.config_loader import get_config_from_api
from core.auth import AuthManager, AuthenticationError
from core.utils.modules_initialize import initialize_modules
from core.utils.util import check_vad_update, check_asr_update

TAG = __name__


# WebSocket 关闭码说明
CLOSE_CODE_DESCRIPTIONS = {
    1000: "正常关闭",
    1001: "端点离开（如页面关闭、服务器重启）",
    1002: "协议错误",
    1003: "收到不支持的数据类型",
    1005: "未收到关闭码（异常断开）",
    1006: "连接异常关闭（未收到关闭帧，可能是网络问题）",
    1007: "收到的数据类型与消息类型不一致",
    1008: "收到违反策略的消息",
    1009: "消息过大",
    1010: "客户端期望服务器协商扩展",
    1011: "服务器遇到意外情况",
    1012: "服务重启",
    1013: "稍后重试",
    1014: "网关收到无效响应",
    1015: "TLS 握手失败",
}


class WebSocketServer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.config_lock = asyncio.Lock()
        modules = initialize_modules(
            self.logger,
            self.config,
            True,
            False,
            False,
            False,
            "Memory" in self.config["selected_module"],
            "Intent" in self.config["selected_module"],
        )
        self._vad = modules["vad"] if "vad" in modules else None
        self._asr = modules["asr"] if "asr" in modules else None
        self._llm = modules["llm"] if "llm" in modules else None
        self._intent = modules["intent"] if "intent" in modules else None
        self._memory = modules["memory"] if "memory" in modules else None

        self.active_connections = set()

        auth_config = self.config["server"].get("auth", {})
        self.auth_enable = auth_config.get("enabled", False)
        # 设备白名单
        self.allowed_devices = set(auth_config.get("allowed_devices", []))
        secret_key = self.config["server"]["auth_key"]
        expire_seconds = auth_config.get("expire_seconds", None)
        self.auth = AuthManager(secret_key=secret_key, expire_seconds=expire_seconds)

    async def start(self):
        server_config = self.config["server"]
        host = server_config.get("ip", "0.0.0.0")
        port = int(server_config.get("port", 8000))

        async with websockets.serve(
            self._handle_connection, host, port, process_request=self._http_response,
            ping_interval=30, # Interval between keepalive pings in seconds
            ping_timeout=20, # Timeout for keepalive pings in seconds
            close_timeout=10, # Timeout for closing the connection in seconds
        ):
            await asyncio.Future()

    async def _handle_connection(self, websocket):
        # 记录连接建立时间
        conn_start_time = time.time()
        
        # 获取客户端 IP（优先使用代理头）
        client_ip = "unknown"
        try:
            headers = dict(websocket.request.headers)
            real_ip = headers.get("x-real-ip") or headers.get("x-forwarded-for")
            if real_ip:
                client_ip = real_ip.split(",")[0].strip()
            elif websocket.remote_address:
                client_ip = websocket.remote_address[0]
        except Exception:
            if websocket.remote_address:
                client_ip = websocket.remote_address[0]
        
        # 获取设备ID（用于日志）
        device_id = headers.get("device-id", "unknown")
        
        self.logger.bind(tag=TAG).info(
            f"🔗 [连接建立] IP={client_ip} | Device-ID={device_id} | "
            f"当前活动连接数={len(self.active_connections)}"
        )
        
        if headers.get("device-id", None) is None:
            # 尝试从 URL 的查询参数中获取 device-id
            from urllib.parse import parse_qs, urlparse

            # 从 WebSocket 请求中获取路径
            request_path = websocket.request.path
            if not request_path:
                self.logger.bind(tag=TAG).error(f"🔴 [连接拒绝] IP={client_ip} | 原因=无法获取请求路径")
                await websocket.close()
                return
            parsed_url = urlparse(request_path)
            query_params = parse_qs(parsed_url.query)
            if "device-id" not in query_params:
                self.logger.bind(tag=TAG).warning(
                    f"⚠️ [连接测试] IP={client_ip} | 原因=缺少device-id，可能是端口探测"
                )
                await websocket.send("端口正常，如需测试连接，请使用test_page.html")
                await websocket.close()
                return
            else:
                websocket.request.headers["device-id"] = query_params["device-id"][0]
                device_id = query_params["device-id"][0]  # 更新设备ID
            if "client-id" in query_params:
                websocket.request.headers["client-id"] = query_params["client-id"][0]
            if "agent-id" in query_params:
                websocket.request.headers["agent-id"] = query_params["agent-id"][0]
            if "authorization" in query_params:
                websocket.request.headers["authorization"] = query_params[
                    "authorization"
                ][0]
            if "timezone" in query_params:
                self.logger.bind(tag=TAG).info(f"timezone: {query_params['timezone'][0]}")
                websocket.request.headers["timezone"] = query_params["timezone"][0]

        """处理新连接，每次创建独立的ConnectionHandler"""
        # 先认证，后建立连接
        try:
            await self._handle_auth(websocket)
        except AuthenticationError as auth_error:
            self.logger.bind(tag=TAG).warning(
                f"🔐 [认证失败] IP={client_ip} | Device-ID={device_id} | 原因={auth_error}"
            )
            await websocket.send("认证失败")
            await websocket.close()
            return
        
        self.logger.bind(tag=TAG).info(
            f"✅ [认证成功] IP={client_ip} | Device-ID={device_id}"
        )
        
        # 创建ConnectionHandler时传入当前server实例
        handler = ConnectionHandler(
            self.config,
            self._vad,
            self._asr,
            self._llm,
            self._memory,
            self._intent,
            self,  # 传入server实例
        )
        self.active_connections.add(handler)
        
        # 记录连接关闭原因
        close_reason = "未知"
        close_code = None
        
        try:
            await handler.handle_connection(websocket)
            close_reason = "正常结束"
        except ConnectionClosed as cc:
            close_code = cc.code
            close_reason = CLOSE_CODE_DESCRIPTIONS.get(cc.code, f"未知关闭码({cc.code})")
            self.logger.bind(tag=TAG).info(
                f"🔌 [连接关闭] IP={client_ip} | Device-ID={device_id} | "
                f"关闭码={cc.code} | 原因={close_reason} | 详情={cc.reason or '无'}"
            )
        except Exception as e:
            close_reason = f"异常: {type(e).__name__}"
            self.logger.bind(tag=TAG).error(
                f"❌ [连接异常] IP={client_ip} | Device-ID={device_id} | "
                f"异常类型={type(e).__name__} | 详情={e}"
            )
        finally:
            # 计算连接持续时间
            conn_duration = time.time() - conn_start_time
            
            # 确保从活动连接集合中移除
            self.active_connections.discard(handler)
            
            self.logger.bind(tag=TAG).info(
                f"📊 [连接统计] IP={client_ip} | Device-ID={device_id} | "
                f"持续时间={conn_duration:.1f}秒 | 关闭原因={close_reason} | "
                f"剩余活动连接数={len(self.active_connections)}"
            )
            
            # 强制关闭连接（如果还没有关闭的话）
            try:
                # 安全地检查WebSocket状态并关闭
                if hasattr(websocket, "closed") and not websocket.closed:
                    await websocket.close()
                elif hasattr(websocket, "state") and websocket.state.name != "CLOSED":
                    await websocket.close()
                else:
                    # 如果没有closed属性，直接尝试关闭
                    await websocket.close()
            except Exception as close_error:
                self.logger.bind(tag=TAG).error(
                    f"服务器端强制关闭连接时出错: {close_error}"
                )

    async def _http_response(self, websocket, request_headers):
        # 获取客户端 IP
        client_ip = "unknown"
        try:
            real_ip = request_headers.headers.get("x-real-ip") or request_headers.headers.get("x-forwarded-for")
            if real_ip:
                client_ip = real_ip.split(",")[0].strip()
            elif websocket.remote_address:
                client_ip = websocket.remote_address[0]
        except Exception:
            pass
        
        # 检查是否为 WebSocket 升级请求
        connection_header = request_headers.headers.get("connection", "").lower()
        upgrade_header = request_headers.headers.get("upgrade", "").lower()
        
        if connection_header == "upgrade" and upgrade_header == "websocket":
            # 如果是 WebSocket 请求，返回 None 允许握手继续
            self.logger.bind(tag=TAG).debug(
                f"🤝 [握手请求] IP={client_ip} | WebSocket升级请求"
            )
            return None
        else:
            # 记录非 WebSocket 请求的详细信息（用于排查 HTTP/2 等异常请求）
            method = getattr(request_headers, 'method', 'UNKNOWN')
            path = getattr(request_headers, 'path', '/')
            user_agent = request_headers.headers.get("user-agent", "unknown")
            
            self.logger.bind(tag=TAG).warning(
                f"⚠️ [非WS请求] IP={client_ip} | Method={method} | Path={path} | "
                f"Connection={connection_header} | Upgrade={upgrade_header} | "
                f"User-Agent={user_agent[:50] if user_agent else 'unknown'}"
            )
            
            # 如果是普通 HTTP 请求，返回 "server is running"
            return websocket.respond(200, "Server is running\n")

    async def update_config(self) -> bool:
        """更新服务器配置并重新初始化组件

        Returns:
            bool: 更新是否成功
        """
        try:
            async with self.config_lock:
                # 重新获取配置
                new_config = get_config_from_api(self.config)
                if new_config is None:
                    self.logger.bind(tag=TAG).error("获取新配置失败")
                    return False
                self.logger.bind(tag=TAG).info(f"获取新配置成功")
                # 检查 VAD 和 ASR 类型是否需要更新
                update_vad = check_vad_update(self.config, new_config)
                update_asr = check_asr_update(self.config, new_config)
                self.logger.bind(tag=TAG).info(
                    f"检查VAD和ASR类型是否需要更新: {update_vad} {update_asr}"
                )
                # 更新配置
                self.config = new_config
                # 重新初始化组件
                modules = initialize_modules(
                    self.logger,
                    new_config,
                    update_vad,
                    update_asr,
                    "LLM" in new_config["selected_module"],
                    False,
                    "Memory" in new_config["selected_module"],
                    "Intent" in new_config["selected_module"],
                )

                # 更新组件实例
                if "vad" in modules:
                    self._vad = modules["vad"]
                if "asr" in modules:
                    self._asr = modules["asr"]
                if "llm" in modules:
                    self._llm = modules["llm"]
                if "intent" in modules:
                    self._intent = modules["intent"]
                if "memory" in modules:
                    self._memory = modules["memory"]
                self.logger.bind(tag=TAG).info(f"更新配置任务执行完毕")
                return True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"更新服务器配置失败: {str(e)}")
            return False

    async def _handle_auth(self, websocket):
        # 先认证，后建立连接
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

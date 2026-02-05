import asyncio
from aiohttp import web
from config.logger import setup_logging
from core.api.ota_handler import OTAHandler
from core.api.vision_handler import VisionHandler
from core.api.warmup_handler import WarmupHandler
from core.api.agora_handler import AgoraHandler

TAG = __name__


class SimpleHttpServer:
    def __init__(self, config: dict, ws_server=None):
        self.config = config
        self.logger = setup_logging()
        self.ws_server = ws_server  # WebSocketServer 实例，用于共享模块
        self.ota_handler = OTAHandler(config)
        self.vision_handler = VisionHandler(config)
        self.warmup_handler = WarmupHandler(config)
        self.agora_handler = AgoraHandler(config, ws_server)

    def _get_websocket_url(self, local_ip: str, port: int) -> str:
        """获取websocket地址

        Args:
            local_ip: 本地IP地址
            port: 端口号

        Returns:
            str: websocket地址
        """
        server_config = self.config["server"]
        websocket_config = server_config.get("websocket")

        if websocket_config and "你" not in websocket_config:
            return websocket_config
        else:
            return f"ws://{local_ip}:{port}/xiaozhi/v1/"

    async def start(self):
        self.logger.bind(tag=TAG).info("HTTP 服务器启动开始...")
        try:
            server_config = self.config["server"]
            read_config_from_api = self.config.get("read_config_from_api", False)
            host = server_config.get("ip", "0.0.0.0")
            port = int(server_config.get("http_port", 8003))
            self.logger.bind(tag=TAG).info(f"HTTP 服务器配置: host={host}, port={port}")

            if port:
                app = web.Application()

                if not read_config_from_api:
                    # 如果没有开启智控台，只是单模块运行，就需要再添加简单OTA接口，用于下发websocket接口
                    app.add_routes(
                        [
                            web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                            web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                            web.options(
                                "/xiaozhi/ota/", self.ota_handler.handle_options
                            ),
                            # 下载接口，仅提供 data/bin/*.bin 下载
                            web.get(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_download,
                            ),
                            web.options(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_options,
                            ),
                        ]
                    )
                # 添加路由
                app.add_routes(
                    [
                        web.get("/mcp/vision/explain", self.vision_handler.handle_get),
                        web.post(
                            "/mcp/vision/explain", self.vision_handler.handle_post
                        ),
                        web.options(
                            "/mcp/vision/explain", self.vision_handler.handle_options
                        ),
                        # 缓存预热接口
                        web.post(
                            "/internal/warmup/agent", self.warmup_handler.warmup_agent
                        ),
                        web.post(
                            "/internal/warmup/user", self.warmup_handler.warmup_user_agents
                        ),
                        web.options(
                            "/internal/warmup/agent", self.warmup_handler.handle_options
                        ),
                        web.options(
                            "/internal/warmup/user", self.warmup_handler.handle_options
                        ),
                        # Agora RTC API
                        web.post(
                            "/api/agora/token/generate", self.agora_handler.generate_token
                        ),
                        web.post(
                            "/api/agora/agent/start", self.agora_handler.start_agent
                        ),
                        web.post(
                            "/api/agora/agent/stop", self.agora_handler.stop_agent
                        ),
                        web.post(
                            "/api/agora/agent/ping", self.agora_handler.ping_agent
                        ),
                        web.options(
                            "/api/agora/token/generate", self.agora_handler.handle_options
                        ),
                        web.options(
                            "/api/agora/agent/start", self.agora_handler.handle_options
                        ),
                        web.options(
                            "/api/agora/agent/stop", self.agora_handler.handle_options
                        ),
                        web.options(
                            "/api/agora/agent/ping", self.agora_handler.handle_options
                        ),
                    ]
                )

                # 运行服务
                self.logger.bind(tag=TAG).info("HTTP 服务器: 创建 AppRunner...")
                runner = web.AppRunner(app)
                await runner.setup()
                self.logger.bind(tag=TAG).info("HTTP 服务器: 创建 TCPSite...")
                site = web.TCPSite(runner, host, port)
                await site.start()
                self.logger.bind(tag=TAG).info(f"HTTP 服务器已启动，监听 {host}:{port}")

                # 保持服务运行
                while True:
                    await asyncio.sleep(3600)  # 每隔 1 小时检查一次
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"HTTP服务器启动失败: {e}")
            import traceback

            self.logger.bind(tag=TAG).error(f"错误堆栈: {traceback.format_exc()}")
            raise

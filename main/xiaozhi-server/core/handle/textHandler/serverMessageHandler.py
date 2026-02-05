import asyncio
import json
from typing import Dict, Any

from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType
from core.providers.tools.device_mcp import handle_mcp_message

TAG = __name__

class ServerTextMessageHandler(TextMessageHandler):
    """MCP消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.SERVER

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        # 如果配置是从API读取的，则需要验证secret
        if not conn.read_config_from_api:
            return
        # 获取post请求的secret
        post_secret = msg_json.get("content", {}).get("secret", "")
        secret = conn.config["manager-api"].get("secret", "")
        # 如果secret不匹配，则返回
        if post_secret != secret:
            error_msg =             json.dumps(
                {
                    "type": "server",
                    "status": "error",
                    "message": "服务器密钥验证失败",
                }
            )
            await conn.channel.send_text(error_msg)
            return
        # 动态更新配置
        if msg_json["action"] == "update_config":
            try:
                # 更新WebSocketServer的配置
                if not conn.server:
                    error_msg = json.dumps(
                        {
                            "type": "server",
                            "status": "error",
                            "message": "无法获取服务器实例",
                            "content": {"action": "update_config"},
                        }
                    )
                    await conn.channel.send_text(error_msg)
                    return

                if not await conn.server.update_config():
                    error_msg = json.dumps(
                        {
                            "type": "server",
                            "status": "error",
                            "message": "更新服务器配置失败",
                            "content": {"action": "update_config"},
                        }
                    )
                    await conn.channel.send_text(error_msg)
                    return

                # 发送成功响应
                success_msg = json.dumps(
                    {
                        "type": "server",
                        "status": "success",
                        "message": "配置更新成功",
                        "content": {"action": "update_config"},
                    }
                )
                await conn.channel.send_text(success_msg)
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"更新配置失败: {str(e)}")
                error_msg = json.dumps(
                    {
                        "type": "server",
                        "status": "error",
                        "message": f"更新配置失败: {str(e)}",
                        "content": {"action": "update_config"},
                    }
                )
                await conn.channel.send_text(error_msg)
        # 重启服务器
        elif msg_json["action"] == "restart":
            await conn.handle_restart(msg_json)
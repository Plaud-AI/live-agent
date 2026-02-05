import json

from core.handle.textMessageHandlerRegistry import TextMessageHandlerRegistry

TAG = __name__


class TextMessageProcessor:
    """消息处理器主类"""

    def __init__(self, registry: TextMessageHandlerRegistry):
        self.registry = registry

    async def process_message(self, conn, message: str) -> None:
        """处理消息的主入口"""
        try:
            # 解析JSON消息
            msg_json = json.loads(message)

            # 处理JSON消息
            if isinstance(msg_json, dict):
                message_type = msg_json.get("type")

                # 记录日志
                if hasattr(conn, 'logger') and conn.logger:
                    conn.logger.bind(tag=TAG).info(f"收到{message_type}消息：{message}")
                else:
                    # 如果 logger 不存在，使用默认 logger
                    import logging
                    logging.info(f"[{TAG}] 收到{message_type}消息：{message}")

                # 获取并执行处理器
                handler = self.registry.get_handler(message_type)
                if handler:
                    if hasattr(conn, 'logger') and conn.logger:
                        conn.logger.bind(tag=TAG).debug(f"process_message: 找到处理器 {handler.__class__.__name__}，开始处理")
                    await handler.handle(conn, msg_json)
                else:
                    if hasattr(conn, 'logger') and conn.logger:
                        conn.logger.bind(tag=TAG).error(f"收到未知类型消息：{message}")
                    else:
                        import logging
                        logging.error(f"[{TAG}] 收到未知类型消息：{message}")
            # 处理纯数字消息
            elif isinstance(msg_json, int):
                if hasattr(conn, 'logger') and conn.logger:
                    conn.logger.bind(tag=TAG).info(f"收到数字消息：{message}")
                await conn.channel.send_text(message)

        except json.JSONDecodeError:
            # 非JSON消息直接转发
            if hasattr(conn, 'logger') and conn.logger:
                conn.logger.bind(tag=TAG).error(f"解析到错误的消息：{message}")
            await conn.channel.send_text(message)
        except Exception as e:
            # 捕获所有其他异常，避免静默失败
            if hasattr(conn, 'logger') and conn.logger:
                conn.logger.bind(tag=TAG).error(f"处理消息时发生异常: {e}, message={message[:100]}")
            else:
                import logging
                import traceback
                logging.error(f"[{TAG}] 处理消息时发生异常: {e}, traceback: {traceback.format_exc()}")

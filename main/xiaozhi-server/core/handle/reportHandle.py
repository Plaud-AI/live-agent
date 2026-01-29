"""
TTS上报功能已集成到ConnectionHandler类中。

上报功能包括：
1. 每个连接对象拥有自己的上报队列和处理线程
2. 上报线程的生命周期与连接对象绑定
3. 使用ConnectionHandler.enqueue_tts_report方法进行上报

上报目标：统一上报到 live-agent-api
- 需要 agent_id 才能上报
- 设备连接需要先绑定 agent 才有 agent_id

具体实现请参考core/connection.py中的相关代码。
"""

import time
import base64

TAG = __name__

# 延迟导入 live_agent_report，避免循环导入
_live_agent_report = None

def _get_live_agent_report():
    """延迟获取 live_agent_report 函数"""
    global _live_agent_report
    if _live_agent_report is None:
        from config.live_agent_api_client import report_chat_message
        _live_agent_report = report_chat_message
    return _live_agent_report


async def report(conn, type, text, opus_data, report_time):
    """执行聊天记录上报操作（统一上报到 live-agent-api）

    Args:
        conn: 连接对象
        type: 上报类型，1为用户，2为智能体
        text: 合成文本
        opus_data: opus音频数据
        report_time: 上报时间
    """
    # 必须有 agent_id 才能上报
    if not conn.agent_id:
        conn.logger.bind(tag=TAG).debug(
            f"跳过聊天记录上报: 无 agent_id (device_id={conn.device_id})"
        )
        return
    
    try:
        await _report_to_live_agent_api(conn, type, text, opus_data, report_time)
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"聊天记录上报失败: {e}")


async def _report_to_live_agent_api(conn, role, text, opus_data, report_time):
    """上报到 live-agent-api
    
    Args:
        conn: 连接对象
        role: 角色类型，1=用户，2=智能体
        text: 消息文本
        opus_data: opus音频数据
        report_time: 上报时间
    """
    # 构建消息内容列表
    content_items = [{"message_type": "text", "message_content": text}]
    
    # 如果有音频数据，添加到内容列表
    if opus_data:
        # 将 opus packets 合并为一个 bytes 对象
        opus_bytes = b"".join(opus_data)
        audio_base64 = base64.b64encode(opus_bytes).decode("utf-8")
        content_items.append({"message_type": "audio", "message_content": audio_base64})
    
    # 调用 live-agent-api 上报（使用延迟导入）
    live_agent_report = _get_live_agent_report()
    result = live_agent_report(
        agent_id=conn.agent_id,
        role=role,
        content_items=content_items,
        message_time=report_time,
        config=conn.config  # 传入配置以确保客户端初始化
    )
    
    if result:
        conn.logger.bind(tag=TAG).info(
            f"消息上报成功: agent_id={conn.agent_id}, role={role}, text={text[:50] if text else 'None'}..."
        )
    else:
        conn.logger.bind(tag=TAG).error(
            f"消息上报失败: agent_id={conn.agent_id}, role={role}, text={text}"
        )




def enqueue_tts_report(conn, text, opus_data):
    """将TTS数据加入上报队列（统一上报到 live-agent-api）

    Args:
        conn: 连接对象
        text: 合成文本
        opus_data: opus音频数据
    """
    # 必须有 agent_id 才能上报
    if not conn.agent_id:
        conn.logger.bind(tag=TAG).debug(f"跳过TTS上报: 无 agent_id")
        return
    
    try:
        conn.report_queue.put((2, text, opus_data, int(time.time())))
        conn.logger.bind(tag=TAG).info(
            f"TTS数据已加入上报队列: agent_id={conn.agent_id}, text={text[:50] if text else 'None'}..."
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"加入TTS上报队列失败: {text}, {e}")


def enqueue_asr_report(conn, text, opus_data):
    """将ASR数据加入上报队列（统一上报到 live-agent-api）

    Args:
        conn: 连接对象
        text: 识别文本
        opus_data: opus音频数据
    """
    # 必须有 agent_id 才能上报
    if not conn.agent_id:
        conn.logger.bind(tag=TAG).debug(f"跳过ASR上报: 无 agent_id")
        return
    
    try:
        conn.report_queue.put((1, text, opus_data, int(time.time())))
        conn.logger.bind(tag=TAG).info(
            f"ASR数据已加入上报队列: agent_id={conn.agent_id}, text={text}"
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"加入ASR上报队列失败: {text}, {e}")

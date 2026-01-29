import json

TAG = __name__


async def handleAbortMessage(conn):
    conn.logger.bind(tag=TAG).info("Abort message received")
    
    # 使用锁保护对 llm_cancel_event 的访问，避免与 receiveAudioHandle 竞争
    with conn.chat_lock:
        # 设置成打断状态，会自动打断llm、tts任务
        conn.client_abort = True
        
        # 触发 LLM 取消事件
        if hasattr(conn, 'llm_cancel_event') and conn.llm_cancel_event:
            conn.llm_cancel_event.set()
            conn.logger.bind(tag=TAG).debug("LLM cancel event triggered")
    
    conn.clear_queues()
    # 打断客户端说话状态
    await conn.websocket.send(
        json.dumps({"type": "tts", "state": "stop", "session_id": conn.session_id})
    )
    conn.clearSpeakStatus()
    conn.logger.bind(tag=TAG).info("Abort message received-end")

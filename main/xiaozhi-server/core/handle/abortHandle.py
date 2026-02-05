import json
import asyncio

TAG = __name__


async def handleAbortMessage(conn):
    conn.logger.bind(tag=TAG).info("Abort message received")
    
    # 使用锁保护对 llm_cancel_event 的访问，避免与 receiveAudioHandle 竞争
    # 注意：将同步锁操作放到线程池执行，避免阻塞事件循环
    def _set_abort_state():
        with conn.chat_lock:
            # 设置成打断状态，会自动打断llm、tts任务
            conn.client_abort = True
            
            # 触发 LLM 取消事件
            if hasattr(conn, 'llm_cancel_event') and conn.llm_cancel_event:
                conn.llm_cancel_event.set()
                if hasattr(conn, 'logger') and conn.logger:
                    conn.logger.bind(tag=TAG).debug("LLM cancel event triggered")
    
    # 在线程池中执行，避免阻塞事件循环
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _set_abort_state)
    
    conn.clear_queues()
    # 打断客户端说话状态
    stop_message = json.dumps({"type": "tts", "state": "stop", "session_id": conn.session_id})
    await conn.channel.send_text(stop_message)
    conn.clearSpeakStatus()
    conn.logger.bind(tag=TAG).info("Abort message received-end")

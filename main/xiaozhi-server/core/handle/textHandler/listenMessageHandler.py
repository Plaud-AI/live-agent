import time
from typing import Dict, Any, List, TYPE_CHECKING
import asyncio

from core.handle.receiveAudioHandle import handleAudioMessage, startToChat
from core.handle.reportHandle import enqueue_asr_report
from core.handle.sendAudioHandle import send_stt_message, send_tts_message
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType
from core.handle.helloHandle import checkWakeupWords
from core.utils.wakeup_suppression import is_wakeup_word
from core.utils.util import remove_punctuation_and_length

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__


def build_multimodal_content(text: str, attachments: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Build multimodal content (Groq/OpenAI Responses API format)
    
    Args:
        text: Text content
        attachments: Attachments list, format:
            [
                {"type": "image", "url": "https://..."},
                {"type": "file", "url": "https://..."}
            ]
    
    Returns:
        Responses API compatible multimodal content:
        [
            {"type": "input_text", "text": "..."},
            {"type": "input_image", "image_url": "https://..."},
            {"type": "input_file", "file_url": "https://..."}
        ]
    """
    content = []
    
    # add attachments(images first, let LLM "see" them first)
    for attachment in attachments:
        att_type = attachment.get("type")
        url = attachment.get("url")
        
        if not att_type or not url:
            continue
            
        if att_type == "image":
            content.append({
                "type": "input_image",
                "image_url": url
            })
        elif att_type == "file":
            content.append({
                "type": "input_file",
                "file_url": url
            })
    
    # add text content at last
    if text:
        content.append({"type": "input_text", "text": text})
    
    return content

class ListenTextMessageHandler(TextMessageHandler):
    """Listen消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.LISTEN

    async def handle(self, conn: 'ConnectionHandler', msg_json: Dict[str, Any]) -> None:
        if "mode" in msg_json:
            conn.client_listen_mode = msg_json["mode"]
            conn.logger.bind(tag=TAG).info(
                f"客户端拾音模式：{conn.client_listen_mode}"
            )
            await conn.asr.open_audio_channels(conn)
        if msg_json["state"] == "start":
            conn.client_have_voice = True
            conn.client_voice_stop = False
        elif msg_json["state"] == "stop":
            conn.client_have_voice = True
            conn.client_voice_stop = True
            if len(conn.asr_audio) > 0:
                await handleAudioMessage(conn, b"")
        elif msg_json["state"] == "detect":
            conn.client_have_voice = False
            conn.asr_audio.clear()
            if "text" in msg_json:
                conn.last_activity_time = time.time() * 1000
                original_text = msg_json["text"]  # 保留原始文本
                filtered_len, filtered_text = remove_punctuation_and_length(
                    original_text
                )

                # 识别是否是唤醒词
                is_wakeup_words = is_wakeup_word(
                    filtered_text, conn.config.get("wakeup_words", [])
                )
                # 是否开启唤醒词回复
                enable_greeting = conn.config.get("enable_greeting", True)

                if is_wakeup_words and not enable_greeting:
                    # 如果是唤醒词，且关闭了唤醒词回复，就不用回答
                    await send_stt_message(conn, original_text)
                    await send_tts_message(conn, "stop", None)
                    conn.client_is_speaking = False
                elif is_wakeup_words:
                    # === 唤醒延迟优化：异步化 agent 配置拉取 ===
                    # 必须保证用 agent 配置的音色播放唤醒回复
                    # 优化点：将同步 HTTP 调用改为异步，减少阻塞时间
                    
                    wakeup_start_time = time.time() * 1000
                    
                    # 1. 如果需要初始化 agent，先异步完成（必须等待，保证音色正确）
                    needs_agent_init = (
                        (getattr(conn, "defer_agent_init", False) or not conn.agent_id)
                        and getattr(conn, "read_config_from_live_agent_api", False)
                    )
                    if needs_agent_init:
                        init_start = time.time() * 1000
                        ready = await conn.ensure_agent_ready(filtered_text)
                        init_elapsed = time.time() * 1000 - init_start
                        conn.logger.bind(tag=TAG).info(
                            f"⚡ [唤醒延迟] agent 配置加载: {init_elapsed:.0f}ms"
                        )
                        if not ready:
                            conn.logger.bind(tag=TAG).error("未能解析 agent，结束会话")
                            return
                    
                    # Record timestamp for correct message ordering
                    report_time = int(time.time())
                    
                    # 2. 播放缓存的唤醒词短回复（现在已经有正确的 voice_id 了）
                    wakeup_handled = await checkWakeupWords(conn, filtered_text)
                    
                    wakeup_elapsed = time.time() * 1000 - wakeup_start_time
                    conn.logger.bind(tag=TAG).info(
                        f"⚡ [唤醒延迟] 唤醒回复总耗时: {wakeup_elapsed:.0f}ms"
                    )
                    
                    if wakeup_handled:
                        # 成功播放了缓存的短回复，上报唤醒事件后返回
                        enqueue_asr_report(conn, original_text, [], report_time=report_time)
                        conn.logger.bind(tag=TAG).info("设备端唤醒词已通过缓存短回复处理")
                        return
                    
                    # 选项1：唤醒不走 LLM。若短回复未能播放（极少见），仅上报唤醒事件后返回。
                    enqueue_asr_report(conn, original_text, [], report_time=report_time)
                    conn.logger.bind(tag=TAG).warning(
                        "唤醒词短回复未播放成功，已跳过 LLM 兜底（Option1）"
                    )
                    return
                else:
                    # === 非唤醒词文本也需要初始化 agent ===
                    # 当设备发送的文本不是唤醒词时，也需要确保 agent 初始化完成
                    # 否则后续 startToChat 会因为 wait_agent_ready 超时而失败
                    needs_agent_init = (
                        (getattr(conn, "defer_agent_init", False) or not conn.agent_id)
                        and getattr(conn, "read_config_from_live_agent_api", False)
                    )
                    if needs_agent_init:
                        init_start = time.time() * 1000
                        ready = await conn.ensure_agent_ready(filtered_text)
                        init_elapsed = time.time() * 1000 - init_start
                        if init_elapsed > 100:
                            conn.logger.bind(tag=TAG).info(
                                f"⚡ [非唤醒词] agent 配置加载: {init_elapsed:.0f}ms"
                            )
                        if not ready:
                            conn.logger.bind(tag=TAG).error("未能解析 agent，结束会话")
                            return
                    
                    # check if there are attachments(eg. images, files) in text mode
                    attachments = msg_json.get("attachments", [])
                    # Record timestamp for correct message ordering
                    report_time = int(time.time())

                    if conn.memory is not None:
                        client_timezone = conn.client_timezone
                        memory_start = time.time()
                        memory_task = asyncio.create_task(conn.memory.query_memory(original_text, client_timezone=client_timezone))
                        done, _ = await asyncio.wait({memory_task}, timeout=1.0)
                        
                        if done:
                            conn.relevant_memories_this_turn = memory_task.result()
                            conn.logger.bind(tag=TAG).info(f"[Memory] query took {(time.time() - memory_start) * 1000:.0f}ms")
                        else:
                            # Timeout: don't wait for cancellation, just move on
                            memory_task.cancel()
                            conn.logger.bind(tag=TAG).warning(f"[Memory] query timeout after {(time.time() - memory_start) * 1000:.0f}ms")
                            conn.relevant_memories_this_turn = "No relevant memories retrieved for this turn."
                    
                    if attachments:
                        # build multimodal content
                        multimodal_content = build_multimodal_content(original_text, attachments)
                        # report text data with attachments
                        enqueue_asr_report(conn, original_text, [], attachments, report_time=report_time)
                        # use multimodal content to chat
                        await startToChat(conn, original_text, multimodal_content)
                    else:
                        # 上报纯文字数据（复用ASR上报功能，但不提供音频数据）
                        enqueue_asr_report(conn, original_text, [], report_time=report_time)
                        # 否则需要LLM对文字内容进行答复
                        await startToChat(conn, original_text)
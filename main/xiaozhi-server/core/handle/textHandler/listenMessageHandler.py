"""
Listen 消息处理器

处理客户端发送的 listen 消息，支持三种状态：
- start: 开始语音监听
- stop: 停止语音监听，触发 ASR 识别
- detect: 直接发送文字消息（来自移动端 App 或测试页面）
"""

import time
import asyncio
from typing import Dict, Any, List

from core.handle.receiveAudioHandle import startToChat
from core.handle.reportHandle import enqueue_asr_report
from core.handle.sendAudioHandle import send_stt_message, send_tts_message
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType
from core.handle.helloHandle import checkWakeupWords
from core.utils.util import remove_punctuation_and_length
from core.providers.asr.dto.dto import InterfaceType

TAG = __name__


def _is_wakeup_word(text: str, wakeup_words: list) -> bool:
    """判断文本是否为唤醒词（简单的包含匹配）"""
    if not text or not wakeup_words:
        return False
    # 去除标点后进行匹配
    _, clean_text = remove_punctuation_and_length(text)
    clean_text_lower = clean_text.lower()
    for word in wakeup_words:
        if word and word.lower() in clean_text_lower:
            return True
    return False


def _build_multimodal_content(text: str, attachments: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    构建多模态内容（兼容 OpenAI Responses API 格式）
    
    Args:
        text: 文本内容
        attachments: 附件列表 [{"type": "image", "url": "..."}, ...]
    
    Returns:
        多模态内容列表
    """
    content = []
    
    # 先添加图片/文件（让 LLM 先"看到"）
    for att in (attachments or []):
        att_type = att.get("type")
        url = att.get("url")
        if att_type == "image" and url:
            content.append({"type": "input_image", "image_url": url})
        elif att_type == "file" and url:
            content.append({"type": "input_file", "file_url": url})
    
    # 最后添加文本
    if text:
        content.append({"type": "input_text", "text": text})
    
    return content


class ListenTextMessageHandler(TextMessageHandler):
    """Listen 消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.LISTEN

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        """处理 listen 消息"""
        
        # 更新客户端拾音模式
        if "mode" in msg_json:
            conn.client_listen_mode = msg_json["mode"]
            conn.logger.bind(tag=TAG).debug(f"客户端拾音模式: {conn.client_listen_mode}")
        
        state = msg_json.get("state", "")
        
        if state == "start":
            await self._handle_start(conn)
        elif state == "stop":
            await self._handle_stop(conn)
        elif state == "detect":
            await self._handle_detect(conn, msg_json)

    async def _handle_start(self, conn) -> None:
        """处理开始监听"""
        conn.client_have_voice = True
        conn.client_voice_stop = False

    async def _handle_stop(self, conn) -> None:
        """处理停止监听，触发 ASR"""
        conn.client_have_voice = True
        conn.client_voice_stop = True
        
        if conn.asr.interface_type == InterfaceType.STREAM:
            # 流式 ASR：发送结束请求
            asyncio.create_task(conn.asr._send_stop_request())
        else:
            # 非流式 ASR：直接处理已收集的音频
            if len(conn.asr_audio) > 0:
                audio_data = conn.asr_audio.copy()
                conn.asr_audio.clear()
                conn.reset_vad_states()
                if audio_data:
                    await conn.asr.handle_voice_stop(conn, audio_data)

    async def _handle_detect(self, conn, msg_json: Dict[str, Any]) -> None:
        """
        处理文字消息（来自移动端 App 或测试页面）
        
        消息格式：
        {
            "type": "listen",
            "state": "detect",
            "text": "你好",
            "source": "text",  # 可选
            "attachments": [{"type": "image", "url": "..."}]  # 可选
        }
        """
        conn.client_have_voice = False
        conn.asr_audio.clear()
        
        text = msg_json.get("text", "").strip()
        if not text:
            return
        
        conn.last_activity_time = time.time() * 1000
        
        # 获取配置
        wakeup_words = conn.config.get("wakeup_words", [])
        enable_greeting = conn.config.get("enable_greeting", True)
        
        # 检查是否是唤醒词
        is_wakeup = _is_wakeup_word(text, wakeup_words)
        
        if is_wakeup:
            await self._handle_wakeup(conn, text, enable_greeting)
        else:
            await self._handle_normal_text(conn, text, msg_json)

    async def _handle_wakeup(self, conn, text: str, enable_greeting: bool) -> None:
        """处理唤醒词"""
        if not enable_greeting:
            # 关闭了唤醒词回复，只发送识别结果
            await send_stt_message(conn, text)
            await send_tts_message(conn, "stop", None)
            conn.client_is_speaking = False
            return
        
        # 尝试播放缓存的唤醒词短回复
        _, clean_text = remove_punctuation_and_length(text)
        wakeup_handled = await checkWakeupWords(conn, clean_text)
        
        if wakeup_handled:
            # 成功播放缓存回复
            enqueue_asr_report(conn, text, [])
            conn.logger.bind(tag=TAG).info("唤醒词已通过缓存短回复处理")
        else:
            # 缓存未命中，使用 LLM 回复
            conn.just_woken_up = True
            enqueue_asr_report(conn, text, [])
            await startToChat(conn, "嘿，你好呀")

    async def _handle_normal_text(self, conn, text: str, msg_json: Dict[str, Any]) -> None:
        """处理普通文字消息"""
        attachments = msg_json.get("attachments", [])
        
        conn.just_woken_up = True
        enqueue_asr_report(conn, text, [])
        
        if attachments:
            # 多模态消息（带图片/文件）
            multimodal_content = _build_multimodal_content(text, attachments)
            await startToChat(conn, text, multimodal_content)
        else:
            # 纯文字消息
            await startToChat(conn, text)

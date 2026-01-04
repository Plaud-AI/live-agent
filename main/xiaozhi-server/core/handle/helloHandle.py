import time
import json
import random
import asyncio
import uuid
import hashlib
import json as _json
from core.utils.dialogue import Message
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType, TTSMessageDTO, ContentType
from core.utils.wakeup_word import WakeupWordsConfig
from core.handle.sendAudioHandle import sendAudioMessage, send_tts_message
from core.utils.util import remove_punctuation_and_length, opus_datas_to_wav_bytes
from core.providers.tools.device_mcp import (
    MCPClient,
    send_mcp_initialize_message,
    send_mcp_tools_list_request,
)

TAG = __name__

WAKEUP_CONFIG = {
    "refresh_time": 10,
    # 冷启动/预热时优先生成该短句（更短 => 生成更快，首唤醒更稳）
    "default_text": "我在这里哦！",
    "responses": [
        "我一直都在呢，您请说。",
        "在的呢，请随时吩咐我。",
        "来啦来啦，请告诉我吧。",
        "您请说，我正听着。",
        "请您讲话，我准备好了。",
        "请您说出指令吧。",
        "我认真听着呢，请讲。",
        "请问您需要什么帮助？",
        "我在这里，等候您的指令。",
    ],
}

# 创建全局的唤醒词配置管理器
wakeup_words_config = WakeupWordsConfig()

# 用于防止并发调用wakeupWordsResponse的锁
_wakeup_response_lock = asyncio.Lock()


def _get_agent_greeting(conn) -> str | None:
    """
    获取 agent 配置的唤醒词回复（voice_opening）。
    
    Returns:
        agent 配置的 voice_opening 文本，或 None
    """
    greeting_config = getattr(conn, "_greeting_config", None)
    if greeting_config:
        return greeting_config.get("voice_opening")
    return None


def get_tts_voice_key(tts) -> str:
    """
    为唤醒词缓存生成稳定的 voice_key（跨不同 TTS provider 统一）。
    优先级：
      1) tts.voice（OpenAI/Minimax/Huoshan 等）
      2) tts.voice_id（ElevenLabs/Cartesia 等）
      3) tts.reference_id（FishSingleStreamTTS 等）
      4) tts.voice_embedding（Cartesia embedding 模式）→ 做一次哈希避免超长 key
    """
    if tts is None:
        return "default"

    voice = getattr(tts, "voice", None)
    if voice:
        return str(voice)

    voice_id = getattr(tts, "voice_id", None)
    if voice_id:
        return str(voice_id)

    reference_id = getattr(tts, "reference_id", None)
    if reference_id:
        return str(reference_id)

    voice_embedding = getattr(tts, "voice_embedding", None)
    if voice_embedding is not None:
        try:
            payload = _json.dumps(voice_embedding, sort_keys=True, ensure_ascii=False)
        except Exception:
            payload = str(voice_embedding)
        return f"embedding:{hashlib.md5(payload.encode('utf-8')).hexdigest()}"

    return "default"


async def prewarm_wakeup_reply_cache(conn) -> None:
    """
    后台预热生成唤醒短回复缓存，尽量让“首唤醒”直接命中本地 wav（低时延）。
    - 不阻塞主流程
    - 仅在 enable_greeting + enable_wakeup_words_response_cache 开启时执行
    """
    try:
        if not getattr(conn, "tts", None):
            return
        if not conn.config.get("enable_greeting", True):
            return
        if not conn.config.get("enable_wakeup_words_response_cache", False):
            return

        # Fish 在 agent voice 未解析前 reference_id 可能为空：此时不预热，避免生成到 default key
        if hasattr(conn.tts, "reference_id") and not getattr(conn.tts, "reference_id", None):
            return

        voice_key = get_tts_voice_key(conn.tts)
        if not voice_key:
            return

        existing = wakeup_words_config.get_wakeup_response(voice_key)
        if existing and existing.get("file_path"):
            return

        # 预热唤醒词回复缓存（使用 agent 配置的 voice_opening）
        if not _wakeup_response_lock.locked():
            asyncio.create_task(wakeupWordsResponse(conn))
    except Exception as e:
        # 预热失败不影响主流程
        try:
            conn.logger.bind(tag=TAG).debug(f"wakeup prewarm skipped: {e}")
        except Exception:
            pass


async def handleHelloMessage(conn, msg_json):
    """处理hello消息"""
    audio_params = msg_json.get("audio_params")
    if audio_params:
        format = audio_params.get("format")
        conn.logger.bind(tag=TAG).info(f"客户端音频格式: {format}")
        conn.audio_format = format
        conn.welcome_msg["audio_params"] = audio_params
    features = msg_json.get("features")
    if features:
        conn.logger.bind(tag=TAG).info(f"客户端特性: {features}")
        conn.features = features
        if features.get("mcp"):
            conn.logger.bind(tag=TAG).info("客户端支持MCP")
            conn.mcp_client = MCPClient()
            # 发送初始化
            asyncio.create_task(send_mcp_initialize_message(conn))
            # 发送mcp消息，获取tools列表
            asyncio.create_task(send_mcp_tools_list_request(conn))

    await conn.websocket.send(json.dumps(conn.welcome_msg))


async def checkWakeupWords(conn, text):
    enable_wakeup_words_response_cache = conn.config[
        "enable_wakeup_words_response_cache"
    ]

    # Fast path: if not a wakeup word, return early (avoid waiting for TTS init).
    # Use a normalized matcher to tolerate mixed-case wake words (e.g. "OKay那不").
    from core.utils.wakeup_suppression import is_wakeup_word
    if not is_wakeup_word(text, conn.config.get("wakeup_words", [])):
        return False

    # Optimization: after wakeup, the next user query should respond ASAP.
    # Skip TurnDetection ONCE for the first ASR turn after wakeup to remove TD HTTP RTT
    # and endpoint delay from the critical path.
    conn._skip_turn_detection_once = True

    # Drop the first ASR result after wakeup unconditionally.
    # The wakeup word audio is sent to ASR and transcribed (e.g., "Okinaabu", "OK南部"),
    # but it's not a real user query - just discard it.
    # CRITICAL: Set this BEFORE any await point to avoid race condition with ASR processing.
    conn._drop_first_asr_after_wakeup = True
    conn.just_woken_up = True

    # 等待tts初始化，最多等待3秒
    start_time = time.time()
    while time.time() - start_time < 3:
        if conn.tts:
            break
        await asyncio.sleep(0.1)
    else:
        return False
    # 注意：sendAudioMessage 也可能会在首句补发 tts/start。
    # 这里既然显式发送了 tts/start，就必须同步更新 client_is_speaking，
    # 否则会出现你日志里看到的 "tts/start 发送两次"，设备端可能会重置播放状态导致无声/卡顿。
    await send_tts_message(conn, "start")
    conn.client_is_speaking = True
    
    # 重置打断检测的连续帧计数器（行业最佳实践）
    conn._interrupt_consecutive_high_prob_frames = 0

    # 获取当前音色标识（用于唤醒缓存分桶）
    voice_key = get_tts_voice_key(conn.tts)

    # 获取唤醒词回复配置
    response = None
    if enable_wakeup_words_response_cache:
        response = wakeup_words_config.get_wakeup_response(voice_key)

    # 缓存命中：直接播放缓存的音频
    # 缓存未命中或缓存关闭：走 TTS 管线播放 voice_opening
    if not response or not response.get("file_path"):
        # 优先使用 agent 配置的 voice_opening，回退到默认配置
        wakeup_text = _get_agent_greeting(conn) or WAKEUP_CONFIG.get("default_text", "我在这里哦！")
        
        # 尝试走 TTS 管线播放（使用正确的 agent 配置音色）
        if hasattr(conn.tts, "tts_text_queue"):
            try:
                # 后台生成本地 wav 缓存（下次唤醒可直接秒回）
                if enable_wakeup_words_response_cache and not _wakeup_response_lock.locked():
                    asyncio.create_task(wakeupWordsResponse(conn))

                conn.logger.bind(tag=TAG).info(
                    f"唤醒词缓存未命中(voice_key={voice_key}), 使用TTS播放voice_opening"
                )
                conn.client_abort = False
                wakeup_sentence_id = str(uuid.uuid4().hex)
                # FIRST: start session
                conn.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=wakeup_sentence_id,
                        sentence_type=SentenceType.FIRST,
                        content_type=ContentType.ACTION,
                    )
                )
                # MIDDLE: text
                conn.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=str(uuid.uuid4().hex),
                        sentence_type=SentenceType.MIDDLE,
                        content_type=ContentType.TEXT,
                        content_detail=wakeup_text,
                    )
                )
                # LAST: end session
                conn.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=wakeup_sentence_id,
                        sentence_type=SentenceType.LAST,
                        content_type=ContentType.ACTION,
                    )
                )

                # 补充对话（用于上报/上下文一致性）
                conn.dialogue.put(Message(role="assistant", content=wakeup_text))
                return True
            except Exception as e:
                conn.logger.bind(tag=TAG).warning(f"TTS唤醒短句播报失败，回退到固定录音: {e}")
        
        # TTS 不可用时回退到固定录音
        response = {
            "voice": "default",
            "file_path": "config/assets/wakeup_words_short.wav",
            "time": 0,
            "text": wakeup_text,
        }

    try:
        # 获取音频数据：必须跟随设备端声明的音频格式（opus/pcm），否则会出现“服务端在发但设备播不出来”
        # conn.audio_format 由 hello 消息的 audio_params.format 填充（见 handleHelloMessage）
        is_opus = getattr(conn, "audio_format", "opus") != "pcm"
        audio_packets = audio_to_data(response.get("file_path"), is_opus=is_opus)

        # 播放唤醒词回复
        conn.client_abort = False

        conn.logger.bind(tag=TAG).info(f"播放唤醒词回复: {response.get('text')}")
        await sendAudioMessage(
            conn, SentenceType.FIRST, audio_packets, response.get("text")
        )
        await sendAudioMessage(conn, SentenceType.LAST, [], None)
    except Exception as e:
        # 保底恢复 speaking 状态，避免后续对话轮次被错误状态污染
        conn.logger.bind(tag=TAG).error(f"播放唤醒词回复失败: {e}")
        conn.client_is_speaking = False
        try:
            await send_tts_message(conn, "stop", None)
        except Exception:
            pass
        return False

    # 补充对话
    conn.dialogue.put(Message(role="assistant", content=response.get("text")))

    # 检查是否需要更新唤醒词回复
    if enable_wakeup_words_response_cache and time.time() - response.get("time", 0) > WAKEUP_CONFIG["refresh_time"]:
        if not _wakeup_response_lock.locked():
            asyncio.create_task(wakeupWordsResponse(conn))
    return True


async def wakeupWordsResponse(conn):
    """
    生成唤醒词回复的 TTS 缓存。
    
    优先级：
    1. Agent 配置的 voice_opening
    2. 从默认回复列表随机选择
    """
    if not conn.tts:
        return

    try:
        # 尝试获取锁，如果获取不到就返回
        if not await _wakeup_response_lock.acquire():
            return

        # Fish 在 agent voice 未解析前 reference_id 可能为空：此时不生成，避免污染 default key
        if hasattr(conn.tts, "reference_id") and not getattr(conn.tts, "reference_id", None):
            return

        # 优先使用 agent 配置的 voice_opening，回退到随机默认回复
        result = _get_agent_greeting(conn) or random.choice(WAKEUP_CONFIG["responses"])
        if not result or len(result) == 0:
            return

        # 生成TTS音频
        tts_result = await asyncio.to_thread(conn.tts.to_tts, result)
        if not tts_result:
            return

        # 获取当前音色标识
        voice_key = get_tts_voice_key(conn.tts)
        if not voice_key:
            voice_key = "default"

        wav_bytes = opus_datas_to_wav_bytes(tts_result, sample_rate=16000)
        file_path = wakeup_words_config.generate_file_path(voice_key)
        with open(file_path, "wb") as f:
            f.write(wav_bytes)
        # 更新配置
        wakeup_words_config.update_wakeup_response(voice_key, file_path, result)
    finally:
        # 确保在任何情况下都释放锁
        if _wakeup_response_lock.locked():
            _wakeup_response_lock.release()

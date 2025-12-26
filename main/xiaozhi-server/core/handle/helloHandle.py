import time
import json
import random
import asyncio
from core.utils.dialogue import Message
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
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
    _, filtered_text = remove_punctuation_and_length(text)
    if filtered_text not in conn.config.get("wakeup_words"):
        return False

    # Optimization: after wakeup, the next user query should respond ASAP.
    # Skip TurnDetection ONCE for the first ASR turn after wakeup to remove TD HTTP RTT
    # and endpoint delay from the critical path.
    conn._skip_turn_detection_once = True

    # 等待tts初始化，最多等待3秒
    start_time = time.time()
    while time.time() - start_time < 3:
        if conn.tts:
            break
        await asyncio.sleep(0.1)
    else:
        return False

    if not enable_wakeup_words_response_cache:
        # 选项1：即使关闭“缓存唤醒回复”，也不走 LLM，而是播放默认的短回复音频
        # 这样能保证唤醒“秒回”，且避免进入对话生成链路。
        pass

    conn.just_woken_up = True
    # 抑制“唤醒词残留音频”被 ASR/TurnDetection 再次触发一轮 chat（double-trigger）
    # 只在短窗口内生效，避免误伤后续真实提问。
    conn._wakeup_suppress_next_asr_until_ms = int(time.time() * 1000) + 5000
    # 注意：sendAudioMessage 也可能会在首句补发 tts/start。
    # 这里既然显式发送了 tts/start，就必须同步更新 client_is_speaking，
    # 否则会出现你日志里看到的 “tts/start 发送两次”，设备端可能会重置播放状态导致无声/卡顿。
    await send_tts_message(conn, "start")
    conn.client_is_speaking = True

    # 获取当前音色
    voice = getattr(conn.tts, "voice", "default")
    if not voice:
        voice = "default"

    # 获取唤醒词回复配置
    response = None
    if enable_wakeup_words_response_cache:
        response = wakeup_words_config.get_wakeup_response(voice)
    if not response or not response.get("file_path"):
        # 默认短回复（本地资源），不依赖网络与模型
        response = {
            "voice": "default",
            "file_path": "config/assets/wakeup_words_short.wav",
            "time": 0,
            "text": "我在这里哦！",
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
    if not conn.tts:
        return

    try:
        # 尝试获取锁，如果获取不到就返回
        if not await _wakeup_response_lock.acquire():
            return

        # 从预定义回复列表中随机选择一个回复
        result = random.choice(WAKEUP_CONFIG["responses"])
        if not result or len(result) == 0:
            return

        # 生成TTS音频
        tts_result = await asyncio.to_thread(conn.tts.to_tts, result)
        if not tts_result:
            return

        # 获取当前音色
        voice = getattr(conn.tts, "voice", "default")

        wav_bytes = opus_datas_to_wav_bytes(tts_result, sample_rate=16000)
        file_path = wakeup_words_config.generate_file_path(voice)
        with open(file_path, "wb") as f:
            f.write(wav_bytes)
        # 更新配置
        wakeup_words_config.update_wakeup_response(voice, file_path, result)
    finally:
        # 确保在任何情况下都释放锁
        if _wakeup_response_lock.locked():
            _wakeup_response_lock.release()

import json
import time
import asyncio
from core.utils import textUtils
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import (
    SentenceType,
    MessageTag,
)
from core.utils.textUtils import strip_emotion_tags, get_emotion_tag
from core.utils.opus import pack_opus_with_header
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

async def sendAudioMessage(conn, sentenceType, audios, text, message_tag=MessageTag.NORMAL):
    # 详细日志追踪
    audio_len = len(audios) if audios else 0
    
    # 在新句子开始或会话结束前，先发送前一个句子的 sentence_end
    # 这确保 sentence_end 在该句子的所有音频发送完毕后才发送
    if sentenceType in (SentenceType.FIRST, SentenceType.LAST):
        if hasattr(conn, '_pending_sentence_text') and conn._pending_sentence_text:
            await send_tts_message(conn, "sentence_end", conn._pending_sentence_text, message_tag)
            conn._pending_sentence_text = None

    # IMPORTANT: streaming TTS 会先发 FIRST(仅文本, audio_data=None) 再产出音频(MIDDLE)。
    # 如果在 FIRST(无音频) 时就发送 tts/start，设备端会进入“等待音频”状态，
    # 一旦首包音频因网络/TTS首包延迟而超过设备阈值，就会关闭播放通道 → 用户无声（必现/偶现取决于阈值与抖动）。
    # 因此：FIRST(无音频) 只缓存 sentence_start 文本，等到“首个非空音频包”到来时再发送 tts/start + sentence_start + 音频。
    has_audio = bool(audios)
    if sentenceType == SentenceType.FIRST and not has_audio:
        if text:
            # 记录待发送的 sentence_start（等首音频到来时再发，确保 start→audio 间隙极小）
            conn._tts_pending_sentence_start_text = text
            conn._tts_pending_sentence_start_message_tag = message_tag
            # 记录待发送的 sentence_end（下一句开始/会话结束时发送）
            conn._pending_sentence_text = text
        return

    async def _ensure_tts_session_started_before_audio(_log_text: str | None):
        """确保在发送任何音频前，tts/start 已发送且设备已完成状态切换。"""
        # 只有当 client_is_speaking 为 False 时才发送 tts/start
        # 如果 wakeup/其他路径已发送过 tts/start，此时 client_is_speaking 已为 True
        if not conn.client_is_speaking:
            await send_tts_message(conn, "start", None, message_tag)
            conn.client_is_speaking = True

            # 等待设备端完成状态切换（Schedule 异步切换）
            # 硬件约束：设备端需要 ~134ms 完成 Schedule callback + AudioService 操作
            # 150ms 是经过验证的安全值，不可随意降低
            tts_start_delay = conn.config.get("tts_start_delay_ms", 150) / 1000.0
            # 防御性编程：负值 clamp 到 0
            if tts_start_delay < 0:
                tts_start_delay = 0
            if tts_start_delay > 0:
                conn.logger.bind(tag=TAG).debug(f"⏳ 等待设备状态切换: {tts_start_delay*1000:.0f}ms")
                await asyncio.sleep(tts_start_delay)

        # 仅在“首个音频包”到来时做一次会话级流控重置与延迟打点
        if hasattr(conn, "tts") and getattr(conn.tts, "tts_audio_first_sentence", False):
            conn.tts.tts_audio_first_sentence = False

            # 在整个 TTS 会话开始时重置流控（而不是每个句子开始时）
            if hasattr(conn, "audio_flow_control"):
                conn.audio_flow_control["start_time"] = time.perf_counter()
                conn.audio_flow_control["packet_count"] = 0
                conn.audio_flow_control["last_send_time"] = 0
                conn.logger.bind(tag=TAG).debug("重置音频流控状态 (TTS会话开始)")

            # 记录首句 TTS 播放时间（端到端延迟的终点）
            first_audio_time = time.time() * 1000

            # 计算 TTS 首包延迟（输入到输出）
            tts_first_package_delay = 0
            if hasattr(conn, "_latency_tts_first_text_time") and conn._latency_tts_first_text_time:
                tts_first_package_delay = first_audio_time - conn._latency_tts_first_text_time

            # 计算端到端延迟
            e2e_total_delay = 0
            if hasattr(conn, "_latency_voice_end_time"):
                e2e_total_delay = first_audio_time - conn._latency_voice_end_time

            conn.logger.bind(tag=TAG).info(
                f"🔊 [延迟追踪] 首句TTS开始播放 | "
                f"TTS首包延迟: {tts_first_package_delay:.0f}ms | "
                f"⏱️  端到端总延迟: {e2e_total_delay:.0f}ms (用户说完→首句播放) | "
                f"文本: {_log_text if _log_text else '(无文本)'}"
            )
    
    if sentenceType == SentenceType.FIRST:
        # FIRST 且有音频：在发送音频前确保会话已启动（start→audio 间隙仅剩 tts_start_delay_ms）
        await _ensure_tts_session_started_before_audio(text)
        await send_tts_message(conn, "sentence_start", text, message_tag)
        # 保存当前句子的文本，等待该句子的音频发送完毕后再发送 sentence_end
        conn._pending_sentence_text = text if text else None
        # 清理可能存在的“延迟发送 sentence_start”缓存
        if hasattr(conn, "_tts_pending_sentence_start_text"):
            conn._tts_pending_sentence_start_text = None
        if hasattr(conn, "_tts_pending_sentence_start_message_tag"):
            conn._tts_pending_sentence_start_message_tag = None

    # MIDDLE(音频) 且存在待发送 sentence_start：先补发 sentence_start，再下发音频
    if sentenceType == SentenceType.MIDDLE and has_audio:
        pending_start_text = getattr(conn, "_tts_pending_sentence_start_text", None)
        if pending_start_text:
            pending_tag = getattr(conn, "_tts_pending_sentence_start_message_tag", message_tag)
            # 确保 tts/start 在 sentence_start 之前
            await _ensure_tts_session_started_before_audio(pending_start_text)
            await send_tts_message(conn, "sentence_start", pending_start_text, pending_tag)
            # 保存当前句子的文本，等待该句子的音频发送完毕后再发送 sentence_end
            conn._pending_sentence_text = pending_start_text
            conn._tts_pending_sentence_start_text = None
            conn._tts_pending_sentence_start_message_tag = None
        else:
            # 没有 sentence_start 文本（异常/兼容场景），但仍需确保 start 在首音频前
            if not conn.client_is_speaking:
                await _ensure_tts_session_started_before_audio(None)

    await sendAudio(conn, audios, message_tag=message_tag)
    
    # 发送句子开始消息
    if sentenceType is not SentenceType.MIDDLE:
        conn.logger.bind(tag=TAG).info(f"发送音频消息: {sentenceType}, {text}")

    # 发送结束消息（如果是最后一个文本）
    if sentenceType == SentenceType.LAST:
        await send_tts_message(conn, "stop", None, message_tag)
        conn.client_is_speaking = False
        if conn.close_after_chat:
            await conn.close()


def calculate_timestamp_and_sequence(conn, start_time, packet_index, frame_duration=60):
    """
    计算音频数据包的时间戳和序列号
    Args:
        conn: 连接对象
        start_time: 起始时间（性能计数器值）
        packet_index: 数据包索引
        frame_duration: 帧时长（毫秒），匹配 Opus 编码
    Returns:
        tuple: (timestamp, sequence)
    """
    # 计算时间戳（使用播放位置计算）
    timestamp = int((start_time + packet_index * frame_duration / 1000) * 1000) % (
        2**32
    )

    # 计算序列号
    if hasattr(conn, "audio_flow_control"):
        sequence = conn.audio_flow_control["sequence"]
    else:
        sequence = packet_index  # 如果没有流控状态，直接使用索引

    return timestamp, sequence


async def _send_to_mqtt_gateway(conn, opus_packet, timestamp, sequence):
    """
    发送带16字节头部的opus数据包给mqtt_gateway
    Args:
        conn: 连接对象
        opus_packet: opus数据包
        timestamp: 时间戳
        sequence: 序列号
    """
    # 为opus数据包添加16字节头部
    header = bytearray(16)
    header[0] = 1  # type
    header[2:4] = len(opus_packet).to_bytes(2, "big")  # payload length
    header[4:8] = sequence.to_bytes(4, "big")  # sequence
    header[8:12] = timestamp.to_bytes(4, "big")  # 时间戳
    header[12:16] = len(opus_packet).to_bytes(4, "big")  # opus长度

    # 发送包含头部的完整数据包
    complete_packet = bytes(header) + opus_packet
    await conn.websocket.send(complete_packet)

async def _send_audio_with_header(conn, audios, message_tag=MessageTag.NORMAL):
    if audios is None or len(audios) == 0:
        return
    # 统一发送带 16 字节头部的音频包
    # 非官方服务器的设备端（is_official_server_=false）期望带头部的数据
    # 头部格式：type(1) + message_tag(1) + payload_size(4, big-endian) + reserved(10) = 16 bytes
    complete_packet = pack_opus_with_header(audios, message_tag)
    # conn.logger.bind(tag=TAG).debug(f"📤 发送音频包: {len(complete_packet)} bytes (opus={len(audios)}, with header)")
    await conn.websocket.send(complete_packet)
    # 确保数据立即发送到网络（避免 asyncio 调度延迟导致缓冲区积压）
    # websockets 库的 send() 内部会等待 drain，但在高频发送时可能需要显式让出控制权
    # 使用 sleep(0) 让事件循环有机会处理 I/O
    await asyncio.sleep(0)


# 播放音频
async def sendAudio(conn, audios, frame_duration=60, message_tag=MessageTag.NORMAL):
    """
    发送单个opus包，支持流控
    Args:
        conn: 连接对象
        opus_packet: 单个opus数据包
        pre_buffer: 快速发送音频
        frame_duration: 帧时长（毫秒），匹配 Opus 编码
    """
    if audios is None or len(audios) == 0:
        return

    # 获取发送延迟配置
    send_delay = conn.config.get("tts_audio_send_delay", -1) / 1000.0

    if isinstance(audios, bytes):
        if conn.client_abort:
            conn.logger.bind(tag=TAG).debug(f"⚠️ client_abort=True, 跳过音频发送")
            return

        conn.last_activity_time = time.time() * 1000

        # 获取或初始化流控状态
        if not hasattr(conn, "audio_flow_control"):
            conn.audio_flow_control = {
                "last_send_time": 0,
                "packet_count": 0,
                "start_time": time.perf_counter(),
                "sequence": 0,  # 添加序列号
            }

        flow_control = conn.audio_flow_control
        current_time = time.perf_counter()
        
        # 每 20 个包记录一次流控状态
        if flow_control["packet_count"] % 20 == 0:
            conn.logger.bind(tag=TAG).debug(
                f"📊 流控状态: packet_count={flow_control['packet_count']}, "
                f"elapsed={current_time - flow_control['start_time']:.2f}s"
            )
        
        # 流控配置
        pre_buffer_count = conn.config.get("tts_audio_pre_buffer_count", 8)  # 预缓冲包数（约480ms）
        speed_multiplier = conn.config.get("tts_audio_speed_multiplier", 1.0)  # 发送速度倍率
        
        # 最小发送间隔（毫秒）- 避免数据突发导致设备端缓冲区溢出
        min_send_interval_ms = conn.config.get("tts_audio_min_send_interval_ms", 5)
        
        if send_delay > 0:
            # 使用固定延迟
            await asyncio.sleep(send_delay)
        elif flow_control["packet_count"] < pre_buffer_count:
            # 预缓冲阶段：快速发送，但仍需要最小间隔避免突发
            if min_send_interval_ms > 0 and flow_control["packet_count"] > 0:
                await asyncio.sleep(min_send_interval_ms / 1000.0)
        else:
            # 按略快于实时的速度发送
            packets_after_prebuffer = flow_control["packet_count"] - pre_buffer_count
            expected_time = flow_control["start_time"] + (
                packets_after_prebuffer * frame_duration / 1000 / speed_multiplier
            )
            delay = expected_time - current_time
            if delay > 0:
                await asyncio.sleep(delay)
            else:
                # 纠正误差
                flow_control["start_time"] += abs(delay)

        if conn.conn_from_mqtt_gateway:
            # 计算时间戳和序列号
            timestamp, sequence = calculate_timestamp_and_sequence(
                conn,
                flow_control["start_time"],
                flow_control["packet_count"],
                frame_duration,
            )
            # 调用通用函数发送带头部的数据包
            await _send_to_mqtt_gateway(conn, audios, timestamp, sequence)
        else:
            # 直接发送opus数据包，不添加头部
            await _send_audio_with_header(conn, audios, message_tag)

        # 更新流控状态
        flow_control["packet_count"] += 1
        flow_control["sequence"] += 1
        flow_control["last_send_time"] = time.perf_counter()
    else:
        # 文件型音频走普通播放
        start_time = time.perf_counter()
        play_position = 0

        # 执行预缓冲
        pre_buffer_frames = min(3, len(audios))
        for i in range(pre_buffer_frames):
            if conn.conn_from_mqtt_gateway:
                # 计算时间戳和序列号
                timestamp, sequence = calculate_timestamp_and_sequence(
                    conn, start_time, i, frame_duration
                )
                # 调用通用函数发送带头部的数据包
                await _send_to_mqtt_gateway(conn, audios[i], timestamp, sequence)
            else:
                # 直接发送预缓冲包，不添加头部
                await _send_audio_with_header(conn, audios[i], message_tag)
        remaining_audios = audios[pre_buffer_frames:]

        # 播放剩余音频帧
        for i, opus_packet in enumerate(remaining_audios):
            if conn.client_abort:
                break

            # 重置没有声音的状态
            conn.last_activity_time = time.time() * 1000

            if send_delay > 0:
                # 固定延迟模式
                await asyncio.sleep(send_delay)
            else:
                 # 计算预期发送时间
                expected_time = start_time + (play_position / 1000)
                current_time = time.perf_counter()
                delay = expected_time - current_time
                if delay > 0:
                    await asyncio.sleep(delay)

            if conn.conn_from_mqtt_gateway:
                # 计算时间戳和序列号（使用当前的数据包索引确保连续性）
                packet_index = pre_buffer_frames + i
                timestamp, sequence = calculate_timestamp_and_sequence(
                    conn, start_time, packet_index, frame_duration
                )
                # 调用通用函数发送带头部的数据包
                await _send_to_mqtt_gateway(conn, opus_packet, timestamp, sequence)
            else:
                # 直接发送opus数据包，不添加头部
                await _send_audio_with_header(conn, opus_packet, message_tag)

            play_position += frame_duration


async def send_tts_message(conn, state, text=None, message_tag=MessageTag.NORMAL):
    """发送 TTS 状态消息
    
    Args:
        conn: Connection object
        state: TTS state (start, sentence_start, stop)
        text: Optional text content
        message_tag: Message tag for categorization
    """
    if text is None and state == "sentence_start":
        return
    
    message = {
        "type": "tts", 
        "state": state,
        "session_id": conn.session_id,
        "message_tag": message_tag.value,
    }
    
    # TTS 开始时添加 sample_rate 参数（官方协议要求）
    if state == "start":
        # 从配置中获取 TTS 的 sample_rate，默认 16000
        tts_sample_rate = conn.config.get("xiaozhi", {}).get("audio_params", {}).get("sample_rate", 16000)
        message["sample_rate"] = tts_sample_rate
    
    if text is not None:
        text = textUtils.check_emoji(text)
        # Extract emotion tag before stripping
        emotion = get_emotion_tag(text)
        if emotion:
            message["emotion"] = emotion
        text = strip_emotion_tags(text)
        message["text"] = text

    # TTS播放结束
    if state == "stop":
        # 首轮对话完成，启用打断检测
        if not getattr(conn, "first_dialogue_completed", False):
            conn.first_dialogue_completed = True
            logger.bind(tag=TAG).info("首轮对话完成，启用打断检测")
        # 播放提示音
        tts_notify = conn.config.get("enable_stop_tts_notify", False)
        if tts_notify:
            stop_tts_notify_voice = conn.config.get(
                "stop_tts_notify_voice", "config/assets/tts_notify.mp3"
            )
            audios = audio_to_data(stop_tts_notify_voice, is_opus=True)
            await sendAudio(conn, audios)
        # 清除服务端讲话状态
        conn.clearSpeakStatus()

    # 发送消息到客户端
    logger.bind(tag=TAG).info(f"发送TTS消息: {message}")
    await conn.websocket.send(json.dumps(message))
    # 确保消息立即发送到网络（避免 TCP 缓冲区积压）
    await asyncio.sleep(0)


async def send_stt_message(conn, text):
    """发送 STT 状态消息（仅发送用户识别文本，不启动 TTS 会话）
    
    修复说明（2025-12-27）:
    之前此函数会提前发送 tts start 来"预热"设备，但这导致了问题：
    - tts start 发送后，设备进入等待音频状态
    - LLM 生成 + TTS 合成需要 1-2 秒
    - 设备等待超时（通常 1-2 秒阈值），关闭播放通道
    - 后续音频到达时被丢弃，用户听不到回复
    
    修复方案：
    - 此函数只发送 STT 文本消息（用于 UI 显示用户说了什么）
    - tts start 由 sendAudioMessage 在首帧音频准备好时发送
    - 确保 tts start 与音频数据紧密衔接，消除超时间隙
    
    注意：此函数在同一对话轮次中只应被调用一次。
    如果 client_is_speaking 已为 True，说明本轮对话已开始，
    此时再次调用是重复的（可能由于 wake word 音频被误识别导致）。
    """
    # 防止重复发送：如果已经在 speaking 状态，说明本轮对话的 stt 已经发送过了
    if conn.client_is_speaking:
        logger.bind(tag=TAG).warning(
            f"跳过重复的 stt 消息发送：已在 speaking 状态 (text: {text[:50] if text else ''}...)"
        )
        return
    
    # end_prompt 是特殊场景：用户说"再见"等结束语时，只需启动 TTS 播放告别语
    end_prompt_str = conn.config.get("end_prompt", {}).get("prompt")
    if end_prompt_str and end_prompt_str == text:
        await send_tts_message(conn, "start")
        return

    # 解析JSON格式，提取实际的用户说话内容
    display_text = text
    try:
        # 尝试解析JSON格式
        if text.strip().startswith("{") and text.strip().endswith("}"):
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "content" in parsed_data:
                # 如果是包含说话人信息的JSON格式，只显示content部分
                display_text = parsed_data["content"]
                # 保存说话人信息到conn对象
                if "speaker" in parsed_data:
                    conn.current_speaker = parsed_data["speaker"]
    except (json.JSONDecodeError, TypeError):
        # 如果不是JSON格式，直接使用原始文本
        display_text = text
    stt_text = textUtils.get_string_no_punctuation_or_emoji(display_text)
    
    # 只发送 STT 文本消息（用于设备端 UI 显示用户说了什么）
    # 不再发送 tts start，也不设置 client_is_speaking
    # tts start 将由 sendAudioMessage 在首帧音频到达时发送
    await conn.websocket.send(
        json.dumps({"type": "stt", "text": stt_text, "session_id": conn.session_id})
    )
    # 确保消息立即发送到网络
    await asyncio.sleep(0)
    logger.bind(tag=TAG).info(f"发送STT消息: {stt_text}")

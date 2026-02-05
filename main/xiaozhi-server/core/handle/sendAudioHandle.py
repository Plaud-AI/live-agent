import json
import time
import asyncio
from core.utils import textUtils
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
from core.utils.audioRateController import AudioRateController

TAG = __name__
# 音频帧时长（毫秒）
AUDIO_FRAME_DURATION = 60
# 预缓冲包数量，直接发送以减少延迟
PRE_BUFFER_COUNT = 5


async def sendAudioMessage(conn, sentenceType, audios, text):
    # 安全地获取音频大小
    try:
        if isinstance(audios, bytes):
            audio_size = len(audios)
        elif isinstance(audios, list):
            audio_size = sum(len(a) for a in audios if isinstance(a, bytes))
        else:
            audio_size = 'N/A'
    except Exception:
        audio_size = 'N/A'
    
    # 安全地记录日志
    if hasattr(conn, 'logger') and conn.logger:
        conn.logger.bind(tag=TAG).debug(
            f"sendAudioMessage: 开始处理, sentenceType={sentenceType}, "
            f"audio_size={audio_size}, text={text[:30] if text else 'None'}..."
        )
    
    if conn.tts.tts_audio_first_sentence:
        if hasattr(conn, 'logger') and conn.logger:
            conn.logger.bind(tag=TAG).info(f"发送第一段语音: {text}")
        conn.tts.tts_audio_first_sentence = False
        await send_tts_message(conn, "start", None)

    if sentenceType == SentenceType.FIRST:
        # 同一句子的后续消息加入流控队列，其他情况立即发送
        if (
            hasattr(conn, "audio_rate_controller")
            and conn.audio_rate_controller
            and getattr(conn, "audio_flow_control", {}).get("sentence_id")
            == conn.sentence_id
        ):
            conn.audio_rate_controller.add_message(
                lambda: send_tts_message(conn, "sentence_start", text)
            )
        else:
            # 新句子或流控器未初始化，立即发送
            await send_tts_message(conn, "sentence_start", text)

    # 发送音频数据
    audio_count_before = getattr(conn, "_audio_sent_count", 0)
    await sendAudio(conn, audios)
    audio_count_after = getattr(conn, "_audio_sent_count", 0)
    
    if hasattr(conn, 'logger') and conn.logger:
        conn.logger.bind(tag=TAG).debug(
            f"sendAudioMessage: 音频发送完成, sentenceType={sentenceType}, "
            f"sent_packets={audio_count_after - audio_count_before}"
        )
    
    # 发送句子开始消息
    if sentenceType is not SentenceType.MIDDLE:
        if hasattr(conn, 'logger') and conn.logger:
            conn.logger.bind(tag=TAG).info(f"发送音频消息: {sentenceType}, {text}")

    # 发送结束消息（如果是最后一个文本）
    if sentenceType == SentenceType.LAST:
        await send_tts_message(conn, "stop", None)
        conn.client_is_speaking = False
        if conn.close_after_chat:
            await conn.close()


async def _wait_for_audio_completion(conn):
    """
    等待音频队列清空并等待预缓冲包播放完成

    Args:
        conn: 连接对象
    """
    if hasattr(conn, "audio_rate_controller") and conn.audio_rate_controller:
        rate_controller = conn.audio_rate_controller
        queue_size = len(rate_controller.queue) if rate_controller.queue else 0
        if hasattr(conn, 'logger') and conn.logger:
            conn.logger.bind(tag=TAG).debug(
                f"等待音频发送完成，队列中还有 {queue_size} 个包"
            )
        
        # 添加超时保护，避免永远等待导致 tts.state:stop 不发送
        try:
            await asyncio.wait_for(rate_controller.queue_empty_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            if hasattr(conn, 'logger') and conn.logger:
                conn.logger.bind(tag=TAG).warning(
                    f"等待音频队列清空超时（10s），强制继续，队列剩余: {len(rate_controller.queue) if rate_controller.queue else 0}"
                )

        # 等待预缓冲包播放完成
        # 前N个包直接发送，增加2个网络抖动包，需要额外等待它们在客户端播放完成
        frame_duration_ms = rate_controller.frame_duration
        pre_buffer_playback_time = (PRE_BUFFER_COUNT + 2) * frame_duration_ms / 1000.0
        await asyncio.sleep(pre_buffer_playback_time)

        if hasattr(conn, 'logger') and conn.logger:
            conn.logger.bind(tag=TAG).debug("音频发送完成")


async def sendAudio(conn, audios, frame_duration=AUDIO_FRAME_DURATION):
    """
    发送音频包，使用 AudioRateController 进行精确的流量控制

    Args:
        conn: 连接对象
        audios: 单个opus包(bytes) 或 opus包列表
        frame_duration: 帧时长（毫秒），默认使用全局常量AUDIO_FRAME_DURATION
    """
    # 安全地检查音频数据
    if audios is None:
        if hasattr(conn, 'logger') and conn.logger:
            conn.logger.bind(tag=TAG).debug("sendAudio: 音频数据为 None，跳过发送")
        return
    
    try:
        if isinstance(audios, bytes):
            if len(audios) == 0:
                if hasattr(conn, 'logger') and conn.logger:
                    conn.logger.bind(tag=TAG).debug("sendAudio: 音频数据为空 bytes，跳过发送")
                return
            is_single_packet = True
            audio_size = len(audios)
            audio_count = 1
        elif isinstance(audios, list):
            if len(audios) == 0:
                if hasattr(conn, 'logger') and conn.logger:
                    conn.logger.bind(tag=TAG).debug("sendAudio: 音频数据为空列表，跳过发送")
                return
            is_single_packet = False
            audio_size = sum(len(a) for a in audios if isinstance(a, bytes))
            audio_count = len(audios)
        else:
            if hasattr(conn, 'logger') and conn.logger:
                conn.logger.bind(tag=TAG).warning(f"sendAudio: 音频数据类型不支持: {type(audios)}")
            return
    except Exception as e:
        if hasattr(conn, 'logger') and conn.logger:
            conn.logger.bind(tag=TAG).error(f"sendAudio: 检查音频数据时出错: {e}")
        return
    
    if hasattr(conn, 'logger') and conn.logger:
        conn.logger.bind(tag=TAG).debug(
            f"sendAudio: 开始发送音频, is_single_packet={is_single_packet}, "
            f"audio_count={audio_count}, total_size={audio_size} bytes"
        )

    send_delay = conn.config.get("tts_audio_send_delay", -1) / 1000.0

    # 初始化或获取 RateController
    rate_controller, flow_control = _get_or_create_rate_controller(
        conn, frame_duration, is_single_packet
    )

    # 统一转换为列表处理
    audio_list = [audios] if is_single_packet else audios

    # 发送音频包
    await _send_audio_with_rate_control(
        conn, audio_list, rate_controller, flow_control, send_delay
    )
    
    # 更新发送计数
    if not hasattr(conn, "_audio_sent_count"):
        conn._audio_sent_count = 0
    conn._audio_sent_count += audio_count
    
    if hasattr(conn, 'logger') and conn.logger:
        conn.logger.bind(tag=TAG).debug(
            f"sendAudio: 音频发送完成, sent_count={audio_count}, "
            f"total_sent={conn._audio_sent_count}"
        )


def _get_or_create_rate_controller(conn, frame_duration, is_single_packet):
    """
    获取或创建 RateController 和 flow_control

    Args:
        conn: 连接对象
        frame_duration: 帧时长
        is_single_packet: 是否单包模式（True: TTS流式单包, False: 批量包）

    Returns:
        (rate_controller, flow_control)
    """
    # 判断是否需要重置：sentence_id 变化，或者控制器不存在
    current_sentence_id = getattr(conn, "audio_flow_control", {}).get("sentence_id")
    need_reset = (
        current_sentence_id != conn.sentence_id
        or not hasattr(conn, "audio_rate_controller")
    )

    if need_reset:
        # 创建或获取 rate_controller
        if not hasattr(conn, "audio_rate_controller"):
            conn.audio_rate_controller = AudioRateController(frame_duration)
        else:
            conn.audio_rate_controller.reset()

        # 初始化 flow_control
        conn.audio_flow_control = {
            "packet_count": 0,
            "sequence": 0,
            "sentence_id": conn.sentence_id,
        }

        # 启动后台发送循环
        _start_background_sender(
            conn, conn.audio_rate_controller, conn.audio_flow_control
        )

    return conn.audio_rate_controller, conn.audio_flow_control


def _start_background_sender(conn, rate_controller, flow_control):
    """
    启动后台发送循环任务

    Args:
        conn: 连接对象
        rate_controller: 速率控制器
        flow_control: 流控状态
    """

    async def send_callback(packet):
        # 检查是否应该中止
        if conn.client_abort:
            raise asyncio.CancelledError("客户端已中止")

        conn.last_activity_time = time.time() * 1000
        await _do_send_audio(conn, packet, flow_control)
        conn.client_is_speaking = True

    # 使用 start_sending 启动后台循环
    rate_controller.start_sending(send_callback)


async def _send_audio_with_rate_control(
    conn, audio_list, rate_controller, flow_control, send_delay
):
    """
    使用 rate_controller 发送音频包

    Args:
        conn: 连接对象
        audio_list: 音频包列表
        rate_controller: 速率控制器
        flow_control: 流控状态
        send_delay: 固定延迟（秒），-1表示使用动态流控
    """
    for packet in audio_list:
        if conn.client_abort:
            return

        conn.last_activity_time = time.time() * 1000

        # 预缓冲：前N个包直接发送
        if flow_control["packet_count"] < PRE_BUFFER_COUNT:
            await _do_send_audio(conn, packet, flow_control)
            conn.client_is_speaking = True
        elif send_delay > 0:
            # 固定延迟模式
            await asyncio.sleep(send_delay)
            await _do_send_audio(conn, packet, flow_control)
            conn.client_is_speaking = True
        else:
            # 动态流控模式：仅添加到队列，由后台循环负责发送
            rate_controller.add_audio(packet)


async def _do_send_audio(conn, opus_packet, flow_control):
    """
    执行实际的音频发送
    
    通过通道抽象层发送，自动适配不同通道类型：
    - WebSocket 直连：纯 Opus 数据
    - MQTT 网关：16 字节头部 + Opus 数据
    """
    packet_index = flow_control.get("packet_count", 0)
    sequence = flow_control.get("sequence", 0)

    # 记录首音频播放时间（第一个包）
    if packet_index == 0:
        if hasattr(conn, 'latency_metrics') and conn.latency_metrics:
            conn.latency_metrics.mark_first_audio_play()
        if hasattr(conn, 'logger') and conn.logger:
            conn.logger.bind(tag=TAG).info(
                f"_do_send_audio: 发送首个音频包, size={len(opus_packet)} bytes, "
                f"sequence={sequence}"
            )

    try:
        send_start = time.time()
        timestamp = int(send_start * 1000) % (2**32)
        
        # 使用通道抽象层发送（自动适配协议差异）
        from core.channels import AudioPacket
        packet = AudioPacket(data=opus_packet, timestamp=timestamp, sequence=sequence)
        await conn.channel.send_audio(packet)
        
        if hasattr(conn, 'logger') and conn.logger:
            if packet_index % 10 == 0:
                conn.logger.bind(tag=TAG).info(
                    f"通道发送音频包 #{packet_index}: {len(opus_packet)} bytes, "
                    f"channel_type={conn.channel.channel_type}"
                )
            else:
                conn.logger.bind(tag=TAG).debug(
                    f"_do_send_audio: 通道发送 #{packet_index}, size={len(opus_packet)} bytes"
                )
        
        # 记录发送耗时，超过100ms时警告
        send_duration = (time.time() - send_start) * 1000
        if send_duration > 100:
            if hasattr(conn, 'logger') and conn.logger:
                conn.logger.bind(tag=TAG).warning(
                    f"_do_send_audio: 发送耗时过长 {send_duration:.1f}ms, "
                    f"packet_index={packet_index}"
                )
    except Exception as e:
        if hasattr(conn, 'logger') and conn.logger:
            conn.logger.bind(tag=TAG).error(
                f"_do_send_audio: 发送音频包失败, packet_index={packet_index}, "
                f"size={len(opus_packet)} bytes, error={e}"
            )
        raise

    # 更新流控状态
    flow_control["packet_count"] = packet_index + 1
    flow_control["sequence"] = sequence + 1


async def send_tts_message(conn, state, text=None):
    """发送 TTS 状态消息
    
    注意：sentence_start 消息的 text 可以为空（流式 TTS 时 FIRST 消息还不知道具体文本）
    客户端应该能处理没有 text 的 sentence_start 消息
    """
    start_time = time.time()
    message = {"type": "tts", "state": state, "session_id": conn.session_id}
    if text is not None:
        message["text"] = textUtils.check_emoji(text)

    # TTS播放结束
    if state == "stop":
        # 播放提示音
        tts_notify = conn.config.get("enable_stop_tts_notify", False)
        if tts_notify:
            stop_tts_notify_voice = conn.config.get(
                "stop_tts_notify_voice", "config/assets/tts_notify.mp3"
            )
            audios = await audio_to_data(stop_tts_notify_voice, is_opus=True)
            await sendAudio(conn, audios)
        # 等待所有音频包发送完成
        await _wait_for_audio_completion(conn)
        # 清除服务端讲话状态
        conn.clearSpeakStatus()

    # 发送消息到客户端
    msg_json = json.dumps(message)
    send_start = time.time()
    await conn.channel.send_text(msg_json)
    send_end = time.time()
    
    # 记录详细的延迟信息
    if hasattr(conn, 'logger') and conn.logger:
        total_ms = (send_end - start_time) * 1000
        send_ms = (send_end - send_start) * 1000
        conn.logger.bind(tag=TAG).info(
            f"发送TTS消息: state={state}, total={total_ms:.1f}ms, send={send_ms:.1f}ms, "
            f"text={text[:30] if text else 'None'}..."
        )


async def send_stt_message(conn, text):
    """发送 STT 状态消息"""
    end_prompt_str = conn.config.get("end_prompt", {}).get("prompt")
    if end_prompt_str and end_prompt_str == text:
        await send_tts_message(conn, "start")
        # 标记已发送 start，避免 sendAudioMessage 中重复发送
        if hasattr(conn, 'tts') and conn.tts:
            conn.tts.tts_audio_first_sentence = False
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
    stt_message = json.dumps({"type": "stt", "text": stt_text, "session_id": conn.session_id})
    
    # 发送 STT 消息
    await conn.channel.send_text(stt_message)
    await send_tts_message(conn, "start")
    # 标记已发送 start，避免 sendAudioMessage 中重复发送
    if hasattr(conn, 'tts') and conn.tts:
        conn.tts.tts_audio_first_sentence = False

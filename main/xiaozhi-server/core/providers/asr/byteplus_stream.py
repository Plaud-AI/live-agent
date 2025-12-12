import json
import gzip
import uuid
import asyncio
import time
import websockets
import opuslib_next
from core.providers.asr.base import ASRProviderBase
from config.logger import setup_logging
from core.providers.asr.dto.dto import InterfaceType

TAG = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__()
        self.interface_type = InterfaceType.STREAM
        self.config = config
        self.text = ""
        self.max_retries = 3
        self.retry_delay = 2
        self.decoder = opuslib_next.Decoder(16000, 1)
        self.asr_ws = None
        self.forward_task = None
        self.is_processing = False  # 添加处理状态标志
        self._connection_lock = asyncio.Lock()  # 防止并发连接竞态
        self._result_event = asyncio.Event()  # 等待 ASR 结果的事件
        self._ws_initialized_event = asyncio.Event()  # WS完成初始化(已发init且收init响应)
        self._audio_ended = False  # 标记是否已发送音频结束信号
        self._pending_stop = False  # stop 早于 WS init 完成，避免竞态提前结束
        self._session_active = False  # 标记当前会话是否正在进行（防止重复建连）
        # 注意：definite 并不等于“整段最终文本”（长语音可能分多段 definite），因此不能据此停止发送音频
        self._definite_texts: list[str] = []  # 已确认片段（用于 WS 提前关闭时兜底）
        self._definite_seen: set[str] = set()
        self._end_sent_at = None  # monotonic time when last-audio(end) sent; for tail-grace waiting

        # 配置参数
        self.appid = str(config.get("appid"))
        self.access_token = config.get("access_token")
        # 建连/初始化期间的音频缓存帧数（60ms/帧），用于覆盖网络抖动/WS建连耗时，避免丢开头
        self.preconnect_audio_cache_frames = int(config.get("preconnect_audio_cache_frames", 80))
        self.output_dir = config.get("output_dir", "tmp/")
        self.delete_audio_file = delete_audio_file

        # BytePlus ASR 配置 (海外版)
        self.ws_url = "wss://voice.ap-southeast-1.bytepluses.com/api/v3/sauc/bigmodel_nostream"
        self.uid = config.get("uid", "streaming_asr_service")
        self.result_type = config.get("result_type", "single")
        self.format = config.get("format", "pcm")
        self.codec = config.get("codec", "pcm")
        self.rate = config.get("sample_rate", 16000)
        self.language = config.get("language", "")  # 留空支持中英粤自动识别
        self.bits = config.get("bits", 16)
        self.channel = config.get("channel", 1)

    async def open_audio_channels(self, conn):
        await super().open_audio_channels(conn)

    async def receive_audio(self, conn, audio, audio_have_voice):
        # 与 ASRProviderBase 对齐：manual 模式不依赖 VAD
        if getattr(conn, "client_listen_mode", "auto") in ("auto", "realtime"):
            have_voice = audio_have_voice
        else:
            have_voice = getattr(conn, "client_have_voice", False)

        # b"" 由 listen stop 注入用于触发收尾，不属于音频内容
        if audio:
            conn.asr_audio.append(audio)
            conn.asr_audio = conn.asr_audio[-self.preconnect_audio_cache_frames:]

        # 存储音频数据
        if not hasattr(conn, 'asr_audio_for_voiceprint'):
            conn.asr_audio_for_voiceprint = []
        if audio:
            conn.asr_audio_for_voiceprint.append(audio)

        # 当没有音频数据(b"")时处理完整语音片段
        if not audio and len(conn.asr_audio_for_voiceprint) > 0:
            # stop 可能在 WS connect/init 过程中到达：不能提前进入 handle_voice_stop（会导致 0ms/空文本）
            self._pending_stop = True

            # 调试日志：stop 时的状态
            logger.bind(tag=TAG).info(
                f"Stop received - asr_ws: {self.asr_ws is not None}, "
                f"is_processing: {self.is_processing}, "
                f"ws_initialized: {self._ws_initialized_event.is_set()}, "
                f"session_active: {self._session_active}, "
                f"definite_texts: {len(self._definite_texts)}"
            )

            # WS 尚未初始化完毕：直接返回，由建连逻辑在 init 完成后处理 stop
            if not (self.asr_ws and self.is_processing and self._ws_initialized_event.is_set()):
                # WS 已经提前关闭或尚未完成初始化，但我们已经收到过 definite 片段：用片段兜底，避免"说了但没展示"
                if self._definite_texts:
                    self.text = "".join(self._definite_texts)
                    await self._finalize_without_last(conn)
                else:
                    # WS 未初始化且无 definite 文本：清理状态，警告用户
                    logger.bind(tag=TAG).warning(
                        "收到 stop 但 WS 未初始化且无识别结果，可能是说话时间过短或网络问题"
                    )
                    self._session_active = False
                    self._pending_stop = False
                    # 清理音频缓存
                    if hasattr(conn, "asr_audio_for_voiceprint"):
                        conn.asr_audio_for_voiceprint = []
                    if hasattr(conn, "asr_audio"):
                        conn.asr_audio = []
                    if hasattr(conn, "reset_vad_states"):
                        conn.reset_vad_states()
                return

            await self._finalize_utterance(conn)
            return

        # 避免 b"" 触发建连：listen stop 注入的空包仅用于收尾
        if not audio:
            return

        # 如果本次有声音，且之前没有建立连接，且当前会话未激活（防止重复建连）
        if have_voice and self.asr_ws is None and not self.is_processing and not self._session_active:
            # 使用锁防止并发连接竞态
            async with self._connection_lock:
                # 双重检查：获取锁后再次确认状态
                if self.asr_ws is not None or self.is_processing:
                    # 另一个协程已经建立了连接，直接返回发送音频
                    pass
                else:
                    try:
                        self.is_processing = True
                        self._session_active = True  # 标记会话开始，防止重复建连
                        self._ws_initialized_event.clear()
                        self._pending_stop = False
                        self._definite_texts = []
                        self._definite_seen = set()
                        # 建立新的WebSocket连接
                        headers = self.token_auth()
                        safe_headers = dict(headers)
                        if "X-Api-Access-Key" in safe_headers:
                            safe_headers["X-Api-Access-Key"] = "***"
                        logger.bind(tag=TAG).info(f"正在连接 BytePlus ASR 服务，headers: {safe_headers}")

                        self.asr_ws = await websockets.connect(
                            self.ws_url,
                            additional_headers=headers,
                            max_size=1000000000,
                            ping_interval=None,
                            ping_timeout=None,
                            close_timeout=10,
                        )

                        # 发送初始化请求
                        request_params = self.construct_request(str(uuid.uuid4()))
                        try:
                            payload_bytes = str.encode(json.dumps(request_params))
                            payload_bytes = gzip.compress(payload_bytes)
                            full_client_request = self.generate_header()
                            full_client_request.extend((len(payload_bytes)).to_bytes(4, "big"))
                            full_client_request.extend(payload_bytes)

                            # 初始化请求包含 token，日志必须脱敏
                            safe_request_params = json.loads(json.dumps(request_params))
                            if isinstance(safe_request_params, dict):
                                app = safe_request_params.get("app", {})
                                if isinstance(app, dict) and app.get("token"):
                                    app["token"] = "***"
                            logger.bind(tag=TAG).info(f"发送初始化请求: {safe_request_params}")
                            await self.asr_ws.send(full_client_request)

                            # 等待初始化响应
                            init_res = await self.asr_ws.recv()
                            result = self.parse_response(init_res)
                            logger.bind(tag=TAG).info(f"收到初始化响应: {result}")

                            # 检查初始化响应
                            if "code" in result and result["code"] != 1000:
                                error_msg = f"BytePlus ASR 服务初始化失败: {result.get('payload_msg', {}).get('error', '未知错误')}"
                                logger.bind(tag=TAG).error(error_msg)
                                raise Exception(error_msg)

                        except Exception as e:
                            logger.bind(tag=TAG).error(f"发送初始化请求失败: {str(e)}")
                            if hasattr(e, "__cause__") and e.__cause__:
                                logger.bind(tag=TAG).error(f"错误原因: {str(e.__cause__)}")
                            raise e

                        self._ws_initialized_event.set()
                        # 启动接收ASR结果的异步任务
                        self.forward_task = asyncio.create_task(self._forward_asr_results(conn))

                        # 发送缓存的音频数据
                        if conn.asr_audio and len(conn.asr_audio) > 0:
                            for cached_audio in conn.asr_audio[-10:]:
                                try:
                                    pcm_frame = self.decoder.decode(cached_audio, 960)
                                    payload = gzip.compress(pcm_frame)
                                    audio_request = bytearray(
                                        self.generate_audio_default_header()
                                    )
                                    audio_request.extend(len(payload).to_bytes(4, "big"))
                                    audio_request.extend(payload)
                                    await self.asr_ws.send(audio_request)
                                except Exception as e:
                                    logger.bind(tag=TAG).info(
                                        f"发送缓存音频数据时发生错误: {e}"
                                    )

                        # stop 在建连/初始化期间到达：init 完成后立刻收尾（避免竞态产生空结果）
                        if self._pending_stop:
                            await self._finalize_utterance(conn)
                            return
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"建立 BytePlus ASR 连接失败: {str(e)}")
                        if hasattr(e, "__cause__") and e.__cause__:
                            logger.bind(tag=TAG).error(f"错误原因: {str(e.__cause__)}")
                        if self.asr_ws:
                            await self.asr_ws.close()
                            self.asr_ws = None
                        self.is_processing = False
                        return

        # 发送当前音频数据
        if self.asr_ws and self.is_processing:
            try:
                if not audio:
                    return
                pcm_frame = self.decoder.decode(audio, 960)
                payload = gzip.compress(pcm_frame)
                audio_request = bytearray(self.generate_audio_default_header())
                audio_request.extend(len(payload).to_bytes(4, "big"))
                audio_request.extend(payload)
                await self.asr_ws.send(audio_request)
            except Exception as e:
                logger.bind(tag=TAG).info(f"发送音频数据时发生错误: {e}")

    async def _finalize_utterance(self, conn):
        """
        发送结束包并等待最终结果，然后触发基类 handle_voice_stop 进入对话流程。
        需要幂等，避免重复 stop 导致重复收尾/重复上报。
        """
        # 防止与建连竞态：收尾过程也需要串行化
        async with self._connection_lock:
            if not (self.asr_ws and self.is_processing and self._ws_initialized_event.is_set()):
                return
            if self._audio_ended:
                return

            try:
                self._result_event.clear()
                self._audio_ended = True
                self._end_sent_at = time.monotonic()

                # 关键修复：在发送结束信号前等待一段时间，让网络中的音频数据有机会到达 ASR
                # 这解决了流式 ASR 与非流式 ASR（如 Groq）的差异：
                # - 非流式：先缓存所有音频，stop 时批量发送
                # - 流式：边收边发，stop 时最后几帧可能还在网络中
                await asyncio.sleep(0.5)  # 等待 500ms 让网络音频帧到达

                empty_payload = gzip.compress(b"")
                last_audio_request = bytearray(self.generate_last_audio_default_header())
                last_audio_request.extend(len(empty_payload).to_bytes(4, "big"))
                last_audio_request.extend(empty_payload)
                await self.asr_ws.send(last_audio_request)
                logger.bind(tag=TAG).info("发送音频结束信号，等待识别结果...")

                try:
                    await asyncio.wait_for(self._result_event.wait(), timeout=10.0)
                    logger.bind(tag=TAG).info(f"收到识别结果: {self.text}")
                except asyncio.TimeoutError:
                    logger.bind(tag=TAG).warning("等待 ASR 结果超时")
            except Exception as e:
                logger.bind(tag=TAG).error(f"发送音频结束信号失败: {e}")
            finally:
                self._audio_ended = False
                self._pending_stop = False
                self._end_sent_at = None
                self._session_active = False  # 会话结束，允许下次建连

        audio_data = getattr(conn, "asr_audio_for_voiceprint", [])
        if audio_data:
            await self.handle_voice_stop(conn, audio_data)
        if hasattr(conn, "asr_audio_for_voiceprint"):
            conn.asr_audio_for_voiceprint = []
        if hasattr(conn, "asr_audio"):
            conn.asr_audio = []
        # 关键：我们绕过了 ASRProviderBase.receive_audio() 的 reset 分支，必须手动重置
        if hasattr(conn, "reset_vad_states"):
            conn.reset_vad_states()

    async def _finalize_without_last(self, conn):
        """
        已经收到 definite 文本的场景：直接触发下游处理，不再发送 last packet。
        目的是避免在 WS 已关闭/重连时把文本覆盖为空。
        """
        audio_data = getattr(conn, "asr_audio_for_voiceprint", [])
        if audio_data:
            await self.handle_voice_stop(conn, audio_data)
        if hasattr(conn, "asr_audio_for_voiceprint"):
            conn.asr_audio_for_voiceprint = []
        if hasattr(conn, "asr_audio"):
            conn.asr_audio = []
        if hasattr(conn, "reset_vad_states"):
            conn.reset_vad_states()
        self._pending_stop = False
        self._session_active = False  # 会话结束，允许下次建连

    async def _forward_asr_results(self, conn):
        """接收 ASR 结果的长期运行任务"""
        exit_reason = "unknown"
        try:
            while True:
                # 详细检查退出条件
                if not self.asr_ws:
                    exit_reason = "asr_ws is None"
                    break
                if conn.stop_event.is_set():
                    exit_reason = "conn.stop_event is set"
                    break
                
                try:
                    # 添加超时，避免无限阻塞导致无法检测退出条件
                    response = await asyncio.wait_for(self.asr_ws.recv(), timeout=5.0)
                    result = self.parse_response(response)
                    duration = 0
                    
                    if "payload_msg" in result:
                        payload = result["payload_msg"]
                        duration = payload.get("audio_info", {}).get("duration", 0)
                        
                        # 检查是否是错误码1013（无有效语音）
                        if "code" in payload and payload["code"] == 1013:
                            if self._audio_ended:
                                self._result_event.set()  # 通知等待方
                            continue

                        if "result" in payload:
                            utterances = payload["result"].get("utterances", [])
                            text_result = payload["result"].get("text", "")
                            
                            # 收集 definite 片段（长语音可能多段 definite）
                            for utterance in utterances:
                                if utterance.get("definite", False):
                                    utext = utterance.get("text", "")
                                    if not utext:
                                        continue
                                    # 用文本去重（BytePlus 可能重复推送相同 definite）
                                    if utext not in self._definite_seen:
                                        self._definite_seen.add(utext)
                                        self._definite_texts.append(utext)
                                        self.text = "".join(self._definite_texts)
                                        logger.bind(tag=TAG).info(f"识别到文本(utterance): {utext}")
                            
                            # 只有在发送结束信号后才处理最终结果
                            if self._audio_ended:
                                # BytePlus 的 text 字段可能只包含最后一个片段，不是完整结果
                                # 所以我们用已收集的 definite_texts（包含所有片段）作为主要结果
                                # 只有当 text 比 definite_texts 更长时才使用 text
                                if text_result:
                                    definite_combined = "".join(self._definite_texts)
                                    # 选择更完整的结果
                                    if len(text_result) > len(definite_combined):
                                        self.text = text_result
                                        logger.bind(tag=TAG).info(f"识别到最终文本(text优先): {self.text}")
                                    else:
                                        self.text = definite_combined
                                        logger.bind(tag=TAG).info(f"识别到最终文本(definite优先): {self.text}")
                                    exit_reason = "received final text result"
                                    self._result_event.set()
                                    return
                                
                                # 如果有 duration 但无 text：判断是否是"处理完毕"信号
                                # BytePlus 会在处理完所有音频后返回一个 duration>0 但无 text 的响应
                                if duration > 0 and not text_result:
                                    # 如果没有新的 utterances，说明可能是最终响应
                                    if not utterances:
                                        # 给一个宽限期等待可能的最终 text 结果
                                        grace_s = 2.0
                                        if self._end_sent_at is not None:
                                            waited = time.monotonic() - self._end_sent_at
                                            if waited < grace_s:
                                                logger.bind(tag=TAG).debug(
                                                    f"收到处理完成回包，继续等待最终文本: waited={waited:.2f}s, duration={duration}ms"
                                                )
                                                continue
                                        # 宽限期已过，使用已收集的 definite 片段作为结果
                                        if self._definite_texts:
                                            self.text = "".join(self._definite_texts)
                                            logger.bind(tag=TAG).info(f"使用 definite 片段作为最终结果: {self.text}")
                                            exit_reason = "grace period expired, using definite texts"
                                            self._result_event.set()
                                            return
                                        else:
                                            logger.bind(tag=TAG).warning(f"音频处理完成但无识别结果，duration={duration}ms")
                                            self.text = ""
                                            exit_reason = "no result after grace period"
                                            self._result_event.set()
                                            return
                                    # 有新的 utterances，继续循环收集
                                    continue
                            else:
                                # 发送结束信号前收到的响应，只记录日志
                                logger.bind(tag=TAG).debug(f"收到中间响应，duration={duration}ms，等待最终结果...")
                                
                        elif "error" in payload:
                            error_msg = payload.get("error", "未知错误")
                            logger.bind(tag=TAG).error(f"BytePlus ASR 服务返回错误: {error_msg}")
                            self._result_event.set()  # 通知等待方
                            break

                except asyncio.TimeoutError:
                    # recv 超时：继续循环检查退出条件
                    # 如果已经发送了结束信号但一直没收到结果，可能是服务端异常
                    if self._audio_ended:
                        if self._end_sent_at and time.monotonic() - self._end_sent_at > 8.0:
                            exit_reason = "recv timeout after audio_ended (8s)"
                            logger.bind(tag=TAG).warning("发送结束信号后 8 秒仍未收到结果，超时退出")
                            break
                    continue
                except websockets.ConnectionClosed as e:
                    exit_reason = f"websocket closed (code={e.code}, reason={e.reason})"
                    logger.bind(tag=TAG).info(f"BytePlus ASR 服务连接已关闭: {exit_reason}")
                    self._result_event.set()  # 通知等待方
                    break
                except Exception as e:
                    exit_reason = f"exception: {type(e).__name__}: {str(e)}"
                    logger.bind(tag=TAG).error(f"处理 ASR 结果时发生错误: {str(e)}")
                    if hasattr(e, "__cause__") and e.__cause__:
                        logger.bind(tag=TAG).error(f"错误原因: {str(e.__cause__)}")
                    self._result_event.set()  # 通知等待方
                    break

        except Exception as e:
            exit_reason = f"outer exception: {type(e).__name__}: {str(e)}"
            logger.bind(tag=TAG).error(f"ASR 结果转发任务发生错误: {str(e)}")
            if hasattr(e, "__cause__") and e.__cause__:
                logger.bind(tag=TAG).error(f"错误原因: {str(e.__cause__)}")
        finally:
            logger.bind(tag=TAG).info(
                f"_forward_asr_results 退出 - reason: {exit_reason}, "
                f"audio_ended: {self._audio_ended}, "
                f"definite_texts: {len(self._definite_texts)}"
            )
            self._result_event.set()  # 确保事件被设置
            if self.asr_ws:
                await self.asr_ws.close()
                self.asr_ws = None
            self.is_processing = False
            # 关键：意外退出时也要重置 session_active，否则无法重新建连
            # 但如果是正常结束（_finalize_utterance 调用后），已经在那里重置了
            # 这里仅作为兜底，防止状态泄漏
            if not self._audio_ended and exit_reason not in ("unknown",):
                logger.bind(tag=TAG).warning(
                    f"ASR 连接意外断开 (reason={exit_reason})，重置 session_active 以允许重连"
                )
                self._session_active = False

    def stop_ws_connection(self):
        if self.asr_ws:
            asyncio.create_task(self.asr_ws.close())
            self.asr_ws = None
        self.is_processing = False
        self._session_active = False  # 重置会话状态

    def construct_request(self, reqid):
        """构造 BytePlus ASR 请求参数（与 Doubao 不同，移除 cluster，使用 model_name）"""
        req = {
            "app": {
                "appid": self.appid,
                "token": self.access_token,
            },
            "user": {"uid": self.uid},
            "request": {
                "reqid": reqid,
                "model_name": "bigmodel",
                "show_utterances": True,
                "result_type": self.result_type,
                "sequence": 1,
                "end_window_size": 200,
            },
            "audio": {
                "format": self.format,
                "codec": self.codec,
                "rate": self.rate,
                "language": self.language,
                "bits": self.bits,
                "channel": self.channel,
                "sample_rate": self.rate,
            },
        }
        logger.bind(tag=TAG).debug(
            f"构造请求参数: {json.dumps(req, ensure_ascii=False)}"
        )
        return req

    def token_auth(self):
        """BytePlus 认证头"""
        return {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }

    def generate_header(
        self,
        version=0x01,
        message_type=0x01,
        message_type_specific_flags=0x00,
        serial_method=0x01,
        compression_type=0x01,
        reserved_data=0x00,
        extension_header: bytes = b"",
    ):
        header = bytearray()
        header_size = int(len(extension_header) / 4) + 1
        header.append((version << 4) | header_size)
        header.append((message_type << 4) | message_type_specific_flags)
        header.append((serial_method << 4) | compression_type)
        header.append(reserved_data)
        header.extend(extension_header)
        return header

    def generate_audio_default_header(self):
        return self.generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x00,
            serial_method=0x01,
            compression_type=0x01,
        )

    def generate_last_audio_default_header(self):
        return self.generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x02,
            serial_method=0x01,
            compression_type=0x01,
        )

    def parse_response(self, res: bytes) -> dict:
        try:
            # 检查响应长度
            if len(res) < 4:
                logger.bind(tag=TAG).error(f"响应数据长度不足: {len(res)}")
                return {"error": "响应数据长度不足"}

            # 获取消息头
            header = res[:4]
            message_type = header[1] >> 4

            # 如果是错误响应
            if message_type == 0x0F:  # SERVER_ERROR_RESPONSE
                code = int.from_bytes(res[4:8], "big", signed=False)
                msg_length = int.from_bytes(res[8:12], "big", signed=False)
                error_msg = json.loads(res[12:].decode("utf-8"))
                return {
                    "code": code,
                    "msg_length": msg_length,
                    "payload_msg": error_msg,
                }

            # 获取JSON数据（跳过12字节头部）
            try:
                json_data = res[12:].decode("utf-8")
                result = json.loads(json_data)
                logger.bind(tag=TAG).debug(f"成功解析JSON响应: {result}")
                return {"payload_msg": result}
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.bind(tag=TAG).error(f"JSON解析失败: {str(e)}")
                logger.bind(tag=TAG).error(f"原始数据: {res}")
                raise

        except Exception as e:
            logger.bind(tag=TAG).error(f"解析响应失败: {str(e)}")
            logger.bind(tag=TAG).error(f"原始响应数据: {res.hex()}")
            raise

    async def speech_to_text(self, opus_data, session_id, audio_format):
        result = self.text
        self.text = ""  # 清空text
        return result, None

    async def close(self):
        """资源清理方法"""
        if self.asr_ws:
            await self.asr_ws.close()
            self.asr_ws = None
        if self.forward_task:
            self.forward_task.cancel()
            try:
                await self.forward_task
            except asyncio.CancelledError:
                pass
            self.forward_task = None
        self.is_processing = False
        self._session_active = False  # 重置会话状态
        # 清理所有连接的音频缓冲区
        if hasattr(self, '_connections'):
            for conn in self._connections.values():
                if hasattr(conn, 'asr_audio_for_voiceprint'):
                    conn.asr_audio_for_voiceprint = []
                if hasattr(conn, 'asr_audio'):
                    conn.asr_audio = []
                if hasattr(conn, 'has_valid_voice'):
                    conn.has_valid_voice = False

import asyncio
import threading
import unittest
import sys
import types
from unittest.mock import AsyncMock, patch

# 本地开发环境可能未安装 requirements.txt 中的 opuslib_next；
# 这里提供最小 stub 以保证单测可运行（不影响生产环境使用真实依赖）。
if "opuslib_next" not in sys.modules:
    stub = types.ModuleType("opuslib_next")

    class _DummyDecoder:
        def __init__(self, *_args, **_kwargs):
            pass

        def decode(self, _data, frame_size):
            return b"\x00\x00" * frame_size

    stub.Decoder = _DummyDecoder
    stub.OpusError = Exception
    sys.modules["opuslib_next"] = stub

# Python 3.13 环境下 pydub 可能依赖 audioop/pyaudioop 导致 import 失败；
# 这里同样提供最小 stub，避免单测因环境差异无法运行。
if "pydub" not in sys.modules:
    pydub_stub = types.ModuleType("pydub")

    class _DummyAudioSegment:  # pragma: no cover
        pass

    pydub_stub.AudioSegment = _DummyAudioSegment
    sys.modules["pydub"] = pydub_stub

if "portalocker" not in sys.modules:
    portalocker_stub = types.ModuleType("portalocker")

    class _DummyLockException(Exception):  # pragma: no cover
        pass

    def _noop_lock(_file, _flags):  # pragma: no cover
        return

    def _noop_unlock(_file):  # pragma: no cover
        return

    portalocker_stub.lock = _noop_lock
    portalocker_stub.unlock = _noop_unlock
    portalocker_stub.LockException = _DummyLockException
    portalocker_stub.LOCK_EX = 1
    portalocker_stub.LOCK_NB = 2
    sys.modules["portalocker"] = portalocker_stub

from core.providers.asr.byteplus_stream import ASRProvider
from core.handle.receiveAudioHandle import (
    _trigger_pseudo_streaming_prefetch,
    PSEUDO_STREAM_BUFFER_THRESHOLD,
)
from core.providers.asr.dto.dto import InterfaceType


class _FakeWebSocket:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def send(self, data):
        self.sent.append(data)

    async def recv(self):
        # byteplus_stream.parse_response() 会从 res[12:] 解析 JSON
        return b"\x00" * 12 + b"{}"

    async def close(self):
        self.closed = True


class _DummyConn:
    def __init__(self):
        self.stop_event = threading.Event()
        self.client_listen_mode = "manual"
        self.client_have_voice = True
        self.asr_audio = []
        # asr_audio_for_voiceprint 由 provider 动态创建

        # base.handle_voice_stop 可能会访问这些字段（本测试会 mock 掉 handle_voice_stop）
        self.session_id = "test-session"
        self.audio_format = "opus"

    def reset_vad_states(self):
        # 某些 provider 会调用；这里提供空实现
        return


class TestBytePlusStreamASR(unittest.IsolatedAsyncioTestCase):
    async def test_pseudo_stream_prefetch_skips_when_asr_is_stream(self):
        """
        伪流式预取会在后台线程调用 conn.asr.speech_to_text()；
        对 STREAM ASR 这是“消费型”接口（会清空内部状态）且不一定支持离线识别。
        为稳定性，STREAM ASR 下预取应被跳过。
        """
        class _AsrStub:
            interface_type = InterfaceType.STREAM

            async def speech_to_text(self, *_args, **_kwargs):  # pragma: no cover
                raise AssertionError("STREAM ASR 下不应触发预取 speech_to_text()")

        class _MemoryStub:
            async def query_memory(self, _text):
                return "ok"

        conn = _DummyConn()
        conn.asr = _AsrStub()
        conn.memory = _MemoryStub()

        # 连续多帧触发阈值也不应创建预取任务
        for _ in range(PSEUDO_STREAM_BUFFER_THRESHOLD + 2):
            await _trigger_pseudo_streaming_prefetch(conn, b"frame", have_voice=True)

        self.assertFalse(hasattr(conn, "_prefetched_memory_task"))

    async def test_stop_during_connect_is_deferred_and_manual_mode_does_not_require_vad(self):
        provider = ASRProvider({"appid": "1", "access_token": "token"}, delete_audio_file=True)

        # 避免依赖真实 opus 解码
        provider.decoder.decode = lambda _data, frame_size: b"\x00\x00" * frame_size

        # forward task：等到发送 last audio 后立刻给出结果
        async def _fake_forward(_conn):
            while not provider._audio_ended:
                await asyncio.sleep(0)
            provider.text = "hello"
            provider._result_event.set()

        provider._forward_asr_results = AsyncMock(side_effect=_fake_forward)

        # 只验证“不会在 WS 未 init 完成时提前触发 handle_voice_stop”
        provider.handle_voice_stop = AsyncMock()

        fake_ws = _FakeWebSocket()
        connect_started = asyncio.Event()
        allow_connect = asyncio.Event()

        async def _fake_connect(*_args, **_kwargs):
            connect_started.set()
            await allow_connect.wait()
            return fake_ws

        conn = _DummyConn()

        with patch("core.providers.asr.byteplus_stream.websockets.connect", new=_fake_connect):
            # 这里 audio_have_voice=False，但 manual 模式应仍会建连（使用 client_have_voice）
            t_connect = asyncio.create_task(provider.receive_audio(conn, b"frame1", audio_have_voice=False))

            await connect_started.wait()

            # stop 在 connect/init 期间到达：不应立即进入 handle_voice_stop
            await provider.receive_audio(conn, b"", audio_have_voice=False)
            provider.handle_voice_stop.assert_not_awaited()
            self.assertTrue(provider._pending_stop)

            # 放行连接，确保后续能在 init 完成后收尾并触发 handle_voice_stop
            allow_connect.set()
            await t_connect

        provider.handle_voice_stop.assert_awaited_once()
        args, _kwargs = provider.handle_voice_stop.call_args
        self.assertIs(args[0], conn)
        self.assertEqual(args[1], [b"frame1"])

        # 确保发送过 init / 音频 / last 音频（数量不做严格约束）
        self.assertGreaterEqual(len(fake_ws.sent), 2)

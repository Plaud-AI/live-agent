import asyncio
import re
import time
from typing import TYPE_CHECKING
import httpx

from config.logger import setup_logging
from .base import TurnDetectionProviderBase, TurnDetectionState

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


class LocalTurnDetector:
    """本地轮次检测器 - 快速路径实现
    
    用于在调用远程服务之前，快速判断句子是否明显完整。
    对于明显完整的句子，可以跳过远程调用，节省 300-600ms 延迟。
    
    检测规则：
    1. 句末标点（。？！. ? !）→ 明显完整
    2. 常见结束语（好的、谢谢、OK 等）→ 明显完整
    3. 其他情况 → 需要远程检测
    """
    
    # 句末标点模式
    SENTENCE_END_PUNCTS = (
        '。', '？', '！',  # 中文
        '.', '?', '!',   # 英文
    )
    
    # 常见结束语（中文）- 精确匹配
    ENDING_PHRASES_ZH = (
        '好的', '好', '行', '可以', '没问题',
        '谢谢', '感谢', '多谢',
        '再见', '拜拜', '回头见',
        '知道了', '明白了', '了解',
        '就这样', '就这些', '没了', '没有了',
    )
    
    # 常见结束语（英文）- 精确匹配，忽略大小写
    ENDING_PHRASES_EN = (
        'ok', 'okay', 'yes', 'no', 'sure', 'alright',
        'thanks', 'thank you',
        'bye', 'goodbye',
        'got it', 'understood',
        "that's all", "that's it",
    )
    
    def __init__(self, enable_phrase_detection: bool = True):
        self.enable_phrase_detection = enable_phrase_detection
        # 编译正则表达式以提高性能
        self._ending_phrase_pattern_zh = re.compile(
            r'^(' + '|'.join(re.escape(p) for p in self.ENDING_PHRASES_ZH) + r')$'
        )
        self._ending_phrase_pattern_en = re.compile(
            r'^(' + '|'.join(re.escape(p) for p in self.ENDING_PHRASES_EN) + r')$',
            re.IGNORECASE
        )
    
    def is_obviously_complete(self, text: str) -> tuple[bool, str]:
        """检测句子是否明显完整
        
        Args:
            text: 待检测文本
            
        Returns:
            (is_complete, reason)
            - is_complete: 是否明显完整
            - reason: 判断原因（用于日志和监控）
        """
        if not text:
            return False, "empty_text"
        
        text = text.strip()
        if not text:
            return False, "whitespace_only"
        
        # 规则 1：以句末标点结尾
        if text.endswith(self.SENTENCE_END_PUNCTS):
            return True, "ends_with_punct"
        
        # 规则 2：常见结束语（精确匹配）
        if self.enable_phrase_detection:
            # 中文结束语
            if self._ending_phrase_pattern_zh.match(text):
                return True, "zh_ending_phrase"
            # 英文结束语
            if self._ending_phrase_pattern_en.match(text.lower()):
                return True, "en_ending_phrase"
        
        return False, "incomplete"


class TurnDetectionProvider(TurnDetectionProviderBase):
    """HTTP-based Turn Detection provider with local fast path
    
    Hybrid approach:
    1. Local fast path: For obviously complete sentences (punctuation, common phrases)
       - Latency: ~1ms (regex matching)
       - Skip remote call entirely
    2. Remote fallback: For uncertain cases
       - Latency: 300-700ms (HTTP round-trip)
    
    Implements endpoint delay mechanism:
    - First checks local fast path (new optimization)
    - If local says finished → use min_endpoint_delay
    - If local says incomplete → call remote service
    - If result is "finished", wait min_endpoint_delay
    - If result is "unfinished/waiting", wait max_endpoint_delay
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        host = config.get("host", "127.0.0.1")
        port = config.get("port", 8080)
        endpoint = config.get("endpoint", "/")
        
        self.url = f"http://{host}:{port}{endpoint}"
        self.timeout = float(config.get("timeout", 0.5))
        self._client = httpx.AsyncClient(timeout=self.timeout)
        
        # 本地快速路径配置
        self.enable_fast_path = config.get("enable_fast_path", True)
        self.enable_phrase_detection = config.get("enable_phrase_detection", True)
        self._local_detector = LocalTurnDetector(
            enable_phrase_detection=self.enable_phrase_detection
        )
        
        # 统计信息（用于监控快速路径命中率）
        self._fast_path_hits = 0
        self._remote_calls = 0
        
        logger.bind(tag=TAG).info(
            f"TenTurnDetection initialized: url={self.url}, timeout={self.timeout}s, "
            f"min_endpoint_delay={self.min_endpoint_delay}ms, max_endpoint_delay={self.max_endpoint_delay}ms, "
            f"fast_path={self.enable_fast_path}, phrase_detection={self.enable_phrase_detection}"
        )
    
    def _check_fast_path(self, text: str) -> tuple[bool, bool, str]:
        """本地快速路径检测
        
        Args:
            text: 待检测文本
            
        Returns:
            (should_use_fast_path, is_finished, reason)
            - should_use_fast_path: 是否使用快速路径（跳过远程调用）
            - is_finished: 如果使用快速路径，返回检测结果
            - reason: 判断原因（用于日志）
        """
        if not self.enable_fast_path:
            return False, False, "fast_path_disabled"
        
        start_time = time.perf_counter()
        is_complete, reason = self._local_detector.is_obviously_complete(text)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        if is_complete:
            self._fast_path_hits += 1
            logger.bind(tag=TAG).info(
                f"⚡ [FastPath] Hit: '{text[:50]}' | reason={reason} | "
                f"latency={elapsed_ms:.2f}ms | hits={self._fast_path_hits}"
            )
            return True, True, reason
        
        return False, False, reason
    
    async def _call_turn_detection(self, full_text: str) -> tuple[bool, str]:
        """Call Turn Detection HTTP service to get result
        
        Args:
            full_text: Accumulated text to check
            
        Returns:
            (is_finished, source)
            - is_finished: True if turn detection says finished
            - source: "fast_path" or "remote"
        """
        # Step 1: 尝试本地快速路径
        use_fast_path, is_finished, reason = self._check_fast_path(full_text)
        if use_fast_path:
            return is_finished, f"fast_path:{reason}"
        
        # Step 2: 调用远程服务
        self._remote_calls += 1
        start_time = time.perf_counter()
        
        try:
            response = await self._client.post(
                self.url,
                json={"text": full_text}
            )
            response.raise_for_status()
            data = response.json()
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.bind(tag=TAG).info(
                f"🔄 [Remote] TD response: {data} | latency={elapsed_ms:.0f}ms | "
                f"remote_calls={self._remote_calls}"
            )
            
            result_str = data.get("result", "finished")
            is_finished = result_str == TurnDetectionState.FINISHED.value
            
            logger.bind(tag=TAG).info(
                f"Turn detection result: {result_str}, text: '{full_text[:50]}'"
            )
            return is_finished, "remote"
            
        except httpx.TimeoutException:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.bind(tag=TAG).warning(
                f"TurnDetection timeout ({self.timeout}s), defaulting to finished | "
                f"latency={elapsed_ms:.0f}ms"
            )
            return True, "remote:timeout"
            
        except httpx.HTTPStatusError as e:
            logger.bind(tag=TAG).error(
                f"TurnDetection HTTP error: {e.response.status_code}, defaulting to finished"
            )
            return True, "remote:http_error"
            
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"TurnDetection error: {e}, defaulting to finished"
            )
            return True, "remote:error"

    async def _delayed_turn_detection_task(
        self,
        conn: "ConnectionHandler",
    ):
        """Task that calls turn detection, then waits for appropriate delay
        
        Flow:
        1. Cancel any pending memory task from previous turn
        2. Call turn detection service to get result
        3. If finished: start memory prefetch in parallel with delay wait
        4. Wait for the delay (memory prefetch runs in parallel)
        5. After delay completes, call on_end_of_turn
        
        Args:
            conn: Connection handler
            
        Returns:
            True if end of turn, False if cancelled
            
        Raises:
            asyncio.CancelledError: If cancelled by new speech
        """
        # Step 1: Cancel any pending memory task from previous turn
        if conn._memory_task is not None:
            if not conn._memory_task.done():
                conn._memory_task.cancel()
                logger.bind(tag=TAG).debug("Cancelled previous memory task")
            conn._memory_task = None
        
        full_text = conn.asr_text_buffer
        
        # Step 2: Call turn detection (with local fast path optimization)
        is_finished, source = await self._call_turn_detection(full_text)
        
        # Step 3: Calculate sleep time based on result
        sleep_time = self._calculate_sleep_time(conn, is_finished)
        
        # 记录延迟追踪日志
        logger.bind(tag=TAG).debug(
            f"🔍 [TD] source={source}, is_finished={is_finished}, sleep_time={sleep_time}ms"
        )
        
        # Step 4: Start memory prefetch in parallel (if finished and memory available)
        prefetch_start_time = time.perf_counter()
        if is_finished and conn.memory is not None:
            logger.bind(tag=TAG).debug(
                f"🧠 [Prefetch] Starting memory prefetch in parallel with delay: '{full_text[:50]}...'"
            )
            conn._memory_task = asyncio.create_task(
                self._prefetch_memory(conn, full_text)
            )
        
        # Step 5: Wait for the delay (memory prefetch runs in parallel)
        # 优化说明：prefetch 和 delay 是并行的，不是串行
        # - 如果 prefetch 在 delay 内完成，结果可直接使用
        # - 如果 prefetch 超过 delay，会被取消（但不阻塞主流程）
        if sleep_time > 0:
            await asyncio.sleep(sleep_time / 1000)  # Convert ms to seconds
        
        # Step 6: 检查 memory prefetch 状态
        prefetch_elapsed_ms = (time.perf_counter() - prefetch_start_time) * 1000
        if conn._memory_task is not None:
            if conn._memory_task.done():
                # Prefetch 在 delay 内完成
                if not conn._memory_task.cancelled():
                    try:
                        # 确保结果已存储（_prefetch_memory 内部会设置）
                        conn._memory_task.result()  # 触发异常检查
                        logger.bind(tag=TAG).info(
                            f"✅ [Prefetch] Memory prefetch completed within delay: {prefetch_elapsed_ms:.0f}ms"
                        )
                    except Exception as e:
                        logger.bind(tag=TAG).warning(f"⚠️ [Prefetch] Memory prefetch error: {e}")
            else:
                # Prefetch 超时，取消任务
                conn._memory_task.cancel()
                logger.bind(tag=TAG).info(
                    f"⏱️ [Prefetch] Memory prefetch timeout after {prefetch_elapsed_ms:.0f}ms, cancelled"
                )
            conn._memory_task = None
        
        # Step 7: After delay, trigger end of turn processing
        logger.bind(tag=TAG).info("Endpoint delay completed, triggering on_end_of_turn")
        await conn.on_end_of_turn()
    
    async def _prefetch_memory(self, conn: "ConnectionHandler", query: str) -> None:
        """Prefetch memory during endpoint delay
        
        Results are stored in conn._prefetched_memory_result for later use in chat().
        
        Args:
            conn: Connection handler with memory provider
            query: Full ASR text to query memory with
        """
        start_time = time.time()
        client_timezone = conn.client_timezone
        
        try:
            result = await conn.memory.query_memory(query, client_timezone=client_timezone)
            logger.bind(tag=TAG).debug(f"Memory result type: {type(result)}")
            conn.relevant_memories_this_turn = result
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.bind(tag=TAG).info(
                f"Memory prefetch done: {elapsed_ms:.0f}ms, len={len(result) if result else 0}"
            )
        except asyncio.TimeoutError:
            logger.bind(tag=TAG).warning("Memory prefetch timeout")
            conn.relevant_memories_this_turn = "No relevant memories retrieved for this turn."
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Memory prefetch error: {e}")
            conn.relevant_memories_this_turn = "No relevant memories retrieved for this turn."
    
    def check_end_of_turn(self, conn: "ConnectionHandler"):
        """Check if the user has finished their turn with endpoint delay mechanism
        
        Flow:
        1. Cancel any pending task from previous call
        2. Create a new task that:
           - Calls turn detection service
           - Waits min_endpoint_delay (if finished) or max_endpoint_delay (if unfinished)
           - Calls conn.on_end_of_turn() after delay
        
        Args:
            conn: Connection handler containing asr_text_buffer and _last_speaking_time
        """
        # Step 1: Cancel pending task
        self.cancel_pending_task()
        
        logger.bind(tag=TAG).debug(
            f"check_end_of_turn called: buffer='{conn.asr_text_buffer[:50]}...'"
        )
        
        # Step 2: Create the delayed task (don't await, let it run in background)
        self._turn_detection_task = asyncio.create_task(
            self._delayed_turn_detection_task(conn)
        )
        # Add callback to log exceptions (task may be cancelled, which is expected)
        self._turn_detection_task.add_done_callback(self._on_task_done)
    
    def _on_task_done(self, task: asyncio.Task):
        """Callback when turn detection task completes"""
        if task.cancelled():
            logger.bind(tag=TAG).debug("Turn detection task was cancelled")
            return
        exc = task.exception()
        if exc:
            logger.bind(tag=TAG).error(f"Turn detection task failed: {exc}")
    
    async def close(self) -> None:
        """Close the httpx client"""
        await super().close()
        await self._client.aclose()
        logger.bind(tag=TAG).debug("TenTurnDetection client closed")

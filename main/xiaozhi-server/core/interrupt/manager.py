"""
打断管理器 (InterruptManager)

核心类，负责协调各组件的打断操作。
参考 ten-framework 的设计，支持：
1. 分层打断（ASR、LLM、TTS 可独立打断）
2. 请求追踪（通过 request_id/flush_id）
3. 回调通知机制
4. 线程安全设计
"""

import asyncio
import threading
import logging
import time
import traceback
from typing import Dict, List, Optional, Set, Callable, Any, Union
from datetime import datetime
from contextlib import asynccontextmanager

from .types import (
    InterruptSource,
    InterruptTarget,
    InterruptReason,
    InterruptState,
    InterruptEvent,
    FlushRequest,
    RequestContext,
)
from .protocol import (
    Interruptible,
    InterruptCallback,
    InterruptCallbackFunc,
    QueueFlushable,
    TaskCancellable,
    InterruptNotifier,
)

# 模块级日志标签
TAG = "InterruptManager"


class InterruptManager:
    """
    打断管理器
    
    每个连接/会话应该创建一个 InterruptManager 实例。
    负责协调 ASR、LLM、TTS 等组件的打断操作。
    
    设计原则：
    1. 线程安全：使用锁保护共享状态
    2. 异步优先：核心方法都是异步的
    3. 可扩展：通过回调和事件支持扩展
    4. 易迁移：最小化外部依赖
    
    使用示例:
        # 创建管理器
        manager = InterruptManager(session_id="session_123")
        
        # 注册组件
        manager.register_target(InterruptTarget.TTS, tts_provider)
        manager.register_target(InterruptTarget.LLM, llm_handler)
        
        # 添加回调
        manager.add_callback(my_callback)
        
        # 触发打断
        event = await manager.interrupt(
            source=InterruptSource.VAD,
            targets=[InterruptTarget.TTS, InterruptTarget.LLM]
        )
        
        # 清理
        await manager.cleanup()
    """
    
    def __init__(
        self,
        session_id: str = "",
        logger: Optional[logging.Logger] = None,
        debug: bool = False,
    ):
        """
        初始化打断管理器
        
        Args:
            session_id: 会话 ID，用于追踪和日志
            logger: 可选的日志记录器
            debug: 是否启用详细调试日志
        """
        self.session_id = session_id
        self.logger = logger or logging.getLogger(__name__)
        self._debug = debug
        
        # 线程安全锁
        self._lock = threading.RLock()
        self._async_lock = asyncio.Lock()
        
        # 注册的可中断组件 {InterruptTarget: Interruptible}
        self._targets: Dict[InterruptTarget, Interruptible] = {}
        
        # 可清空队列的组件 {InterruptTarget: QueueFlushable}
        self._queues: Dict[InterruptTarget, QueueFlushable] = {}
        
        # 可取消任务的组件 {InterruptTarget: TaskCancellable}
        self._tasks: Dict[InterruptTarget, TaskCancellable] = {}
        
        # 通知器
        self._notifier: Optional[InterruptNotifier] = None
        
        # 回调函数列表
        self._callbacks: List[Union[InterruptCallback, InterruptCallbackFunc]] = []
        
        # 请求上下文追踪 {request_id: RequestContext}
        self._request_contexts: Dict[str, RequestContext] = {}
        
        # 当前活跃的 flush 请求 {flush_id: FlushRequest}
        self._active_flushes: Dict[str, FlushRequest] = {}
        
        # 被打断的请求 ID 集合（用于快速检查）
        self._interrupted_requests: Set[str] = set()
        
        # 打断历史（最近 N 条）
        self._interrupt_history: List[InterruptEvent] = []
        self._history_max_size = 100
        
        # 统计计数
        self._interrupt_count = 0
        self._interrupt_count_by_target: Dict[InterruptTarget, int] = {}
        
        # 状态标志
        self._is_interrupting = False
        self._is_closed = False
        
        self._log_info(f"InterruptManager 初始化完成: session_id={session_id}, debug={debug}")
    
    # ==================== 日志辅助方法 ====================
    
    def _log_debug(self, message: str) -> None:
        """记录调试日志"""
        if self._debug:
            if hasattr(self.logger, 'bind'):
                self.logger.bind(tag=TAG).debug(f"[{self.session_id[:8]}] {message}")
            else:
                self.logger.debug(f"[{TAG}][{self.session_id[:8]}] {message}")
    
    def _log_info(self, message: str) -> None:
        """记录信息日志"""
        if hasattr(self.logger, 'bind'):
            self.logger.bind(tag=TAG).info(f"[{self.session_id[:8]}] {message}")
        else:
            self.logger.info(f"[{TAG}][{self.session_id[:8]}] {message}")
    
    def _log_warning(self, message: str) -> None:
        """记录警告日志"""
        if hasattr(self.logger, 'bind'):
            self.logger.bind(tag=TAG).warning(f"[{self.session_id[:8]}] {message}")
        else:
            self.logger.warning(f"[{TAG}][{self.session_id[:8]}] {message}")
    
    def _log_error(self, message: str, exc_info: bool = False) -> None:
        """记录错误日志"""
        if hasattr(self.logger, 'bind'):
            self.logger.bind(tag=TAG).error(f"[{self.session_id[:8]}] {message}")
        else:
            self.logger.error(f"[{TAG}][{self.session_id[:8]}] {message}", exc_info=exc_info)
    
    # ==================== 组件注册 ====================
    
    def register_target(
        self,
        target: InterruptTarget,
        component: Interruptible,
        queue: Optional[QueueFlushable] = None,
        task: Optional[TaskCancellable] = None,
    ) -> None:
        """
        注册可中断组件
        
        Args:
            target: 组件对应的打断目标类型
            component: 实现 Interruptible 协议的组件
            queue: 可选的队列组件
            task: 可选的任务组件
        """
        with self._lock:
            self._targets[target] = component
            if queue:
                self._queues[target] = queue
            if task:
                self._tasks[target] = task
            
            # 详细日志
            component_type = type(component).__name__
            queue_type = type(queue).__name__ if queue else "None"
            task_type = type(task).__name__ if task else "None"
            self._log_info(
                f"注册组件: target={target.value}, "
                f"component={component_type}, queue={queue_type}, task={task_type}"
            )
            self._log_debug(f"当前已注册目标: {[t.value for t in self._targets.keys()]}")
    
    def unregister_target(self, target: InterruptTarget) -> None:
        """
        注销组件
        
        Args:
            target: 要注销的目标类型
        """
        with self._lock:
            removed = target in self._targets
            self._targets.pop(target, None)
            self._queues.pop(target, None)
            self._tasks.pop(target, None)
            
            if removed:
                self._log_info(f"注销组件: target={target.value}")
            else:
                self._log_warning(f"尝试注销不存在的组件: target={target.value}")
    
    def set_notifier(self, notifier: InterruptNotifier) -> None:
        """
        设置通知器
        
        Args:
            notifier: 实现 InterruptNotifier 协议的对象
        """
        self._notifier = notifier
        notifier_type = type(notifier).__name__
        self._log_info(f"设置通知器: {notifier_type}")
    
    # ==================== 回调管理 ====================
    
    def add_callback(
        self,
        callback: Union[InterruptCallback, InterruptCallbackFunc],
    ) -> None:
        """
        添加打断回调
        
        Args:
            callback: 回调函数或实现 InterruptCallback 协议的对象
        """
        with self._lock:
            self._callbacks.append(callback)
            callback_type = type(callback).__name__
            self._log_info(f"添加回调: {callback_type}, 当前回调数量: {len(self._callbacks)}")
    
    def remove_callback(
        self,
        callback: Union[InterruptCallback, InterruptCallbackFunc],
    ) -> None:
        """
        移除打断回调
        
        Args:
            callback: 要移除的回调
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
                callback_type = type(callback).__name__
                self._log_info(f"移除回调: {callback_type}")
            else:
                self._log_warning("尝试移除不存在的回调")
    
    async def _invoke_callbacks(
        self,
        event: InterruptEvent,
        phase: str = "complete",
        error: Optional[Exception] = None,
    ) -> None:
        """
        调用所有回调
        
        Args:
            event: 打断事件
            phase: 阶段（"start", "complete", "error"）
            error: 错误信息（仅在 error 阶段使用）
        """
        self._log_debug(f"调用回调: phase={phase}, 回调数量={len(self._callbacks)}")
        
        for i, callback in enumerate(self._callbacks):
            callback_type = type(callback).__name__
            try:
                if hasattr(callback, f"on_interrupt_{phase}"):
                    method = getattr(callback, f"on_interrupt_{phase}")
                    self._log_debug(f"执行回调 [{i}] {callback_type}.on_interrupt_{phase}")
                    if phase == "error":
                        await method(event, error)
                    else:
                        await method(event)
                elif callable(callback) and phase == "complete":
                    # 简单的函数回调
                    self._log_debug(f"执行函数回调 [{i}] {callback_type}")
                    await callback(event)
            except Exception as e:
                self._log_error(f"回调执行失败 [{i}] {callback_type}: {e}\n{traceback.format_exc()}")
    
    # ==================== 请求追踪 ====================
    
    def track_request(
        self,
        request_id: str,
        target: InterruptTarget,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RequestContext:
        """
        开始追踪一个请求
        
        Args:
            request_id: 请求 ID
            target: 请求所属的目标类型
            metadata: 可选的元数据
            
        Returns:
            RequestContext: 请求上下文
        """
        with self._lock:
            context = RequestContext(
                request_id=request_id,
                target=target,
                metadata=metadata or {},
            )
            self._request_contexts[request_id] = context
            self._log_debug(
                f"开始追踪请求: request_id={request_id[:16]}..., "
                f"target={target.value}, 当前追踪数量={len(self._request_contexts)}"
            )
            return context
    
    def get_request_context(self, request_id: str) -> Optional[RequestContext]:
        """
        获取请求上下文
        
        Args:
            request_id: 请求 ID
            
        Returns:
            RequestContext 或 None
        """
        with self._lock:
            context = self._request_contexts.get(request_id)
            if context:
                self._log_debug(f"获取请求上下文: request_id={request_id[:16]}..., state={context.state.value}")
            return context
    
    def is_request_interrupted(self, request_id: str) -> bool:
        """
        检查请求是否已被打断
        
        Args:
            request_id: 请求 ID
            
        Returns:
            bool: 是否已被打断
        """
        with self._lock:
            is_interrupted = request_id in self._interrupted_requests
            if is_interrupted:
                self._log_debug(f"请求已被打断: request_id={request_id[:16]}...")
            return is_interrupted
    
    def mark_request_processing(self, request_id: str) -> None:
        """
        标记请求为处理中
        
        Args:
            request_id: 请求 ID
        """
        with self._lock:
            context = self._request_contexts.get(request_id)
            if context:
                context.mark_processing()
                self._log_debug(f"请求标记为处理中: request_id={request_id[:16]}...")
            else:
                self._log_warning(f"尝试标记不存在的请求: request_id={request_id[:16]}...")
    
    def mark_request_completed(
        self,
        request_id: str,
        reason: InterruptReason = InterruptReason.REQUEST_END,
    ) -> None:
        """
        标记请求为已完成
        
        Args:
            request_id: 请求 ID
            reason: 完成原因
        """
        with self._lock:
            context = self._request_contexts.get(request_id)
            if context:
                context.mark_completed(reason)
                duration = context.duration_ms
                self._log_debug(
                    f"请求标记为已完成: request_id={request_id[:16]}..., "
                    f"reason={reason.name}, duration={duration}ms"
                )
            # 清理
            self._interrupted_requests.discard(request_id)
    
    # ==================== 核心打断方法 ====================
    
    async def interrupt(
        self,
        source: InterruptSource = InterruptSource.UNKNOWN,
        targets: Optional[List[InterruptTarget]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        notify_client: bool = True,
    ) -> InterruptEvent:
        """
        触发打断操作
        
        这是打断模块的核心方法，协调各组件的打断。
        
        Args:
            source: 打断触发源
            targets: 要打断的目标列表，默认为 ALL
            metadata: 附加的元数据
            notify_client: 是否通知客户端
            
        Returns:
            InterruptEvent: 打断事件（包含结果）
        """
        start_time = time.time()
        
        self._log_info(f"========== 开始打断 ==========")
        self._log_info(f"触发源: {source.value}")
        self._log_info(f"目标: {[t.value for t in targets] if targets else 'ALL'}")
        self._log_debug(f"元数据: {metadata}")
        self._log_debug(f"通知客户端: {notify_client}")
        
        if self._is_closed:
            self._log_warning("InterruptManager 已关闭，忽略打断请求")
            return InterruptEvent(
                session_id=self.session_id,
                source=source,
                success=False,
                error_message="Manager is closed",
            )
        
        # 确定打断目标
        if targets is None or InterruptTarget.ALL in targets:
            targets = [InterruptTarget.ASR, InterruptTarget.LLM, InterruptTarget.TTS, InterruptTarget.AUDIO_OUTPUT]
            self._log_debug(f"展开 ALL 目标为: {[t.value for t in targets]}")
        
        # 创建 Flush 请求
        flush_request = FlushRequest(
            metadata={
                "session_id": self.session_id,
                **(metadata or {}),
            }
        )
        self._log_info(f"创建 FlushRequest: flush_id={flush_request.flush_id[:16]}...")
        
        # 创建打断事件
        event = InterruptEvent(
            session_id=self.session_id,
            source=source,
            targets=targets,
            flush_request=flush_request,
            metadata=metadata or {},
        )
        self._log_debug(f"创建 InterruptEvent: event_id={event.event_id[:16]}...")
        
        async with self._async_lock:
            self._is_interrupting = True
            self._active_flushes[flush_request.flush_id] = flush_request
            self._log_debug("已获取异步锁，开始执行打断")
            
            try:
                # 通知回调：打断开始
                self._log_debug("触发 on_interrupt_start 回调")
                await self._invoke_callbacks(event, "start")
                
                # 执行打断
                self._log_info("开始执行打断操作...")
                interrupted_ids = await self._execute_interrupt(targets, flush_request)
                event.interrupted_request_ids = interrupted_ids
                self._log_info(f"打断操作完成，被打断的请求数量: {len(interrupted_ids)}")
                
                # 记录被打断的请求
                with self._lock:
                    self._interrupted_requests.update(interrupted_ids)
                    self._log_debug(f"更新被打断请求集合，当前数量: {len(self._interrupted_requests)}")
                
                # 通知客户端
                if notify_client and self._notifier:
                    self._log_debug("发送客户端通知...")
                    try:
                        await self._notifier.notify_interrupt(event)
                        self._log_info("客户端通知发送成功")
                    except Exception as e:
                        self._log_error(f"客户端通知发送失败: {e}")
                
                # 更新统计
                self._update_stats(event)
                
                # 通知回调：打断完成
                self._log_debug("触发 on_interrupt_complete 回调")
                await self._invoke_callbacks(event, "complete")
                
                elapsed_ms = (time.time() - start_time) * 1000
                self._log_info(
                    f"========== 打断完成 (耗时 {elapsed_ms:.2f}ms) ==========\n"
                    f"  触发源: {source.value}\n"
                    f"  目标: {[t.value for t in targets]}\n"
                    f"  被打断请求数: {len(interrupted_ids)}\n"
                    f"  成功: {event.success}"
                )
                
            except Exception as e:
                event.success = False
                event.error_message = str(e)
                elapsed_ms = (time.time() - start_time) * 1000
                self._log_error(
                    f"========== 打断失败 (耗时 {elapsed_ms:.2f}ms) ==========\n"
                    f"  错误: {e}\n"
                    f"  堆栈: {traceback.format_exc()}"
                )
                await self._invoke_callbacks(event, "error", e)
                
            finally:
                self._is_interrupting = False
                self._active_flushes.pop(flush_request.flush_id, None)
                self._log_debug("释放异步锁")
                
                # 记录历史
                self._add_to_history(event)
        
        return event
    
    async def _execute_interrupt(
        self,
        targets: List[InterruptTarget],
        flush_request: FlushRequest,
    ) -> List[str]:
        """
        执行具体的打断操作
        
        Args:
            targets: 打断目标列表
            flush_request: Flush 请求
            
        Returns:
            List[str]: 被打断的请求 ID 列表
        """
        interrupted_ids = []
        
        # 按顺序打断：TTS -> LLM -> ASR（从下游到上游）
        # 这样可以避免上游继续产生数据
        ordered_targets = self._order_targets(targets)
        self._log_debug(f"打断执行顺序: {[t.value for t in ordered_targets]}")
        
        for i, target in enumerate(ordered_targets):
            self._log_debug(f"[{i+1}/{len(ordered_targets)}] 处理目标: {target.value}")
            
            # 打断可中断组件
            if target in self._targets:
                component = self._targets[target]
                component_type = type(component).__name__
                self._log_debug(f"  找到组件: {component_type}")
                
                try:
                    # 获取当前请求 ID
                    current_id = component.get_current_request_id()
                    if current_id:
                        interrupted_ids.append(current_id)
                        self._log_info(f"  当前请求 ID: {current_id[:16]}...")
                    else:
                        self._log_debug(f"  无当前请求")
                    
                    # 执行打断
                    self._log_debug(f"  调用 on_interrupt...")
                    success = await component.on_interrupt(flush_request)
                    if success:
                        self._log_info(f"  ✓ {target.value} 打断成功")
                    else:
                        self._log_warning(f"  ✗ {target.value} 打断失败 (返回 False)")
                except Exception as e:
                    self._log_error(f"  ✗ {target.value} 打断异常: {e}\n{traceback.format_exc()}")
            else:
                self._log_debug(f"  未注册组件，跳过")
            
            # 清空队列
            if target in self._queues:
                queue_component = self._queues[target]
                queue_type = type(queue_component).__name__
                try:
                    queue_size_before = queue_component.get_queue_size()
                    count = queue_component.flush_queue()
                    self._log_info(f"  ✓ 清空队列: {queue_type}, 清空 {count} 项 (之前 {queue_size_before} 项)")
                except Exception as e:
                    self._log_error(f"  ✗ 清空队列失败: {e}")
            
            # 取消任务
            if target in self._tasks:
                task_component = self._tasks[target]
                task_type = type(task_component).__name__
                try:
                    has_task = task_component.has_active_task()
                    if has_task:
                        self._log_debug(f"  取消任务: {task_type}")
                        await task_component.cancel_current_task()
                        self._log_info(f"  ✓ 任务已取消")
                    else:
                        self._log_debug(f"  无活动任务")
                except Exception as e:
                    self._log_error(f"  ✗ 取消任务失败: {e}")
        
        self._log_debug(f"打断执行完成，共打断 {len(interrupted_ids)} 个请求")
        return interrupted_ids
    
    def _order_targets(self, targets: List[InterruptTarget]) -> List[InterruptTarget]:
        """
        对打断目标排序（从下游到上游）
        
        打断顺序：AUDIO_OUTPUT -> TTS -> LLM -> ASR
        这样可以确保先停止输出，再停止处理，最后停止输入。
        """
        priority = {
            InterruptTarget.AUDIO_OUTPUT: 0,
            InterruptTarget.TTS: 1,
            InterruptTarget.LLM: 2,
            InterruptTarget.ASR: 3,
        }
        return sorted(targets, key=lambda t: priority.get(t, 99))
    
    # ==================== 快捷方法 ====================
    
    async def interrupt_all(
        self,
        source: InterruptSource = InterruptSource.UNKNOWN,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InterruptEvent:
        """
        打断所有组件（快捷方法）
        
        Args:
            source: 打断触发源
            metadata: 附加元数据
            
        Returns:
            InterruptEvent: 打断事件
        """
        self._log_info(f"调用 interrupt_all: source={source.value}")
        return await self.interrupt(
            source=source,
            targets=[InterruptTarget.ALL],
            metadata=metadata,
        )
    
    async def interrupt_tts(
        self,
        source: InterruptSource = InterruptSource.UNKNOWN,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InterruptEvent:
        """
        只打断 TTS（快捷方法）
        
        Args:
            source: 打断触发源
            metadata: 附加元数据
            
        Returns:
            InterruptEvent: 打断事件
        """
        self._log_info(f"调用 interrupt_tts: source={source.value}")
        return await self.interrupt(
            source=source,
            targets=[InterruptTarget.TTS, InterruptTarget.AUDIO_OUTPUT],
            metadata=metadata,
        )
    
    async def interrupt_llm_and_tts(
        self,
        source: InterruptSource = InterruptSource.UNKNOWN,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InterruptEvent:
        """
        打断 LLM 和 TTS（快捷方法）
        
        这是最常见的打断场景：用户说话时打断 AI 的回复。
        
        Args:
            source: 打断触发源
            metadata: 附加元数据
            
        Returns:
            InterruptEvent: 打断事件
        """
        self._log_info(f"调用 interrupt_llm_and_tts: source={source.value}")
        return await self.interrupt(
            source=source,
            targets=[InterruptTarget.LLM, InterruptTarget.TTS, InterruptTarget.AUDIO_OUTPUT],
            metadata=metadata,
        )
    
    # ==================== Flush 检查 ====================
    
    def is_flushed(self, request_id: str) -> bool:
        """
        检查请求是否应该被跳过（已被 flush）
        
        参考 ten-framework 的设计，在处理请求前检查是否已被打断。
        
        Args:
            request_id: 请求 ID
            
        Returns:
            bool: 是否应该跳过
        """
        with self._lock:
            is_flushed = request_id in self._interrupted_requests
            if is_flushed:
                self._log_debug(f"is_flushed 检查: request_id={request_id[:16]}... -> True (已被打断)")
            return is_flushed
    
    def get_active_flush_id(self) -> Optional[str]:
        """
        获取当前活跃的 flush ID
        
        Returns:
            flush_id 或 None
        """
        with self._lock:
            if self._active_flushes:
                flush_id = next(iter(self._active_flushes.keys()))
                self._log_debug(f"当前活跃 flush_id: {flush_id[:16]}...")
                return flush_id
            return None
    
    # ==================== 统计和历史 ====================
    
    def _update_stats(self, event: InterruptEvent) -> None:
        """更新统计数据"""
        with self._lock:
            self._interrupt_count += 1
            for target in event.targets:
                self._interrupt_count_by_target[target] = \
                    self._interrupt_count_by_target.get(target, 0) + 1
    
    def _add_to_history(self, event: InterruptEvent) -> None:
        """添加到历史记录"""
        with self._lock:
            self._interrupt_history.append(event)
            # 限制历史大小
            if len(self._interrupt_history) > self._history_max_size:
                self._interrupt_history = self._interrupt_history[-self._history_max_size:]
    
    def get_interrupt_count(self, target: Optional[InterruptTarget] = None) -> int:
        """
        获取打断次数
        
        Args:
            target: 可选的目标过滤
            
        Returns:
            int: 打断次数
        """
        with self._lock:
            if target:
                return self._interrupt_count_by_target.get(target, 0)
            return self._interrupt_count
    
    def get_interrupt_history(
        self,
        limit: int = 10,
        target: Optional[InterruptTarget] = None,
    ) -> List[InterruptEvent]:
        """
        获取打断历史
        
        Args:
            limit: 返回的最大数量
            target: 可选的目标过滤
            
        Returns:
            List[InterruptEvent]: 打断事件列表
        """
        with self._lock:
            history = self._interrupt_history
            if target:
                history = [e for e in history if target in e.targets]
            return history[-limit:]
    
    # ==================== 状态查询 ====================
    
    @property
    def is_interrupting(self) -> bool:
        """是否正在执行打断"""
        return self._is_interrupting
    
    @property
    def is_closed(self) -> bool:
        """管理器是否已关闭"""
        return self._is_closed
    
    def get_registered_targets(self) -> List[InterruptTarget]:
        """获取已注册的目标列表"""
        with self._lock:
            return list(self._targets.keys())
    
    # ==================== 生命周期 ====================
    
    async def cleanup(self) -> None:
        """
        清理资源
        
        在连接关闭时调用，释放所有资源。
        """
        self._log_info("========== 开始清理 InterruptManager ==========")
        
        if self._is_closed:
            self._log_warning("InterruptManager 已经关闭，跳过清理")
            return
        
        self._is_closed = True
        
        # 执行最后的打断
        if not self._is_interrupting:
            self._log_info("执行最终打断...")
            try:
                await self.interrupt(
                    source=InterruptSource.SESSION_END,
                    notify_client=False,
                )
            except Exception as e:
                self._log_error(f"最终打断出错: {e}")
        else:
            self._log_warning("正在执行打断中，跳过最终打断")
        
        # 清理状态
        with self._lock:
            target_count = len(self._targets)
            queue_count = len(self._queues)
            task_count = len(self._tasks)
            callback_count = len(self._callbacks)
            context_count = len(self._request_contexts)
            
            self._targets.clear()
            self._queues.clear()
            self._tasks.clear()
            self._callbacks.clear()
            self._request_contexts.clear()
            self._active_flushes.clear()
            self._interrupted_requests.clear()
            
            self._log_info(
                f"清理完成:\n"
                f"  - 目标组件: {target_count}\n"
                f"  - 队列组件: {queue_count}\n"
                f"  - 任务组件: {task_count}\n"
                f"  - 回调: {callback_count}\n"
                f"  - 请求上下文: {context_count}"
            )
        
        self._log_info(f"========== InterruptManager 清理完成 ==========")
    
    @asynccontextmanager
    async def interrupt_scope(
        self,
        source: InterruptSource = InterruptSource.UNKNOWN,
        targets: Optional[List[InterruptTarget]] = None,
    ):
        """
        打断作用域（上下文管理器）
        
        在进入作用域时自动打断，便于使用 with 语句。
        
        使用示例:
            async with manager.interrupt_scope(source=InterruptSource.VAD):
                # 这里的代码在打断完成后执行
                await process_new_input()
        """
        event = await self.interrupt(source=source, targets=targets)
        try:
            yield event
        finally:
            pass  # 可以在这里添加清理逻辑


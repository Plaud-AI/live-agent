"""
全局GC管理模块
定期执行垃圾回收，避免频繁触发GC导致的GIL锁问题

同时提供事件循环健康监控功能：
- 检测事件循环阻塞
- 记录详细的阻塞信息
"""

import gc
import asyncio
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class GlobalGCManager:
    """全局垃圾回收管理器 & 事件循环健康监控"""

    def __init__(self, interval_seconds=300):
        """
        初始化GC管理器

        Args:
            interval_seconds: GC执行间隔（秒），默认300秒（5分钟）
        """
        self.interval_seconds = interval_seconds
        self._task = None
        self._stop_event = asyncio.Event()
        self._lock = threading.Lock()
        
        # 事件循环健康监控
        self._last_heartbeat_time = time.time()
        self._heartbeat_monitor_thread = None
        self._monitor_stop_event = threading.Event()
        # 阈值设为 45 秒（心跳间隔 30 秒 + 15 秒缓冲），避免误报
        self._blocking_threshold_seconds = 45

    async def start(self):
        """启动定时GC任务和事件循环监控"""
        if self._task is not None:
            logger.bind(tag=TAG).warning("GC管理器已经在运行")
            return

        logger.bind(tag=TAG).info(f"启动全局GC管理器，间隔{self.interval_seconds}秒")
        self._stop_event.clear()
        self._task = asyncio.create_task(self._gc_loop())
        
        # 启动事件循环阻塞监控线程
        self._monitor_stop_event.clear()
        self._heartbeat_monitor_thread = threading.Thread(
            target=self._monitor_event_loop_health,
            name="EventLoopMonitor",
            daemon=True
        )
        self._heartbeat_monitor_thread.start()
        logger.bind(tag=TAG).info("事件循环健康监控已启动")

    async def stop(self):
        """停止定时GC任务和事件循环监控"""
        if self._task is None:
            return

        logger.bind(tag=TAG).info("停止全局GC管理器")
        self._stop_event.set()
        self._monitor_stop_event.set()

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._task = None
        
        # 等待监控线程退出
        if self._heartbeat_monitor_thread and self._heartbeat_monitor_thread.is_alive():
            self._heartbeat_monitor_thread.join(timeout=2.0)

    async def _gc_loop(self):
        """GC循环任务"""
        heartbeat_count = 0
        try:
            while not self._stop_event.is_set():
                # 更新心跳时间戳（用于阻塞检测）
                self._last_heartbeat_time = time.time()
                
                # 每 30 秒输出一次心跳日志，用于监控事件循环是否正常
                heartbeat_count += 1
                if heartbeat_count % 10 == 0:  # 每 300 秒（5分钟）执行 GC
                    await self._run_gc()
                else:
                    # 心跳日志，每 30 秒一次，使用 INFO 级别确保生产环境可见
                    logger.bind(tag=TAG).info(
                        f"[心跳] 事件循环正常 #{heartbeat_count}"
                    )
                
                # 等待 30 秒
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=30
                    )
                    # 如果stop_event被设置，退出循环
                    break
                except asyncio.TimeoutError:
                    # 超时表示继续循环
                    pass

        except asyncio.CancelledError:
            logger.bind(tag=TAG).info("GC循环任务被取消")
            raise
        except Exception as e:
            logger.bind(tag=TAG).error(f"GC循环任务异常: {e}")
        finally:
            logger.bind(tag=TAG).info("GC循环任务已退出")
    
    def _monitor_event_loop_health(self):
        """
        独立线程：监控事件循环健康状态
        
        通过检查心跳时间戳来检测事件循环阻塞
        """
        consecutive_warnings = 0
        
        while not self._monitor_stop_event.is_set():
            time.sleep(5)  # 每 5 秒检查一次
            
            if self._monitor_stop_event.is_set():
                break
            
            elapsed = time.time() - self._last_heartbeat_time
            
            if elapsed > self._blocking_threshold_seconds:
                consecutive_warnings += 1
                
                # 获取当前所有线程的堆栈信息
                thread_info = self._get_thread_stacks() if consecutive_warnings <= 3 else ""
                
                logger.bind(tag=TAG).error(
                    f"[事件循环阻塞警告] 已 {elapsed:.1f} 秒未收到心跳! "
                    f"(连续警告: {consecutive_warnings})"
                )
                
                if thread_info and consecutive_warnings == 1:
                    logger.bind(tag=TAG).error(f"[线程堆栈信息]\n{thread_info}")
                
                # 连续警告超过 6 次（约 30 秒），记录严重警告
                if consecutive_warnings >= 6:
                    logger.bind(tag=TAG).critical(
                        f"[严重] 事件循环持续阻塞超过 {elapsed:.1f} 秒，可能需要重启服务!"
                    )
            else:
                if consecutive_warnings > 0:
                    logger.bind(tag=TAG).info(
                        f"[事件循环恢复] 阻塞已解除，心跳恢复正常"
                    )
                consecutive_warnings = 0
    
    def _get_thread_stacks(self) -> str:
        """获取所有线程的堆栈信息（用于诊断阻塞）"""
        try:
            import sys
            thread_stacks = []
            
            for thread_id, frame in sys._current_frames().items():
                thread_name = None
                for t in threading.enumerate():
                    if t.ident == thread_id:
                        thread_name = t.name
                        break
                
                thread_name = thread_name or f"Thread-{thread_id}"
                stack = ''.join(traceback.format_stack(frame))
                
                # 只记录可能相关的线程（排除系统线程）
                if "EventLoopMonitor" not in thread_name:
                    thread_stacks.append(f"\n=== {thread_name} ===\n{stack}")
            
            return '\n'.join(thread_stacks[:5])  # 最多记录 5 个线程
        except Exception as e:
            return f"获取线程堆栈失败: {e}"

    async def _run_gc(self):
        """执行垃圾回收"""
        try:
            # 在线程池中执行GC，避免阻塞事件循环
            loop = asyncio.get_running_loop()

            def do_gc():
                with self._lock:
                    before = len(gc.get_objects())
                    collected = gc.collect()
                    after = len(gc.get_objects())
                    return before, collected, after

            before, collected, after = await loop.run_in_executor(None, do_gc)
            logger.bind(tag=TAG).debug(
                f"全局GC执行完成 - 回收对象: {collected}, "
                f"对象数量: {before} -> {after}"
            )
        except Exception as e:
            logger.bind(tag=TAG).error(f"执行GC时出错: {e}")


# 全局单例
_gc_manager_instance = None


def get_gc_manager(interval_seconds=300):
    """
    获取全局GC管理器实例（单例模式）

    Args:
        interval_seconds: GC执行间隔（秒），默认300秒（5分钟）

    Returns:
        GlobalGCManager实例
    """
    global _gc_manager_instance
    if _gc_manager_instance is None:
        _gc_manager_instance = GlobalGCManager(interval_seconds)
    return _gc_manager_instance

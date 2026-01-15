"""
WebSocket 连接初始化性能测试器

测量从 WebSocket 连接建立到 Agent 初始化完成的时间分布。

时间点定义:
- T0: 客户端发起 WebSocket 连接
- T1: WebSocket 连接建立 (onopen)
- T2: 客户端发送 hello 消息
- T3: 收到服务端 hello 响应
- Agent Ready: 服务端 _agent_ready_event.set() (需要查看服务端日志)

使用方式:
1. 确保 xiaozhi-server 已启动
2. 运行: python performance_tester.py 然后选择此测试
3. 或直接运行: python -m performance_tester.performance_tester_connection_init

可配置参数:
- WS_URL: WebSocket 服务器地址
- DEVICE_ID: 设备ID
- AGENT_ID: Agent ID (可选)
- NUM_TESTS: 测试次数
"""

import asyncio
import json
import time
import statistics
import websockets
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from tabulate import tabulate

description = "WebSocket连接初始化性能测试"

# ============== 配置 ==============
# WebSocket 服务器地址
WS_URL = "ws://44.228.155.146:8000/xiaozhi/v1/"

# 认证信息（参考设备端连接参数）
DEVICE_ID = "XZA000-80B54EE8AD4C"
CLIENT_ID = "XZA000-80B54EE8AD4C"
AGENT_ID = ""  # 留空则使用设备端模式（需要唤醒词触发）
TOKEN = ""  # 如果启用了认证，填入有效 token

# 协议版本（与设备端保持一致）
PROTOCOL_VERSION = 1

# 测试参数
NUM_TESTS = 10  # 测试次数
HELLO_TIMEOUT = 10.0  # hello 响应超时时间（秒）
CONNECT_TIMEOUT = 5.0  # 连接超时时间（秒）
WAIT_AFTER_HELLO = 1.0  # hello 响应后等待时间（秒），让服务端完成初始化


@dataclass
class TestResult:
    """单次测试结果"""
    test_id: int
    success: bool
    
    # 时间戳（毫秒）
    t0_connect_start: float = 0
    t1_connected: float = 0
    t2_hello_sent: float = 0
    t3_hello_received: float = 0
    
    # 计算的时延（毫秒）
    connect_latency: float = 0  # T0 -> T1
    hello_rtt: float = 0  # T2 -> T3
    total_latency: float = 0  # T0 -> T3
    
    session_id: str = ""
    error_msg: str = ""
    
    # 服务端返回的 welcome 消息
    welcome_msg: Dict[str, Any] = field(default_factory=dict)


class ConnectionInitTester:
    def __init__(self):
        self.results: List[TestResult] = []
    
    def _build_ws_url(self) -> str:
        """构建 WebSocket URL"""
        return WS_URL.rstrip('/')
    
    def _build_headers(self) -> Dict[str, str]:
        """构建 WebSocket 连接 Headers（与设备端保持一致）"""
        headers = {
            "Device-Id": DEVICE_ID,
            "Client-Id": CLIENT_ID,
            "Protocol-Version": str(PROTOCOL_VERSION),
        }
        
        if AGENT_ID:
            headers["Agent-Id"] = AGENT_ID
        
        if TOKEN:
            if TOKEN.startswith("Bearer "):
                headers["Authorization"] = TOKEN
            else:
                headers["Authorization"] = f"Bearer {TOKEN}"
        
        return headers
    
    async def run_single_test(self, test_id: int) -> TestResult:
        """执行单次连接测试"""
        result = TestResult(test_id=test_id, success=False)
        ws = None
        
        try:
            ws_url = self._build_ws_url()
            headers = self._build_headers()
            
            # T0: 开始连接
            result.t0_connect_start = time.time() * 1000
            
            # 建立 WebSocket 连接（使用 Headers，与设备端保持一致）
            try:
                ws = await asyncio.wait_for(
                    websockets.connect(
                        ws_url,
                        additional_headers=headers,
                        ping_interval=None,  # 禁用 ping，避免干扰测试
                        close_timeout=2,
                    ),
                    timeout=CONNECT_TIMEOUT
                )
            except asyncio.TimeoutError:
                result.error_msg = f"连接超时 ({CONNECT_TIMEOUT}s)"
                return result
            except Exception as e:
                result.error_msg = f"连接失败: {str(e)}"
                return result
            
            # T1: 连接建立
            result.t1_connected = time.time() * 1000
            result.connect_latency = result.t1_connected - result.t0_connect_start
            
            # 构造 hello 消息（与设备端格式保持一致）
            hello_message = {
                "type": "hello",
                "version": PROTOCOL_VERSION,
                "transport": "websocket",
                "audio_params": {
                    "format": "opus",
                    "sample_rate": 16000,
                    "channels": 1,
                    "frame_duration": 60,
                },
                "features": {
                    "mcp": False,  # 禁用 MCP 以简化测试
                }
            }
            
            # T2: 发送 hello 消息
            result.t2_hello_sent = time.time() * 1000
            await ws.send(json.dumps(hello_message))
            
            # 等待 hello 响应
            try:
                response_received = False
                while not response_received:
                    message = await asyncio.wait_for(
                        ws.recv(),
                        timeout=HELLO_TIMEOUT
                    )
                    
                    try:
                        response = json.loads(message)
                        if response.get("type") == "hello" and response.get("session_id"):
                            # T3: 收到 hello 响应
                            result.t3_hello_received = time.time() * 1000
                            result.session_id = response.get("session_id", "")
                            result.welcome_msg = response
                            response_received = True
                    except json.JSONDecodeError:
                        # 忽略非 JSON 消息
                        continue
                        
            except asyncio.TimeoutError:
                result.error_msg = f"Hello响应超时 ({HELLO_TIMEOUT}s)"
                return result
            
            # 计算时延
            result.hello_rtt = result.t3_hello_received - result.t2_hello_sent
            result.total_latency = result.t3_hello_received - result.t0_connect_start
            result.success = True
            
            # 等待一段时间让服务端完成初始化（避免打断后续组件初始化）
            if WAIT_AFTER_HELLO > 0:
                await asyncio.sleep(WAIT_AFTER_HELLO)
            
        except Exception as e:
            result.error_msg = f"测试异常: {str(e)}"
        finally:
            if ws:
                try:
                    await ws.close()
                except Exception:
                    pass
        
        return result
    
    async def run_tests(self) -> None:
        """执行所有测试"""
        print(f"\n{'='*60}")
        print("WebSocket 连接初始化性能测试")
        print(f"{'='*60}")
        print(f"服务器地址: {WS_URL}")
        print(f"设备ID: {DEVICE_ID}")
        print(f"Agent ID: {AGENT_ID or '(未设置 - 设备端模式)'}")
        print(f"测试次数: {NUM_TESTS}")
        print(f"{'='*60}\n")
        
        for i in range(NUM_TESTS):
            print(f"执行测试 {i+1}/{NUM_TESTS}...", end=" ")
            result = await self.run_single_test(i + 1)
            self.results.append(result)
            
            if result.success:
                print(f"✅ 连接={result.connect_latency:.0f}ms, "
                      f"Hello RTT={result.hello_rtt:.0f}ms, "
                      f"总计={result.total_latency:.0f}ms")
            else:
                print(f"❌ {result.error_msg}")
            
            # 测试间隔
            if i < NUM_TESTS - 1:
                await asyncio.sleep(0.5)
        
        self._print_summary()
    
    def _print_summary(self) -> None:
        """打印测试摘要"""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        print(f"\n{'='*60}")
        print("测试结果摘要")
        print(f"{'='*60}")
        print(f"成功: {len(successful)}/{len(self.results)}")
        print(f"失败: {len(failed)}/{len(self.results)}")
        
        if not successful:
            print("\n⚠️ 所有测试都失败了，请检查服务器是否正常运行")
            if failed:
                print("\n失败原因:")
                for r in failed[:5]:  # 最多显示5个
                    print(f"  - 测试 {r.test_id}: {r.error_msg}")
            return
        
        # 统计数据
        connect_latencies = [r.connect_latency for r in successful]
        hello_rtts = [r.hello_rtt for r in successful]
        total_latencies = [r.total_latency for r in successful]
        
        headers = ["指标", "最小值", "最大值", "平均值", "中位数", "P95", "P99"]
        
        def calc_stats(data: List[float]) -> List[str]:
            if not data:
                return ["-"] * 6
            sorted_data = sorted(data)
            p95_idx = int(len(sorted_data) * 0.95)
            p99_idx = int(len(sorted_data) * 0.99)
            return [
                f"{min(data):.1f}ms",
                f"{max(data):.1f}ms",
                f"{statistics.mean(data):.1f}ms",
                f"{statistics.median(data):.1f}ms",
                f"{sorted_data[min(p95_idx, len(sorted_data)-1)]:.1f}ms",
                f"{sorted_data[min(p99_idx, len(sorted_data)-1)]:.1f}ms",
            ]
        
        table_data = [
            ["WebSocket连接 (T0→T1)"] + calc_stats(connect_latencies),
            ["Hello RTT (T2→T3)"] + calc_stats(hello_rtts),
            ["总延迟 (T0→T3)"] + calc_stats(total_latencies),
        ]
        
        print("\n时延统计:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # 详细结果表
        print("\n详细结果:")
        detail_headers = ["测试#", "状态", "连接", "Hello RTT", "总计", "Session ID"]
        detail_data = []
        
        for r in self.results:
            if r.success:
                detail_data.append([
                    r.test_id,
                    "✅",
                    f"{r.connect_latency:.0f}ms",
                    f"{r.hello_rtt:.0f}ms",
                    f"{r.total_latency:.0f}ms",
                    r.session_id[:8] + "..." if r.session_id else "-",
                ])
            else:
                detail_data.append([
                    r.test_id,
                    "❌",
                    "-",
                    "-",
                    "-",
                    r.error_msg[:30],
                ])
        
        print(tabulate(detail_data, headers=detail_headers, tablefmt="grid"))
        
        # 服务端日志提示
        print(f"\n{'='*60}")
        print("📋 服务端时间分布（请查看服务端日志）")
        print(f"{'='*60}")
        print("""
要获取完整的时间分布，请查看服务端日志中的以下关键点:

1. 连接建立:
   🔗 [连接建立] IP=... | Device-ID=...

2. 组件初始化开始:
   查找 "_initialize_components" 相关日志

3. Agent 配置获取:
   ⚡ [后台初始化] API 调用完成: XXXms

4. 各模块初始化:
   - TTS audio channels opened
   - VAD stream instance created
   - ASR open_audio_channels

5. Agent Ready:
   ✅ [后台初始化] 完成: XXXms

建议: 启用 DEBUG 日志级别以获取更详细的时间信息:
   在 config.yaml 中设置: log_level: DEBUG
""")


async def main():
    tester = ConnectionInitTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())


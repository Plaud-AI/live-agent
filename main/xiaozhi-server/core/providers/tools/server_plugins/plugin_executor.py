"""服务端插件工具执行器"""

import asyncio
import functools
from typing import Dict, Any
from ..base import ToolType, ToolDefinition, ToolExecutor
from plugins_func.register import all_function_registry, Action, ActionResponse


class ServerPluginExecutor(ToolExecutor):
    """服务端插件工具执行器"""

    def __init__(self, conn):
        self.conn = conn
        self.config = conn.config

    async def execute(
        self, conn, tool_name: str, arguments: Dict[str, Any]
    ) -> ActionResponse:
        """
        执行服务端插件工具
        
        重要：所有同步插件函数都在线程池中执行，避免阻塞事件循环。
        超时设置为 60 秒，防止插件函数永久阻塞。
        """
        func_item = all_function_registry.get(tool_name)
        if not func_item:
            return ActionResponse(
                action=Action.NOTFOUND, response=f"插件函数 {tool_name} 不存在"
            )

        try:
            # 获取事件循环
            loop = asyncio.get_running_loop()
            
            # 根据工具类型决定如何调用
            if hasattr(func_item, "type"):
                func_type = func_item.type
                if func_type.code in [4, 5]:  # SYSTEM_CTL, IOT_CTL (需要conn参数)
                    func_call = functools.partial(func_item.func, conn, **arguments)
                elif func_type.code == 2:  # WAIT
                    func_call = functools.partial(func_item.func, **arguments)
                elif func_type.code == 3:  # CHANGE_SYS_PROMPT
                    func_call = functools.partial(func_item.func, conn, **arguments)
                else:
                    func_call = functools.partial(func_item.func, **arguments)
            else:
                # 默认不传conn参数
                func_call = functools.partial(func_item.func, **arguments)

            # 在线程池中执行同步函数，设置 60 秒超时
            # 这样即使插件函数有阻塞操作（如 requests.get、future.result()），也不会阻塞事件循环
            result = await asyncio.wait_for(
                loop.run_in_executor(None, func_call),
                timeout=60.0
            )
            return result

        except asyncio.TimeoutError:
            return ActionResponse(
                action=Action.ERROR,
                response=f"插件函数 {tool_name} 执行超时(60s)",
            )
        except Exception as e:
            return ActionResponse(
                action=Action.ERROR,
                response=str(e),
            )

    def get_tools(self) -> Dict[str, ToolDefinition]:
        """获取所有注册的服务端插件工具"""
        tools = {}

        # 获取必要的函数
        necessary_functions = ["handle_exit_intent", "get_lunar"]

        # 获取配置中的函数
        config_functions = self.config["Intent"][
            self.config["selected_module"]["Intent"]
        ].get("functions", [])

        # 转换为列表
        if not isinstance(config_functions, list):
            try:
                config_functions = list(config_functions)
            except TypeError:
                config_functions = []

        # 合并所有需要的函数
        all_required_functions = list(set(necessary_functions + config_functions))

        for func_name in all_required_functions:
            func_item = all_function_registry.get(func_name)
            if func_item:
                # 从函数注册中获取描述
                fun_description = (
                    self.config.get("plugins", {})
                    .get(func_name, {})
                    .get("description", "")
                )
                if fun_description is not None and len(fun_description) > 0:
                    if "function" in func_item.description and isinstance(
                        func_item.description["function"], dict
                    ):
                        func_item.description["function"][
                            "description"
                        ] = fun_description
                tools[func_name] = ToolDefinition(
                    name=func_name,
                    description=func_item.description,
                    tool_type=ToolType.SERVER_PLUGIN,
                )

        return tools

    def has_tool(self, tool_name: str) -> bool:
        """检查是否有指定的服务端插件工具"""
        return tool_name in all_function_registry

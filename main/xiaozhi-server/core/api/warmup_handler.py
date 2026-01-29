"""
缓存预热接口处理器

用于 App 登录后预热 agent 配置缓存，减少首次激活延迟
"""

import json
from aiohttp import web
from config.logger import setup_logging
from config.manage_api_client import warmup_agent_config, warmup_user_agents

TAG = __name__


class WarmupHandler:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()

    async def handle_options(self, request: web.Request) -> web.Response:
        """处理 CORS 预检请求"""
        return web.Response(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        )

    async def warmup_agent(self, request: web.Request) -> web.Response:
        """
        预热单个 agent 配置
        
        POST /internal/warmup/agent
        Body: {"agent_id": "xxx"}
        
        Response: {"success": true, "message": "Agent config warmed up"}
        """
        try:
            data = await request.json()
            agent_id = data.get("agent_id")
            
            if not agent_id:
                return web.json_response(
                    {"success": False, "message": "agent_id is required"},
                    status=400,
                    headers={"Access-Control-Allow-Origin": "*"},
                )
            
            success = await warmup_agent_config(agent_id)
            
            if success:
                self.logger.bind(tag=TAG).info(f"Agent 配置预热成功: {agent_id}")
                return web.json_response(
                    {"success": True, "message": f"Agent {agent_id} config warmed up"},
                    headers={"Access-Control-Allow-Origin": "*"},
                )
            else:
                self.logger.bind(tag=TAG).warning(f"Agent 配置预热失败: {agent_id}")
                return web.json_response(
                    {"success": False, "message": f"Failed to warm up agent {agent_id}"},
                    status=500,
                    headers={"Access-Control-Allow-Origin": "*"},
                )
                
        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "message": "Invalid JSON"},
                status=400,
                headers={"Access-Control-Allow-Origin": "*"},
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"预热接口异常: {e}")
            return web.json_response(
                {"success": False, "message": str(e)},
                status=500,
                headers={"Access-Control-Allow-Origin": "*"},
            )

    async def warmup_user_agents(self, request: web.Request) -> web.Response:
        """
        批量预热用户所有 agent 配置
        
        POST /internal/warmup/user
        Body: {"user_id": 123}
        
        Response: {"success": true, "count": 5, "message": "5 agent configs warmed up"}
        """
        try:
            data = await request.json()
            user_id = data.get("user_id")
            
            if not user_id:
                return web.json_response(
                    {"success": False, "message": "user_id is required"},
                    status=400,
                    headers={"Access-Control-Allow-Origin": "*"},
                )
            
            count = await warmup_user_agents(int(user_id))
            
            self.logger.bind(tag=TAG).info(f"用户 {user_id} 的 {count} 个 agent 配置预热完成")
            return web.json_response(
                {
                    "success": True,
                    "count": count,
                    "message": f"{count} agent configs warmed up for user {user_id}",
                },
                headers={"Access-Control-Allow-Origin": "*"},
            )
                
        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "message": "Invalid JSON"},
                status=400,
                headers={"Access-Control-Allow-Origin": "*"},
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"批量预热接口异常: {e}")
            return web.json_response(
                {"success": False, "message": str(e)},
                status=500,
                headers={"Access-Control-Allow-Origin": "*"},
            )




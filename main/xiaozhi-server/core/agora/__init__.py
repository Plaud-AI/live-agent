"""
Agora RTC 服务模块

提供 Agora RTC 集成支持：
- AgoraServiceManager: 管理 AgoraService 单例
- TokenService: Token 生成服务
- AgoraConnectionPool: 连接池管理（可选）
"""

from core.agora.service_manager import AgoraServiceManager
from core.agora.token_service import TokenService

__all__ = [
    "AgoraServiceManager",
    "TokenService",
]

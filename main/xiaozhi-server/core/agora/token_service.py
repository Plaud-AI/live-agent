"""
Agora Token 生成服务

根据 Agora 文档，Token 用于频道加入时的鉴权。

Token 生成规则：
- 如果配置了 App Certificate，生成标准 Token
- 如果未配置 App Certificate，直接使用 App ID 作为 Token

用法：
    token = TokenService.generate_rtc_token(
        channel_name="room_123",
        uid=12345,
        expire_seconds=3600
    )
"""

import os
import time
import logging
from typing import Optional

TAG = __name__

# 尝试导入 Token Builder
try:
    from agora_token_builder import RtcTokenBuilder
    TOKEN_BUILDER_AVAILABLE = True
except ImportError:
    TOKEN_BUILDER_AVAILABLE = False
    RtcTokenBuilder = None


class TokenService:
    """
    Agora Token 生成服务
    """
    
    _logger = logging.getLogger(TAG)
    _app_id: Optional[str] = None
    _app_certificate: Optional[str] = None
    
    # Token 角色常量
    ROLE_PUBLISHER = 1
    ROLE_SUBSCRIBER = 2
    
    @classmethod
    def configure(
        cls,
        app_id: Optional[str] = None,
        app_certificate: Optional[str] = None
    ) -> None:
        """
        配置 Token 服务
        
        Args:
            app_id: Agora App ID
            app_certificate: Agora App Certificate
        """
        cls._app_id = app_id or os.getenv("AGORA_APP_ID")
        cls._app_certificate = app_certificate or os.getenv("AGORA_APP_CERTIFICATE", "")
        
        if cls._app_id:
            cls._logger.info(f"Token 服务配置完成: app_id={cls._app_id[:8]}...")
        else:
            cls._logger.warning("未配置 AGORA_APP_ID，Token 生成将失败")
    
    @classmethod
    def is_available(cls) -> bool:
        """检查 Token Builder 是否可用"""
        return TOKEN_BUILDER_AVAILABLE
    
    @classmethod
    def generate_rtc_token(
        cls,
        channel_name: str,
        uid: int,
        role: int = ROLE_PUBLISHER,
        expire_seconds: int = 3600,
        app_id: Optional[str] = None,
        app_certificate: Optional[str] = None,
    ) -> Optional[str]:
        """
        生成 RTC Token
        
        Args:
            channel_name: 频道名称
            uid: 用户 ID
            role: 角色（1=发布者, 2=订阅者）
            expire_seconds: Token 有效期（秒）
            app_id: 可选覆盖的 App ID
            app_certificate: 可选覆盖的 App Certificate
            
        Returns:
            Token 字符串，失败时返回 None
        """
        # 获取配置
        final_app_id = app_id or cls._app_id or os.getenv("AGORA_APP_ID")
        final_app_cert = app_certificate or cls._app_certificate or os.getenv("AGORA_APP_CERTIFICATE", "")
        
        if not final_app_id:
            cls._logger.error("未配置 AGORA_APP_ID，无法生成 Token")
            return None
        
        # 如果没有配置证书，直接返回 App ID 作为 Token
        # （仅用于开发/测试环境）
        if not final_app_cert:
            cls._logger.warning("未配置 App Certificate，使用 App ID 作为 Token（仅限开发环境）")
            return final_app_id
        
        if not TOKEN_BUILDER_AVAILABLE:
            cls._logger.error("agora-token-builder 不可用，请安装依赖")
            return None
        
        try:
            # 计算过期时间
            expire_time = int(time.time()) + expire_seconds
            
            # 生成 Token
            token = RtcTokenBuilder.buildTokenWithUid(
                final_app_id,
                final_app_cert,
                channel_name,
                uid,
                role,
                expire_time
            )
            
            cls._logger.info(
                f"Token 生成成功: channel={channel_name}, uid={uid}, "
                f"expire_in={expire_seconds}s"
            )
            return token
            
        except Exception as e:
            cls._logger.error(f"Token 生成失败: {e}")
            return None
    
    @classmethod
    def generate_token_response(
        cls,
        channel_name: str,
        uid: int,
        expire_seconds: int = 3600,
    ) -> Optional[dict]:
        """
        生成完整的 Token 响应（用于 API 返回）
        
        Args:
            channel_name: 频道名称
            uid: 用户 ID
            expire_seconds: Token 有效期
            
        Returns:
            包含 appId, token, channel_name, uid 的字典
        """
        token = cls.generate_rtc_token(channel_name, uid, expire_seconds=expire_seconds)
        
        if token is None:
            return None
        
        return {
            "appId": cls._app_id or os.getenv("AGORA_APP_ID"),
            "token": token,
            "channel_name": channel_name,
            "uid": uid,
        }

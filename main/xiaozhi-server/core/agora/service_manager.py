"""
Agora Service 管理器

重要限制（来自 Agora SDK 文档）：
- 一个进程只能有一个 AgoraService 实例
- 实例在进程启动时创建，进程关闭时释放
- 一个实例可以有多个连接

用法：
    # 初始化（进程启动时调用一次）
    AgoraServiceManager.initialize(app_id="xxx", app_certificate="xxx")
    
    # 创建连接
    connection = AgoraServiceManager.create_connection(channel_name, user_id, token)
    
    # 释放（进程关闭时调用）
    AgoraServiceManager.release()
"""

import os
import logging
import threading
from typing import Optional, Dict, Any

TAG = __name__

# 尝试导入 Agora SDK
try:
    from agora.rtc.rtc_connection import (
        AgoraService,
        AgoraServiceConfig,
        RTCConnection,
        RTCConnConfig,
        AudioScenarioType,
        ChannelProfileType,
        RtcConnectionPublishConfig,
    )
    from agora.rtc.agora_base import AudioPublishType
    AGORA_SDK_AVAILABLE = True
except ImportError as e:
    AGORA_SDK_AVAILABLE = False
    AgoraService = None
    AgoraServiceConfig = None
    RTCConnection = None
    RTCConnConfig = None


class AgoraServiceManager:
    """
    Agora Service 单例管理器
    
    线程安全，确保进程中只有一个 AgoraService 实例。
    """
    
    _instance: Optional['AgoraService'] = None
    _lock = threading.Lock()
    _initialized = False
    _config: Dict[str, Any] = {}
    _logger = logging.getLogger(TAG)
    
    @classmethod
    def is_available(cls) -> bool:
        """检查 Agora SDK 是否可用"""
        return AGORA_SDK_AVAILABLE
    
    @classmethod
    def is_initialized(cls) -> bool:
        """检查是否已初始化"""
        return cls._initialized
    
    @classmethod
    def initialize(
        cls,
        app_id: Optional[str] = None,
        app_certificate: Optional[str] = None,
        log_path: Optional[str] = None,
        log_level: int = 1,  # 1=INFO
        **kwargs
    ) -> bool:
        """
        初始化 Agora Service（进程级别，只调用一次）
        
        Args:
            app_id: Agora App ID（也可通过环境变量 AGORA_APP_ID 设置）
            app_certificate: Agora App Certificate（也可通过环境变量 AGORA_APP_CERTIFICATE 设置）
            log_path: 日志文件路径
            log_level: 日志级别
            
        Returns:
            bool: 是否初始化成功
        """
        if not AGORA_SDK_AVAILABLE:
            cls._logger.error("Agora SDK 不可用，请安装 agora-python-server-sdk")
            return False
        
        with cls._lock:
            if cls._initialized:
                cls._logger.warning("Agora Service 已经初始化，跳过重复初始化")
                return True
            
            # 从环境变量获取配置
            final_app_id = app_id or os.getenv("AGORA_APP_ID")
            final_app_cert = app_certificate or os.getenv("AGORA_APP_CERTIFICATE", "")
            
            if not final_app_id:
                cls._logger.error("未配置 AGORA_APP_ID")
                return False
            
            cls._config = {
                "app_id": final_app_id,
                "app_certificate": final_app_cert,
            }
            
            try:
                # 创建配置
                config = AgoraServiceConfig()
                config.app_id = final_app_id
                config.log_path = log_path or "/tmp/agora_rtc.log"
                config.log_size = 10 * 1024 * 1024  # 10MB
                
                # 创建服务实例
                cls._instance = AgoraService()
                result = cls._instance.initialize(config)
                
                if result != 0:
                    cls._logger.error(f"Agora Service 初始化失败，错误码: {result}")
                    cls._instance = None
                    return False
                
                cls._initialized = True
                cls._logger.info(f"Agora Service 初始化成功: app_id={final_app_id[:8]}...")
                return True
                
            except Exception as e:
                cls._logger.error(f"Agora Service 初始化异常: {e}")
                cls._instance = None
                return False
    
    @classmethod
    def get_service(cls) -> Optional['AgoraService']:
        """
        获取 AgoraService 实例
        
        Returns:
            AgoraService 实例，未初始化时返回 None
        """
        if not cls._initialized:
            cls._logger.warning("Agora Service 未初始化")
            return None
        return cls._instance
    
    @classmethod
    def get_app_id(cls) -> Optional[str]:
        """获取 App ID"""
        return cls._config.get("app_id")
    
    @classmethod
    def get_app_certificate(cls) -> Optional[str]:
        """获取 App Certificate"""
        return cls._config.get("app_certificate")
    
    @classmethod
    def create_connection(
        cls,
        channel_name: str,
        user_id: int,
        token: Optional[str] = None,
        subscribe_audio: bool = True,
        publish_audio: bool = True,
        publish_data: bool = True,
    ) -> Optional['RTCConnection']:
        """
        创建 RTC 连接
        
        Args:
            channel_name: 频道名称
            user_id: 用户 ID
            token: 认证 Token（如果未提供，使用 App ID）
            subscribe_audio: 是否订阅音频
            publish_audio: 是否发布音频
            publish_data: 是否发布数据通道
            
        Returns:
            RtcConnection 实例，失败时返回 None
        """
        if not cls._initialized or cls._instance is None:
            cls._logger.error("Agora Service 未初始化，无法创建连接")
            return None
        
        try:
            # 创建连接配置
            con_config = RTCConnConfig()
            con_config.channel_profile = ChannelProfileType.CHANNEL_PROFILE_LIVE_BROADCASTING
            con_config.client_role_type = 1  # Broadcaster
            con_config.auto_subscribe_audio = subscribe_audio
            
            # 发布配置
            publish_config = RtcConnectionPublishConfig()
            publish_config.is_publish_audio = publish_audio
            publish_config.audio_scenario = AudioScenarioType.AUDIO_SCENARIO_AI_SERVER
            # 关键：使用 ENCODED_PCM 类型以支持 Opus 编码音频发送
            publish_config.audio_publish_type = AudioPublishType.AUDIO_PUBLISH_TYPE_ENCODED_PCM
            
            # 创建连接
            connection = cls._instance.create_rtc_connection(con_config, publish_config)
            
            if connection is None:
                cls._logger.error("创建 RTC 连接失败")
                return None
            
            cls._logger.info(f"RTC 连接创建成功: channel={channel_name}, uid={user_id}")
            return connection
            
        except Exception as e:
            cls._logger.error(f"创建 RTC 连接异常: {e}")
            return None
    
    @classmethod
    def release(cls) -> None:
        """
        释放 Agora Service（进程关闭时调用）
        """
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance.release()
                    cls._logger.info("Agora Service 已释放")
                except Exception as e:
                    cls._logger.error(f"释放 Agora Service 异常: {e}")
                finally:
                    cls._instance = None
                    cls._initialized = False
                    cls._config = {}

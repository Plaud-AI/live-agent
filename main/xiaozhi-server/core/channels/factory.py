"""
通道工厂

根据请求信息自动创建对应的通道实例。

支持的创建方式：
1. 从 WebSocket 连接创建（自动识别类型）
2. 手动创建特定类型通道
3. 创建 Agora RTC 通道
"""
import logging
from typing import Optional
from urllib.parse import urlparse, parse_qs

from core.channels.base import BaseChannel
from core.channels.dto import ChannelInfo, ChannelType
from core.channels.websocket_channel import WebSocketChannel
from core.channels.mqtt_gateway_channel import MqttGatewayChannel

TAG = __name__


class ChannelFactory:
    """
    通道工厂
    
    职责：
    1. 解析请求信息，识别通道类型
    2. 创建对应的通道实例
    3. 填充通道元信息
    
    Usage:
        # 从 WebSocket 自动创建
        channel = ChannelFactory.create_from_websocket(websocket)
        
        # 手动创建特定类型
        channel = ChannelFactory.create(ChannelType.WEBSOCKET, websocket, info)
    """
    
    _logger = logging.getLogger(TAG)
    
    @classmethod
    def create_from_websocket(cls, websocket) -> BaseChannel:
        """
        从 WebSocket 连接创建通道
        
        自动识别通道类型：
        - URL 包含 ?from=mqtt_gateway → MqttGatewayChannel
        - 其他 → WebSocketChannel
        
        Args:
            websocket: websockets 库的 WebSocket 连接对象
            
        Returns:
            BaseChannel: 对应的通道实例
        """
        # 解析请求信息
        headers = dict(websocket.request.headers) if websocket.request else {}
        request_path = websocket.request.path if websocket.request else ""
        
        # 解析 query parameters
        query_params = cls._parse_query_params(request_path)
        
        # 获取设备信息（优先从 query params，其次从 headers）
        device_id = (
            query_params.get("device-id") or 
            headers.get("device-id") or 
            "unknown"
        )
        client_id = (
            query_params.get("client-id") or 
            headers.get("client-id") or 
            device_id
        )
        agent_id = (
            query_params.get("agent-id") or 
            headers.get("agent-id")
        )
        
        # 获取客户端 IP
        client_ip = cls._get_client_ip(websocket, headers)
        
        # 判断通道类型
        is_mqtt_gateway = (
            "from=mqtt_gateway" in request_path or 
            query_params.get("from") == "mqtt_gateway"
        )
        channel_type = ChannelType.MQTT_GATEWAY.value if is_mqtt_gateway else ChannelType.WEBSOCKET.value
        
        # 创建通道信息
        info = ChannelInfo(
            channel_type=channel_type,
            device_id=device_id,
            client_id=client_id,
            client_ip=client_ip,
            headers=headers,
            query_params=query_params,
            extra={"agent_id": agent_id} if agent_id else {},
        )
        
        # 创建对应的通道实例
        if is_mqtt_gateway:
            cls._logger.info(f"创建 MQTT Gateway 通道: device={device_id}, client={client_id}")
            return MqttGatewayChannel(websocket, info)
        else:
            cls._logger.info(f"创建 WebSocket 直连通道: device={device_id}, client={client_id}")
            return WebSocketChannel(websocket, info)
    
    @classmethod
    def create(
        cls,
        channel_type: ChannelType,
        connection,
        info: Optional[ChannelInfo] = None,
        **kwargs
    ) -> BaseChannel:
        """
        手动创建指定类型的通道
        
        Args:
            channel_type: 通道类型
            connection: 底层连接对象
            info: 通道元信息（可选）
            **kwargs: 额外参数
            
        Returns:
            BaseChannel: 通道实例
            
        Raises:
            ValueError: 不支持的通道类型
        """
        if info is None:
            info = ChannelInfo(channel_type=channel_type.value)
        
        if channel_type == ChannelType.WEBSOCKET:
            return WebSocketChannel(connection, info)
        elif channel_type == ChannelType.MQTT_GATEWAY:
            return MqttGatewayChannel(connection, info)
        elif channel_type == ChannelType.WEBRTC:
            # 预留 WebRTC
            from core.channels.rtc_channel import WebRTCChannel
            return WebRTCChannel(info)
        elif channel_type == ChannelType.AGORA:
            # Agora RTC 通道
            from core.channels.rtc_channel import AgoraChannel
            return AgoraChannel(info)
        else:
            raise ValueError(f"不支持的通道类型: {channel_type}")
    
    @classmethod
    def create_agora_channel(
        cls,
        channel_name: str,
        uid: int,
        token: Optional[str] = None,
        remote_uid: int = 0,
        device_id: Optional[str] = None,
        **extra
    ) -> 'BaseChannel':
        """
        创建 Agora RTC 通道
        
        Args:
            channel_name: Agora 频道名称
            uid: 本地用户 ID
            token: 鉴权 Token（如果未提供，使用 App ID）
            remote_uid: 远程用户 ID（用于订阅）
            device_id: 设备 ID
            **extra: 额外参数
            
        Returns:
            AgoraChannel 实例
            
        Example:
            channel = ChannelFactory.create_agora_channel(
                channel_name="room_123",
                uid=12345,
                token="xxx",
            )
            await channel.join_channel()
        """
        from core.channels.rtc_channel import AgoraChannel
        from core.agora import AgoraServiceManager
        
        # 获取 App ID
        app_id = AgoraServiceManager.get_app_id()
        
        # 创建通道信息
        info = ChannelInfo(
            channel_type=ChannelType.AGORA.value,
            device_id=device_id or str(uid),
            client_id=str(uid),
            extra={
                "app_id": app_id,
                "channel_name": channel_name,
                "token": token,
                "uid": uid,
                "remote_uid": remote_uid,
                **extra,
            }
        )
        
        cls._logger.info(
            f"创建 Agora 通道: channel={channel_name}, uid={uid}, "
            f"remote_uid={remote_uid}"
        )
        
        return AgoraChannel(info)
    
    @classmethod
    def _parse_query_params(cls, path: str) -> dict:
        """解析 URL 查询参数"""
        try:
            parsed = urlparse(path)
            qs = parse_qs(parsed.query)
            # parse_qs 返回 dict[str, list[str]]，取每个参数的第一个值
            return {k: v[0] if v else None for k, v in qs.items()}
        except Exception as e:
            cls._logger.warning(f"解析 URL 参数失败: path={path}, error={e}")
            return {}
    
    @classmethod
    def _get_client_ip(cls, websocket, headers: dict) -> Optional[str]:
        """获取客户端 IP"""
        # 优先从代理头获取
        client_ip = headers.get("x-real-ip") or headers.get("x-forwarded-for")
        if client_ip:
            # X-Forwarded-For 可能包含多个 IP，取第一个
            return client_ip.split(",")[0].strip()
        
        # 从 WebSocket 连接获取
        if hasattr(websocket, 'remote_address') and websocket.remote_address:
            return websocket.remote_address[0]
        
        return None

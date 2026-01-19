"""
Transport Factory

Factory pattern for creating transport instances.
Supports dynamic registration of transport implementations.

Design Pattern: Factory Method + Registry
- Decouples transport creation from usage
- Supports runtime registration of new transport types
- Provides a clean API for transport instantiation
"""

from typing import Dict, Type, Optional

from .base import TransportBase
from .config import TransportConfig, TransportType


class TransportFactory:
    """Factory for creating transport instances
    
    Singleton factory that manages transport type registration
    and instantiation.
    
    Usage:
        # Register implementations
        TransportFactory.register("websocket", WebSocketTransport)
        TransportFactory.register("rtc", RTCTransport)
        
        # Create instances
        transport = TransportFactory.create("websocket", config)
    """
    
    _registry: Dict[str, Type[TransportBase]] = {}
    
    @classmethod
    def register(cls, transport_type: str, transport_class: Type[TransportBase]) -> None:
        """Register a transport implementation
        
        Args:
            transport_type: Type identifier (e.g., "websocket", "rtc")
            transport_class: Transport class to register
            
        Raises:
            ValueError: If transport type is already registered
        """
        if transport_type in cls._registry:
            raise ValueError(f"Transport type '{transport_type}' already registered")
        
        cls._registry[transport_type] = transport_class
    
    @classmethod
    def unregister(cls, transport_type: str) -> bool:
        """Unregister a transport implementation
        
        Args:
            transport_type: Type identifier to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if transport_type in cls._registry:
            del cls._registry[transport_type]
            return True
        return False
    
    @classmethod
    def create(cls, config: TransportConfig) -> TransportBase:
        """Create a transport instance from configuration
        
        Args:
            config: Transport configuration
            
        Returns:
            TransportBase instance
            
        Raises:
            ValueError: If transport type is not registered
        """
        transport_type = config.transport_type.value
        
        if transport_type not in cls._registry:
            raise ValueError(
                f"Transport type '{transport_type}' not registered. "
                f"Available types: {list(cls._registry.keys())}"
            )
        
        transport_class = cls._registry[transport_type]
        return transport_class(config)
    
    @classmethod
    def create_by_type(
        cls, 
        transport_type: str, 
        config: Optional[TransportConfig] = None,
        **kwargs
    ) -> TransportBase:
        """Create a transport instance by type string
        
        Convenience method that creates config automatically if needed.
        
        Args:
            transport_type: Type identifier
            config: Optional pre-built config
            **kwargs: Config parameters (used if config not provided)
            
        Returns:
            TransportBase instance
        """
        if config is None:
            from .config import create_config
            config = create_config(transport_type, **kwargs)
        
        return cls.create(config)
    
    @classmethod
    def get_registered_types(cls) -> list:
        """Get list of registered transport types
        
        Returns:
            List of registered type identifiers
        """
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, transport_type: str) -> bool:
        """Check if a transport type is registered
        
        Args:
            transport_type: Type identifier
            
        Returns:
            True if registered
        """
        return transport_type in cls._registry
    
    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered transports (for testing)"""
        cls._registry.clear()

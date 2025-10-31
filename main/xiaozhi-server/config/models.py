"""
Configuration models for xiaozhi-server using Pydantic.

This module defines strongly-typed configuration models that provide:
- Type validation at runtime
- IDE auto-completion
- Clear documentation
- Default values
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class ModelConfig(BaseModel):
    """Model configuration for components (VAD, STT, LLM, TTS)."""
    
    type: Literal["local", "remote"] = Field(
        description="Model type: 'local' for local models, 'remote' for API-based models"
    )
    name: str = Field(description="Model name/identifier")
    dir: Optional[str] = Field(
        default=None,
        description="Model directory path (required for local models)"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="API base URL (required for remote models)"
    )
    
    @model_validator(mode='after')
    def validate_model_requirements(self):
        """Validate that local models have dir and remote models have base_url."""
        if self.type == "local" and not self.dir:
            raise ValueError("'dir' is required for local models")
        if self.type == "remote" and not self.base_url:
            raise ValueError("'base_url' is required for remote models")
        return self


class AuthConfig(BaseModel):
    """Authentication configuration."""
    
    enabled: bool = Field(default=False, description="Enable authentication")
    allowed_devices: List[str] = Field(
        default_factory=list,
        description="Whitelist of device IDs that bypass token authentication"
    )


class ServerConfig(BaseModel):
    """Server listening configuration."""
    
    ip: str = Field(default="0.0.0.0", description="Server listening IP address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server listening port")
    websocket: str = Field(
        default="ws://localhost:8000/xiaozhi/v1/",
        description="WebSocket endpoint URL sent to devices"
    )
    auth: AuthConfig = Field(default_factory=AuthConfig, description="Authentication settings")


class LogConfig(BaseModel):
    """Logging configuration."""
    
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {extra[tag]} - {message}",
        description="Console log format"
    )
    log_format_file: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {extra[tag]} - {message}",
        description="File log format"
    )
    log_level: str = Field(default="INFO", description="Log level: INFO, DEBUG, WARNING, ERROR")
    log_dir: str = Field(default="tmp", description="Log directory path")
    log_file: str = Field(default="server.log", description="Log file name")
    data_dir: str = Field(default="data", description="Data directory path")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f'log_level must be one of {allowed}')
        return v_upper
    

class AudioParams(BaseModel):
    """Audio parameters configuration."""
    
    format: str = Field(default="opus", description="Audio format (opus, pcm, wav)")
    sample_rate: int = Field(default=16000, gt=0, description="Audio sample rate in Hz")
    channels: int = Field(default=1, ge=1, le=2, description="Number of audio channels (1=mono, 2=stereo)")
    frame_duration: int = Field(default=60, gt=0, description="Audio frame duration in milliseconds")
    


class VADConfig(BaseModel):
    """Voice Activity Detection configuration."""
    
    provider: str = Field(description="VAD provider name (e.g., 'silero')")
    model: ModelConfig = Field(description="VAD model configuration")
    output_dir: str = Field(default="tmp/", description="Output directory for VAD results")


class STTConfig(BaseModel):
    """Speech-to-Text configuration."""
    
    provider: str = Field(description="STT provider name (e.g., 'groq', 'funasr')")
    model: ModelConfig = Field(description="STT model configuration")


class LLMConfig(BaseModel):
    """Large Language Model configuration."""
    
    provider: str = Field(description="LLM provider name (e.g., 'groq', 'openai', 'chatglm')")
    model: ModelConfig = Field(description="LLM model configuration")


class TTSConfig(BaseModel):
    """Text-to-Speech configuration."""
    
    provider: str = Field(description="TTS provider name (e.g., 'cartesia', 'edge', 'doubao')")
    model: Optional[ModelConfig] = Field(
        default=None,
        description="TTS model configuration (optional)"
    )


class MemoryConfig(BaseModel):
    """Memory module configuration."""
    
    provider: str = Field(description="Memory provider name (e.g., 'mem0', 'nomem')")
    


class ComponentsConfig(BaseModel):
    """AI components configuration for VAD, STT, LLM, TTS, and Memory."""
    
    vad: VADConfig = Field(description="Voice Activity Detection configuration")
    stt: STTConfig = Field(description="Speech-to-Text configuration")
    llm: LLMConfig = Field(description="Large Language Model configuration")
    tts: TTSConfig = Field(description="Text-to-Speech configuration")
    Memory: MemoryConfig = Field(
        description="Memory module configuration",
        alias="Memory"  # Keep uppercase 'M' to match YAML
    )
    
    model_config = ConfigDict(extra='allow', populate_by_name=True)


class Config(BaseModel):
    """
    Main configuration model for xiaozhi-server.
    
    This strongly-typed configuration provides:
    - Type safety and validation
    - IDE auto-completion
    - Clear documentation for all fields
    - Sensible default values
    """
    
    # Server configuration
    server: ServerConfig = Field(
        default_factory=ServerConfig,
        description="Server listening and connection settings"
    )
    
    # Logging configuration
    log: LogConfig = Field(
        default_factory=LogConfig,
        description="Logging settings"
    )
    
    # Audio processing settings
    delete_audio: bool = Field(
        default=True,
        description="Delete audio files after processing to save disk space"
    )
    close_connection_no_voice_time: int = Field(
        default=120,
        ge=0,
        description="Seconds before closing connection with no voice input"
    )
    tts_timeout: int = Field(
        default=10,
        gt=0,
        description="TTS request timeout in seconds"
    )
    enable_greeting: bool = Field(
        default=True,
        description="Enable greeting message when connection starts"
    )
    
    # Audio parameters
    audio_params: AudioParams = Field(
        default_factory=AudioParams,
        description="Audio format and encoding parameters"
    )
    
    # MCP endpoint
    mcp_endpoint: str = Field(
        default="your mcp endpoint websocket address",
        description="MCP endpoint WebSocket address"
    )
    
    # Prompt template
    prompt_template: str = Field(
        default="agent-base-prompt.txt",
        description="System prompt template file path"
    )
    
    # AI Components configuration
    components: ComponentsConfig = Field(
        description="AI components (VAD, STT, LLM, TTS, Memory) configuration"
    )
    
    model_config = ConfigDict(
        extra='allow',  # Allow extra fields for flexibility during migration
        validate_assignment=True,  # Validate values when they're assigned
        str_strip_whitespace=True,  # Strip whitespace from string values
        use_enum_values=True,  # Use enum values instead of enum instances
    )
    
    def get_component_config(self, component_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific component.
        
        Args:
            component_type: Type of component ('vad', 'stt', 'llm', 'tts', 'Memory')
            
        Returns:
            Component configuration as a dictionary
            
        Example:
            >>> config.get_component_config('llm')
            {'provider': 'groq', 'model': {'type': 'remote', 'name': 'openai/gpt-oss-120b', ...}, ...}
        """
        component = getattr(self.components, component_type, None)
        if component is None:
            raise ValueError(f"Unknown component type: {component_type}")
        return component.model_dump()
    
    def get_provider_name(self, component_type: str) -> str:
        """
        Get the provider name for a specific component.
        
        Args:
            component_type: Type of component ('vad', 'stt', 'llm', 'tts', 'Memory')
            
        Returns:
            Provider name as string
            
        Example:
            >>> config.get_provider_name('llm')
            'groq'
        """
        component = getattr(self.components, component_type, None)
        if component is None:
            raise ValueError(f"Unknown component type: {component_type}")
        return component.provider


# Export all models
__all__ = [
    'Config',
    'ServerConfig',
    'AuthConfig',
    'LogConfig',
    'AudioParams',
    'ComponentsConfig',
    'ModelConfig',
    'VADConfig',
    'STTConfig',
    'LLMConfig',
    'TTSConfig',
    'MemoryConfig',
]


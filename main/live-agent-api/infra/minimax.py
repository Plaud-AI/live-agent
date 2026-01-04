"""
MiniMax TTS infrastructure - MiniMax Text-to-Speech client
Implements HTTP streaming API for TTS synthesis
Reference: https://platform.minimax.io/docs/api-reference/speech-t2a-http
"""
import json
import httpx
from typing import Optional, Literal

from config import settings
from config.logger import setup_logging

TAG = __name__
logger = setup_logging(TAG)


class MinimaxTTSClient:
    """MiniMax TTS Client using HTTP streaming API"""
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.minimax.io/v1/t2a_v2",
        model: str = "speech-2.6-turbo",
        default_voice_id: str = "female-shaonv"
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.default_voice_id = default_voice_id
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
    
    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: Literal["pcm", "mp3", "wav"] = "pcm",
        sample_rate: int = 16000,
        speed: float = 1.0,
        vol: float = 1.0,
        pitch: int = 0,
        emotion: str = "happy",
    ) -> bytes:
        """
        Synthesize text to speech using MiniMax API
        
        Args:
            text: Text to synthesize
            voice_id: MiniMax voice ID (e.g., 'female-shaonv', 'male-qn-qingse')
            format: Audio format (pcm, mp3, wav)
            sample_rate: Sample rate in Hz
            speed: Speech speed (0.5 - 2.0)
            vol: Volume (0.1 - 1.0)
            pitch: Pitch adjustment (-12 to 12)
            emotion: Emotion tone (happy, sad, angry, fearful, disgusted, surprised, calm, fluent)
            
        Returns:
            Audio bytes in requested format
        """
        voice = voice_id or self.default_voice_id
        
        # Build payload matching MiniMax API structure
        payload = {
            "model": self.model,
            "text": text,
            "stream": True,  # Use streaming for SSE response
            "voice_setting": {
                "voice_id": voice,
                "speed": speed,
                "vol": vol,
                "pitch": pitch,
                "emotion": emotion,
            },
            "audio_setting": {
                "sample_rate": sample_rate,
                "format": format,
                "channel": 1,
            },
        }
        
        audio_data = bytearray()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                self.api_url,
                headers=self.headers,
                content=json.dumps(payload),
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.bind(tag=TAG).error(
                        f"MiniMax TTS request failed: {response.status_code}, {error_text}"
                    )
                    raise Exception(f"MiniMax TTS failed: {response.status_code}")
                
                # Parse SSE (Server-Sent Events) stream
                # Format: data: {"data": {"audio": "<hex>", "status": 1}, ...}\n\n
                buffer = b""
                async for chunk in response.aiter_bytes():
                    buffer += chunk
                    
                    # Parse complete SSE data blocks
                    while True:
                        header_pos = buffer.find(b"data: ")
                        if header_pos == -1:
                            break
                        
                        end_pos = buffer.find(b"\n\n", header_pos)
                        if end_pos == -1:
                            break
                        
                        # Extract JSON block
                        json_str = buffer[header_pos + 6:end_pos].decode("utf-8")
                        buffer = buffer[end_pos + 2:]
                        
                        try:
                            data = json.loads(json_str)
                            status = data.get("data", {}).get("status", 1)
                            audio_hex = data.get("data", {}).get("audio")
                            
                            # Only process status=1 valid audio blocks
                            # status=2 is summary block (ignore)
                            if status == 1 and audio_hex:
                                audio_data.extend(bytes.fromhex(audio_hex))
                        except json.JSONDecodeError as e:
                            logger.bind(tag=TAG).warning(f"Failed to parse SSE data: {e}")
                            continue
        
        return bytes(audio_data)


# Global client instance
_minimax_client: Optional[MinimaxTTSClient] = None


def get_minimax_tts() -> Optional[MinimaxTTSClient]:
    """
    Dependency to get MiniMax TTS client
    
    Returns:
        MiniMax TTS client or None if not configured
    """
    return _minimax_client


async def init_minimax_tts():
    """
    Initialize MiniMax TTS client (called in lifespan startup)
    """
    global _minimax_client
    
    if not settings.MINIMAX_API_KEY:
        logger.bind(tag=TAG).warning(
            "MINIMAX_API_KEY not configured, MiniMax TTS will be unavailable"
        )
        return
    
    try:
        _minimax_client = MinimaxTTSClient(
            api_key=settings.MINIMAX_API_KEY,
            api_url=settings.MINIMAX_API_URL,
            model=settings.MINIMAX_MODEL,
            default_voice_id=settings.MINIMAX_DEFAULT_VOICE_ID,
        )
        logger.bind(tag=TAG).info("MiniMax TTS client initialized")
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to initialize MiniMax TTS: {e}")


async def close_minimax_tts():
    """
    Close MiniMax TTS client (called in lifespan shutdown)
    """
    global _minimax_client
    _minimax_client = None
    logger.bind(tag=TAG).info("MiniMax TTS client closed")


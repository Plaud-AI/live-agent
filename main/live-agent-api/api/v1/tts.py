"""
TTS (Text-to-Speech) API endpoints
简单封装 Fish Audio / MiniMax TTS，供移动端/嵌入式设备调用
支持 mp3, wav, pcm, opus 格式输出
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Literal

from fishaudio.types.tts import TTSConfig
from infra.fishaudio import get_fish_audio
from infra.minimax import get_minimax_tts
from config.logger import setup_logging
from utils.opus_encoder import pcm_to_opus_stream, pcm_to_opus_raw

TAG = __name__
logger = setup_logging(TAG)

router = APIRouter()


class TTSSynthesizeRequest(BaseModel):
    """TTS 合成请求"""
    text: str  # 要合成的文本
    voice_id: Optional[str] = None  # 音色 ID (Fish Audio reference_id 或 MiniMax voice_id)
    provider: Literal["fishspeech", "minimax"] = "fishspeech"  # TTS 提供商
    format: Literal["mp3", "wav", "pcm", "opus", "opus_raw"] = "mp3"  # 输出格式
    sample_rate: int = 16000  # 采样率


async def _synthesize_fish(text: str, voice_id: Optional[str], format: str, sample_rate: int) -> bytes:
    """Fish Audio TTS 合成"""
    fish_client = get_fish_audio()
    if fish_client is None:
        raise HTTPException(status_code=503, detail="Fish Audio not configured")
    
    is_opus = format in ("opus", "opus_raw")
    fish_format = "pcm" if is_opus else format
    
    tts_config = TTSConfig(
        format=fish_format,
        sample_rate=sample_rate,
        normalize=True,
        latency="balanced",
    )
    
    audio_bytes = await fish_client.tts.convert(
        text=text,
        reference_id=voice_id if voice_id and voice_id.lower() != "default" else None,
        model="speech-1.6",
        config=tts_config,
    )
    
    if is_opus:
        if format == "opus":
            audio_bytes = pcm_to_opus_stream(audio_bytes, sample_rate=sample_rate)
        else:
            audio_bytes = pcm_to_opus_raw(audio_bytes, sample_rate=sample_rate)
    
    return audio_bytes


async def _synthesize_minimax(text: str, voice_id: Optional[str], format: str, sample_rate: int) -> bytes:
    """MiniMax TTS 合成"""
    minimax_client = get_minimax_tts()
    if minimax_client is None:
        raise HTTPException(status_code=503, detail="MiniMax TTS not configured")
    
    is_opus = format in ("opus", "opus_raw")
    # MiniMax 只支持 pcm/mp3，opus 需要从 pcm 转换
    mm_format = "pcm" if is_opus or format == "wav" else format
    
    audio_bytes = await minimax_client.synthesize(
        text=text,
        voice_id=voice_id,
        format=mm_format,
        sample_rate=sample_rate,
    )
    
    if is_opus:
        if format == "opus":
            audio_bytes = pcm_to_opus_stream(audio_bytes, sample_rate=sample_rate)
        else:
            audio_bytes = pcm_to_opus_raw(audio_bytes, sample_rate=sample_rate)
    
    return audio_bytes


@router.post("/synthesize", summary="Text to Speech Synthesis")
async def synthesize_speech(request: TTSSynthesizeRequest):
    """
    将文本合成为语音
    
    - **text**: 要合成的文本内容
    - **voice_id**: 音色 ID (Fish Audio reference_id 或 MiniMax voice_id)
    - **provider**: TTS 提供商 (fishspeech 或 minimax)
    - **format**: 输出格式 (mp3, wav, pcm, opus, opus_raw)
    - **sample_rate**: 采样率，默认 16000 Hz
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    text = request.text.strip()
    if len(text) > 1000:
        raise HTTPException(status_code=400, detail="Text too long, max 1000 characters")
    
    logger.bind(tag=TAG).info(
        f"TTS: provider={request.provider}, voice={request.voice_id}, format={request.format}"
    )
    
    try:
        # 根据 provider 路由
        if request.provider == "minimax":
            audio_bytes = await _synthesize_minimax(
                text, request.voice_id, request.format, request.sample_rate
            )
        else:
            audio_bytes = await _synthesize_fish(
                text, request.voice_id, request.format, request.sample_rate
            )
        
        logger.bind(tag=TAG).info(f"TTS done: {len(audio_bytes)} bytes")
        
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "pcm": "audio/pcm",
            "opus": "audio/opus",
            "opus_raw": "audio/opus"
        }
        
        return Response(
            content=audio_bytes,
            media_type=content_type_map.get(request.format, "audio/mpeg"),
            headers={"Content-Disposition": f"inline; filename=tts.{request.format.replace('_raw', '')}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.bind(tag=TAG).error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


@router.get("/health", summary="TTS Service Health Check")
async def tts_health():
    """检查 TTS 服务可用性"""
    fish = get_fish_audio()
    minimax = get_minimax_tts()
    
    return {
        "fishspeech": "available" if fish else "unavailable",
        "minimax": "available" if minimax else "unavailable",
    }

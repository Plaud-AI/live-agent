"""
TTS (Text-to-Speech) API endpoints
简单封装 Fish Audio TTS，供移动端/嵌入式设备调用
支持 mp3, wav, pcm, opus 格式输出
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Literal

from fishaudio.types.tts import TTSConfig
from infra.fishaudio import get_fish_audio
from config.logger import setup_logging
from utils.opus_encoder import pcm_to_opus_stream, pcm_to_opus_raw

TAG = __name__
logger = setup_logging(TAG)

router = APIRouter()


class TTSSynthesizeRequest(BaseModel):
    """TTS 合成请求"""
    text: str  # 要合成的文本
    voice_id: Optional[str] = None  # 可选的音色 ID (Fish Audio voice reference_id)
    format: Literal["mp3", "wav", "pcm", "opus", "opus_raw"] = "mp3"  # 输出格式
    sample_rate: int = 16000  # 采样率（仅对 opus 格式有效），默认 16000 Hz


@router.post("/synthesize", summary="Text to Speech Synthesis")
async def synthesize_speech(
    request: TTSSynthesizeRequest,
    fish_client = Depends(get_fish_audio)
):
    """
    将文本合成为语音
    
    - **text**: 要合成的文本内容
    - **voice_id**: 可选，Fish Audio 音色 ID。不提供则使用默认音色
    - **format**: 输出格式，支持:
        - mp3 (默认): MP3 格式
        - wav: WAV 格式
        - pcm: 原始 PCM 数据 (16位小端，单声道)
        - opus: Opus 格式（带帧头，与语音对话返回给设备的格式一致）
        - opus_raw: 原始 Opus 帧数据（无帧头）
    - **sample_rate**: 采样率，仅对 opus/opus_raw 格式有效，默认 16000 Hz
    
    Returns:
        音频文件流
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    text = request.text.strip()
    
    # 限制文本长度（避免过长的请求）
    if len(text) > 1000:
        raise HTTPException(status_code=400, detail="Text too long, max 1000 characters")
    
    # 处理 voice_id: "default"、空字符串、None 都使用默认音色
    voice_id = request.voice_id
    if voice_id and voice_id.lower() == "default":
        voice_id = None  # Fish Audio 会使用默认音色
    
    logger.bind(tag=TAG).info(
        f"TTS request: text='{text[:50]}...', voice_id={voice_id}, "
        f"format={request.format}, sample_rate={request.sample_rate}"
    )
    
    try:
        # 判断是否需要 opus 格式转换
        is_opus_format = request.format in ("opus", "opus_raw")
        
        # Fish Audio API 请求格式：opus 需要先获取 pcm 再转换
        fish_format = "pcm" if is_opus_format else request.format
        
        # 构建 TTS 配置（参考 fish_single_stream.py 的配置）
        # Fish Audio 支持 sample_rate 参数，会返回对应采样率的 PCM 数据
        tts_config = TTSConfig(
            format=fish_format,
            sample_rate=request.sample_rate,  # 使用请求指定的采样率
            normalize=True,
            latency="balanced",
        )
        
        # 调用 Fish Audio TTS（与 fish_single_stream.py 保持一致的调用方式）
        audio_bytes = await fish_client.tts.convert(
            text=text,
            reference_id=voice_id,  # 可以为 None，使用默认音色
            model="speech-1.6",  # 指定模型，与 fish_single_stream.py 一致
            config=tts_config,
        )
        
        logger.bind(tag=TAG).info(f"TTS from Fish Audio: {len(audio_bytes)} bytes ({fish_format}, {request.sample_rate}Hz)")
        
        # 如果需要 opus 格式，进行 PCM -> Opus 转换
        if is_opus_format:
            if request.format == "opus":
                # 带帧头的 opus 格式（与语音对话返回给设备的格式一致）
                audio_bytes = pcm_to_opus_stream(audio_bytes, sample_rate=request.sample_rate)
            else:
                # 原始 opus 帧数据
                audio_bytes = pcm_to_opus_raw(audio_bytes, sample_rate=request.sample_rate)
            
            logger.bind(tag=TAG).info(f"Opus encoded: {len(audio_bytes)} bytes")
        
        # 根据格式返回不同的 Content-Type
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "pcm": "audio/pcm",
            "opus": "audio/opus",
            "opus_raw": "audio/opus"
        }
        content_type = content_type_map.get(request.format, "audio/mpeg")
        
        # 文件扩展名
        extension_map = {
            "opus": "opus",
            "opus_raw": "opus"
        }
        extension = extension_map.get(request.format, request.format)
        
        return Response(
            content=audio_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename=tts.{extension}"
            }
        )
        
    except Exception as e:
        logger.bind(tag=TAG).error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


@router.get("/health", summary="TTS Service Health Check")
async def tts_health(fish_client = Depends(get_fish_audio)):
    """
    检查 TTS 服务是否可用
    """
    try:
        # 简单检查 Fish Audio 客户端是否可用
        if fish_client is None:
            return {"status": "unavailable", "message": "Fish Audio client not initialized"}
        return {"status": "available", "message": "TTS service is ready"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

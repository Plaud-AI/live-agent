import asyncio

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from infra import get_db
from infra.fishaudio import get_fish_audio
from services.agent_service import agent_service
from services.device_service import device_service
from services.chat_service import chat_service
from services.voice_service import voice_service
from utils.response import success_response
from schemas.agent import AgentConfigResponse, VoiceConfig, RecentMessage
from schemas.device import DefaultAgentResponse, DeviceAgentResolveResponse

router = APIRouter()


def _parse_tz_offset(tz_offset: str) -> int:
    """
    Parse timezone offset string to hours
    
    Supports formats: "UTC+8", "UTC-7", "+8", "-5", "0"
    
    Returns:
        Offset hours (positive for east, negative for west)
    """
    if not tz_offset:
        return 0
    
    tz_str = tz_offset.strip().upper()
    
    # Remove "UTC" prefix if present
    if tz_str.startswith("UTC"):
        tz_str = tz_str[3:]
    
    if not tz_str or tz_str in ("+0", "-0", "0"):
        return 0
    
    try:
        return int(tz_str)
    except ValueError:
        return 0


@router.get("/agents/{agent_id}/config", summary="Get agent config for backend services")
async def get_agent_config(
    agent_id: str,
    tz_offset: str = Query(default="UTC+0", description="Client timezone offset, e.g. UTC+8, UTC-7"),
    max_history_rounds: int = Query(default=10, ge=0, le=50, description="Max conversation rounds to load for context"),
    db: AsyncSession = Depends(get_db),
    fish_client = Depends(get_fish_audio)
):
    """
    Get agent runtime configuration for xiaozhi-server
    
    This is an internal API for service-to-service communication:
    - No authentication required
    - Returns agent config with voice info (voice_id, reference_id, provider)
    - Used by xiaozhi-server to drive AI conversations
    
    Flow:
    1. Get agent config by agent_id
    2. Parallel fetch: voice language + today's message check + recent messages
    3. Enable greeting only if no messages today (reduce user annoyance)
    4. Return recent messages for dialogue context loading
    """
    # Parse timezone offset at API layer
    tz_offset_hours = _parse_tz_offset(tz_offset)
    
    # Step 1: Get agent config
    agent = await agent_service.get_agent_detail(db=db, agent_id=agent_id)
    
    # Step 2: Get voice config from database
    voice_config_data = await voice_service.get_voice_config(db=db, voice_id=agent.voice_id)
    voice_config = VoiceConfig(**voice_config_data) if voice_config_data else None
    
    # Step 3: Parallel fetch - Fish Audio language, today's message check, and recent messages
    async def fetch_language():
        if not voice_config:
            return None
        try:
            # Use reference_id to fetch from Fish Audio
            fish_voice = await fish_client.voices.get(voice_config.reference_id)
            if fish_voice and hasattr(fish_voice, 'languages') and fish_voice.languages:
                return fish_voice.languages[0] if isinstance(fish_voice.languages, list) else fish_voice.languages
        except Exception as e:
            print(f"Warning: Failed to fetch voice language for {voice_config.reference_id}: {e}")
        return None
    
    async def check_has_messages_today():
        return await chat_service.has_messages_today(db=db, agent_id=agent_id, tz_offset_hours=tz_offset_hours)
    
    async def fetch_recent_messages():
        if max_history_rounds <= 0:
            return []
        return await chat_service.get_recent_rounds(db=db, agent_id=agent_id, max_rounds=max_history_rounds)
    
    # Execute all tasks in parallel
    language, has_messages_today, recent_messages = await asyncio.gather(
        fetch_language(),
        check_has_messages_today(),
        fetch_recent_messages()
    )
    
    # Step 4: Determine greeting behavior
    # Only enable greeting if no messages today (reduce repeated greeting annoyance)
    enable_greeting = not has_messages_today
    greeting = agent.voice_opening if enable_greeting else None
    
    # Step 5: Convert recent messages to simplified format
    # msg.content is List[MessageBody], need to convert to List[dict]
    # Filter out audio content (not useful for LLM context)
    recent_msgs = None
    if recent_messages:
        recent_msgs = []
        for msg in recent_messages:
            filtered_content = [
                part.model_dump() for part in msg.content 
                if part.message_type != "audio"
            ]
            # Skip messages with no content after filtering
            if filtered_content:
                recent_msgs.append(RecentMessage(role=msg.role, content=filtered_content))
        # Set to None if empty after filtering
        recent_msgs = recent_msgs if recent_msgs else None
    
    # Step 6: Build response
    response = AgentConfigResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        voice=voice_config,
        language=language,
        instruction=agent.instruction,
        voice_opening=agent.voice_opening,  # Always return for wakeup greeting
        voice_closing=agent.voice_closing,
        enable_greeting=enable_greeting,
        greeting=greeting,
        recent_messages=recent_msgs,
    )
    
    return success_response(data=response.model_dump(exclude_none=True))


@router.get("/devices/{device_id}/agent-by-wake", summary="Resolve agent by wake word or default")
async def resolve_agent_by_wake(
    device_id: str,
    wake_word: str | None = Query(None, description="Wake word to match"),
    db: AsyncSession = Depends(get_db),
    fish_client = Depends(get_fish_audio),
):
    """
    Resolve device agent by wake word; fallback to default binding.
    Returns agent config for runtime consumption.
    """
    resolved = await device_service.resolve_agent_by_wake_word(
        db=db,
        device_id=device_id,
        wake_word=wake_word,
    )

    # Get voice config from database using raw_voice_id
    agent_cfg = resolved.agent_config
    voice_config_data = await voice_service.get_voice_config(db=db, voice_id=agent_cfg.raw_voice_id)
    voice_config = VoiceConfig(**voice_config_data) if voice_config_data else None
    agent_cfg.voice = voice_config
    
    # Enrich language via Fish Audio if voice exists
    language = agent_cfg.language
    if voice_config and language is None:
        try:
            fish_voice = await fish_client.voices.get(voice_config.reference_id)
            if fish_voice and hasattr(fish_voice, "languages") and fish_voice.languages:
                language = (
                    fish_voice.languages[0]
                    if isinstance(fish_voice.languages, list)
                    else fish_voice.languages
                )
        except Exception:
            language = None
    agent_cfg.language = language

    return success_response(
        data=DeviceAgentResolveResponse(
            device_id=resolved.device_id,
            agent_id=resolved.agent_id,
            owner_id=resolved.owner_id,  # Device owner's user_id for memory storage
            is_default=resolved.is_default,
            match_type=resolved.match_type,
            agent_config=agent_cfg,
        ).model_dump()
    )


@router.get("/devices/{device_id}/default-agent", summary="Get device default agent (internal)")
async def get_default_agent(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    fish_client = Depends(get_fish_audio),
):
    """
    Get default agent binding for a device (fallback to latest).
    """
    binding, agent = await device_service.get_default_agent(db=db, device_id=device_id)

    # Get voice config from database
    voice_config_data = await voice_service.get_voice_config(db=db, voice_id=agent.voice_id)
    voice_config = VoiceConfig(**voice_config_data) if voice_config_data else None
    
    # Enrich language via Fish Audio
    language = None
    if voice_config:
        try:
            fish_voice = await fish_client.voices.get(voice_config.reference_id)
            if fish_voice and hasattr(fish_voice, "languages") and fish_voice.languages:
                language = (
                    fish_voice.languages[0]
                    if isinstance(fish_voice.languages, list)
                    else fish_voice.languages
                )
        except Exception:
            language = None

    agent_cfg = AgentConfigResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        voice=voice_config,
        language=language,
        instruction=agent.instruction,
        voice_opening=agent.voice_opening,
        voice_closing=agent.voice_closing,
    )

    return success_response(
        data=DefaultAgentResponse(
            device_id=device_id,
            agent=agent_cfg,
            is_default=binding.is_default,
        ).model_dump()
    )

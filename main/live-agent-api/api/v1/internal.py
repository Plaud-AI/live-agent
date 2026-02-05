import asyncio
import time
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from infra import get_db, AsyncSessionLocal
from infra.fishaudio import get_fish_audio
from infra.redis import redis_client, Cache
from services.agent_service import agent_service
from services.device_service import device_service
from services.chat_service import chat_service
from services.voice_service import voice_service
from utils.response import success_response
from schemas.agent import AgentConfigResponse, VoiceConfig, RecentMessage
from schemas.device import DefaultAgentResponse, DeviceAgentResolveResponse

router = APIRouter()


# ==================== Warmup 预热相关 ====================

# xiaozhi-server 兼容的 Redis key 前缀
XIAOZHI_CACHE_PREFIX = "xiaozhi:"
# 预热缓存 TTL（秒）
WARMUP_CACHE_TTL = 600


class WarmupRequest(BaseModel):
    """预热请求"""
    user_id: Optional[str] = None
    agent_ids: Optional[List[str]] = None


class WarmupResponse(BaseModel):
    """预热响应"""
    warmed_agents: List[str]
    failed_agents: List[str]
    total_time_ms: float


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


# ==================== 预热接口 ====================

async def _build_agent_config_for_warmup(
    db: AsyncSession,
    agent_id: str,
    fish_client,
    tz_offset: str = "UTC+0",
    max_history_rounds: int = 10,
) -> Optional[dict]:
    """
    构建 Agent 配置用于预热（复用 get_agent_config 逻辑）
    
    Returns:
        Agent 配置字典，或 None 如果失败
    """
    try:
        tz_offset_hours = _parse_tz_offset(tz_offset)
        
        # Get agent config
        agent = await agent_service.get_agent_detail(db=db, agent_id=agent_id)
        
        # Get voice config
        voice_config_data = await voice_service.get_voice_config(db=db, voice_id=agent.voice_id)
        voice_config = VoiceConfig(**voice_config_data) if voice_config_data else None
        
        # Parallel fetch
        async def fetch_language():
            if not voice_config:
                return None
            try:
                fish_voice = await fish_client.voices.get(voice_config.reference_id)
                if fish_voice and hasattr(fish_voice, 'languages') and fish_voice.languages:
                    return fish_voice.languages[0] if isinstance(fish_voice.languages, list) else fish_voice.languages
            except Exception:
                pass
            return None
        
        async def check_has_messages_today():
            return await chat_service.has_messages_today(db=db, agent_id=agent_id, tz_offset_hours=tz_offset_hours)
        
        async def fetch_recent_messages():
            if max_history_rounds <= 0:
                return []
            return await chat_service.get_recent_rounds(db=db, agent_id=agent_id, max_rounds=max_history_rounds)
        
        language, has_messages_today, recent_messages = await asyncio.gather(
            fetch_language(),
            check_has_messages_today(),
            fetch_recent_messages()
        )
        
        enable_greeting = not has_messages_today
        greeting = agent.voice_opening if enable_greeting else None
        
        recent_msgs = None
        if recent_messages:
            recent_msgs = []
            for msg in recent_messages:
                filtered_content = [
                    part.model_dump() for part in msg.content 
                    if part.message_type != "audio"
                ]
                if filtered_content:
                    recent_msgs.append(RecentMessage(role=msg.role, content=filtered_content))
            recent_msgs = recent_msgs if recent_msgs else None
        
        response = AgentConfigResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            voice=voice_config,
            language=language,
            instruction=agent.instruction,
            voice_opening=agent.voice_opening,
            voice_closing=agent.voice_closing,
            enable_greeting=enable_greeting,
            greeting=greeting,
            recent_messages=recent_msgs,
        )
        
        return response.model_dump(exclude_none=True)
    except Exception as e:
        print(f"[Warmup] Failed to build config for agent {agent_id}: {e}")
        return None


def _make_xiaozhi_cache_key(agent_id: str, timezone: str = "UTC+0") -> str:
    """
    生成 xiaozhi-server 兼容的 Redis key
    
    格式: xiaozhi::agent_config:{agent_id}:{timezone}
    """
    return f"{XIAOZHI_CACHE_PREFIX}:agent_config:{agent_id}:{timezone}"


async def _write_warmup_cache(key: str, config: dict, ttl: int = WARMUP_CACHE_TTL) -> bool:
    """
    写入预热缓存（xiaozhi-server 兼容格式）
    
    xiaozhi-server 期望的数据格式:
    {
        "value": <config>,
        "timestamp": <time>
    }
    """
    try:
        serialized = json.dumps({
            "value": config,
            "timestamp": time.time(),
        }, ensure_ascii=False, default=str)
        
        await redis_client.client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        print(f"[Warmup] Failed to write cache for key {key}: {e}")
        return False


@router.post("/warmup", summary="预热 Agent 配置缓存")
async def warmup_agent_configs(
    request: WarmupRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    fish_client = Depends(get_fish_audio),
):
    """
    预热 Agent 配置到 Redis 缓存
    
    使用场景：
    - 用户登录 APP 后调用，提前加载常用 Agent 配置
    - 减少首次对话的冷启动延迟
    
    请求参数：
    - user_id: 用户 ID（可选，用于获取用户的 agents）
    - agent_ids: 指定预热的 Agent ID 列表（可选）
    
    逻辑：
    - 如果指定了 agent_ids，预热这些 agents
    - 如果只指定了 user_id，预热用户最近使用的 agents（最多 5 个）
    - 将配置写入 Redis，key 格式与 xiaozhi-server 兼容
    """
    start_time = time.time()
    
    agent_ids_to_warmup = []
    
    # 确定要预热的 agent 列表
    if request.agent_ids:
        agent_ids_to_warmup = request.agent_ids
    elif request.user_id:
        # 获取用户的 agents（最多 5 个）
        try:
            agents = await agent_service.list_agents(
                db=db, 
                owner_id=request.user_id, 
                limit=5
            )
            agent_ids_to_warmup = [a.agent_id for a in agents]
        except Exception as e:
            print(f"[Warmup] Failed to fetch user agents: {e}")
    
    if not agent_ids_to_warmup:
        return success_response(data=WarmupResponse(
            warmed_agents=[],
            failed_agents=[],
            total_time_ms=0,
        ).model_dump())
    
    warmed_agents = []
    failed_agents = []
    
    # 并行预热所有 agents（每个 agent 使用独立的数据库会话，避免并发冲突）
    async def warmup_single_agent(agent_id: str) -> tuple[str, bool]:
        # 创建独立的数据库会话，避免 SQLAlchemy AsyncSession 并发问题
        async with AsyncSessionLocal() as agent_db:
            config = await _build_agent_config_for_warmup(
                db=agent_db,
                agent_id=agent_id,
                fish_client=fish_client,
            )
            if config:
                cache_key = _make_xiaozhi_cache_key(agent_id, "UTC+0")
                success = await _write_warmup_cache(cache_key, config)
                return (agent_id, success)
            return (agent_id, False)
    
    results = await asyncio.gather(*[
        warmup_single_agent(agent_id) for agent_id in agent_ids_to_warmup
    ])
    
    for agent_id, success in results:
        if success:
            warmed_agents.append(agent_id)
        else:
            failed_agents.append(agent_id)
    
    total_time_ms = (time.time() - start_time) * 1000
    
    print(f"[Warmup] Completed: warmed={len(warmed_agents)}, failed={len(failed_agents)}, time={total_time_ms:.1f}ms")
    
    return success_response(data=WarmupResponse(
        warmed_agents=warmed_agents,
        failed_agents=failed_agents,
        total_time_ms=round(total_time_ms, 2),
    ).model_dump())




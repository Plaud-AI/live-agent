"""API package - FastAPI routers"""
from fastapi import APIRouter

from api.v1 import (
    user,
    auth,
    agents,
    voices,
    devices,
    templates,
    chat,
    internal,
    memories,
    files,
    stt,
    tts,
)

api_router = APIRouter()

# Include v1 routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(voices.router, prefix="/voices", tags=["Voices"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(internal.router, prefix="/internal", tags=["Internal"])
api_router.include_router(memories.router, prefix="/memories", tags=["Memories"])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(stt.router, prefix="/stt", tags=["STT"])
api_router.include_router(tts.router, prefix="/tts", tags=["TTS"])


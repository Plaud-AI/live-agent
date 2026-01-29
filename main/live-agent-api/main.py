"""
Live Agent API - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings, setup_logging, get_logger
from infra import (
    init_db, close_db,
    init_s3, close_s3,
    init_fish_audio, close_fish_audio,
    init_openai, close_openai,
    init_groq, close_groq,
    init_minimax_tts, close_minimax_tts,
)
from utils.exceptions import APIException
from api import api_router

# Setup logging
setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    
    Startup:
        - Initialize database connection pool
        - Initialize S3 client
        - Initialize Fish Audio client
        - Initialize OpenAI client
        - Initialize Groq client
        - Initialize MiniMax TTS client
    
    Shutdown:
        - Close all connections gracefully
    """
    # Startup
    logger.info("Starting Live Agent API...")
    
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    try:
        await init_s3()
        logger.info("S3 client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize S3: {e}")
    
    try:
        await init_fish_audio()
        logger.info("Fish Audio client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Fish Audio: {e}")
    
    try:
        await init_openai()
        logger.info("OpenAI client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI: {e}")
    
    try:
        await init_groq()
        logger.info("Groq client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Groq: {e}")
    
    try:
        await init_minimax_tts()
        logger.info("MiniMax TTS client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize MiniMax TTS: {e}")
    
    logger.info("Live Agent API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Live Agent API...")
    
    await close_minimax_tts()
    await close_groq()
    await close_openai()
    await close_fish_audio()
    await close_s3()
    await close_db()
    
    logger.info("Live Agent API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Live Agent API",
    description="Live Agent Manager API - Manage AI voice agents and conversations",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handler for APIException
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions"""
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.1.0"}


# Include API router
app.include_router(api_router, prefix="/api/live_agent/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )




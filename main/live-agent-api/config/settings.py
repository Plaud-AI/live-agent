from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL: str
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str
    S3_ENDPOINT_URL: str | None = None
    S3_PUBLIC_BASE_URL: str | None = None
    
    # Security
    SECRET_KEY: str
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = False
    
    # Token Configuration
    TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # OAuth - Google Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    
    # OAuth - Apple Configuration
    APPLE_CLIENT_ID: str = ""  # Your app's bundle ID
    APPLE_TEAM_ID: str = ""
    APPLE_KEY_ID: str = ""
    APPLE_PRIVATE_KEY: str = ""  # Contents of the .p8 file
    APPLE_REDIRECT_URI: str = ""
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CREDENTIALS_PATH: str = ""  # Path to service account JSON file
    # OR use inline credentials (for Docker/cloud deployments)
    FIREBASE_PRIVATE_KEY_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""  # The private key content (with \n for newlines)
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CLIENT_ID: str = ""
    
    # Email Configuration (for email verification)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Live Agent"
    SMTP_USE_TLS: bool = True
    
    # Frontend URL (for email links)
    FRONTEND_URL: str = "http://localhost:8080"
    
    # Email verification token expiry (in hours)
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 1
    
    # Fish Audio Configuration
    FISH_API_KEY: str
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # MemU Configuration
    MEMU_API_KEY: str = ""
    MEMU_BASE_URL: str = "https://api.memu.so"
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    QUICK_PERSONA_MODEL: str = "google/gemini-2.5-flash"
    OPTIMIZE_PERSONA_MODEL: str = "google/gemini-3-pro-preview"
    
    # Groq Configuration (for STT)
    GROQ_API_KEY: str
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_STT_MODEL: str = "whisper-large-v3"
    
    # MiniMax TTS Configuration
    MINIMAX_API_KEY: str = ""  # Optional, required for MiniMax TTS
    MINIMAX_API_URL: str = "https://api.minimax.io/v1/t2a_v2"
    MINIMAX_MODEL: str = "speech-2.6-turbo"
    MINIMAX_DEFAULT_VOICE_ID: str = "female-shaonv"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()



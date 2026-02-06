"""
Konfigurasi aplikasi untuk Ko-Desain Platform
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Konfigurasi aplikasi"""

    # App
    APP_NAME: str = "Ko-Desain Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # Database - PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "kodesain"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "kodesain_artifacts"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 2048

    # Voice - Edge TTS
    TTS_VOICE_MALE: str = "id-ID-ArdiNeural"
    TTS_VOICE_FEMALE: str = "id-ID-GadisNeural"
    TTS_DEFAULT_VOICE: str = "female"

    # Voice - Whisper STT
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large

    # Storage
    UPLOAD_DIR: str = "./uploads"
    AUDIO_DIR: str = "./uploads/audio"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Session Config
    SESSION_PHASE_TIMEOUT_MINUTES: int = 60
    MAX_PARTICIPANTS_PER_SESSION: int = 10

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

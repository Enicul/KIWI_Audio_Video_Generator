"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    APP_NAME: str = "KIWI-Video"
    DEBUG: bool = True
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS - Allow both common frontend ports
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Gemini
    GEMINI_API_KEY: Optional[str] = None
    
    # Video Generation (for future use)
    RUNWAY_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


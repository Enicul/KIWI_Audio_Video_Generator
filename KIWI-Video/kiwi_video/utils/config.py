"""Configuration management using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via .env file or environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Google AI Configuration
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key"
    )

    google_application_credentials: str | None = Field(
        None,
        description="Path to Google Cloud service account JSON"
    )

    gcp_project_id: str | None = Field(
        None,
        description="Google Cloud Project ID"
    )

    # Vertex AI Veo Configuration
    gcs_bucket: str = Field(
        ...,
        description="Google Cloud Storage bucket name"
    )

    veo_location: str = Field(
        default="us-central1",
        description="Vertex AI location"
    )

    veo_model: str = Field(
        default="veo-001",
        description="Veo model version"
    )

    # ElevenLabs Configuration
    elevenlabs_api_key: str = Field(
        ...,
        description="ElevenLabs API key"
    )

    elevenlabs_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="Default ElevenLabs voice ID"
    )

    # Application Configuration
    workspace_dir: Path = Field(
        default=Path("./workspaces"),
        description="Base directory for project workspaces"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    max_concurrent_projects: int = Field(
        default=5,
        description="Maximum concurrent projects"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API host"
    )

    api_port: int = Field(
        default=8000,
        description="API port"
    )

    api_workers: int = Field(
        default=4,
        description="Number of API workers"
    )

    # Model Configuration
    gemini_model: str = Field(
        default="gemini-2.5-pro",
        description="Gemini model to use"
    )

    gemini_temperature: float = Field(
        default=0.7,
        description="Temperature for Gemini generation"
    )

    # Video Configuration
    default_video_duration: int = Field(
        default=8,
        description="Default video duration in seconds"
    )

    video_resolution: str = Field(
        default="1280x720",
        description="Video resolution (WxH)"
    )

    video_fps: int = Field(
        default=24,
        description="Video frames per second"
    )

    video_aspect_ratio: str = Field(
        default="16:9",
        description="Video aspect ratio"
    )

    # Retry Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum retries for operations"
    )

    retry_delay: float = Field(
        default=2.0,
        description="Delay between retries in seconds"
    )

    # Timeout Configuration
    llm_timeout: int = Field(
        default=120,
        description="LLM request timeout in seconds"
    )

    video_generation_timeout: int = Field(
        default=600,
        description="Video generation timeout in seconds"
    )


# Global settings instance
settings = Settings()


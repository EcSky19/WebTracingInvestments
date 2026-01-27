"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings

__all__ = ["Settings", "settings"]

class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./app.db"

    # Reddit API
    REDDIT_CLIENT_ID: str | None = None
    REDDIT_CLIENT_SECRET: str | None = None
    REDDIT_USER_AGENT: str | None = None

    # Threads API (Meta)
    THREADS_ACCESS_TOKEN: str | None = None
    THREADS_USER_ID: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields from .env without validation errors

settings = Settings()

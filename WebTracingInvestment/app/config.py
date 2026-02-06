"""Application configuration loaded from environment variables."""

import logging
from pydantic_settings import BaseSettings

__all__ = ["Settings", "settings"]

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings from environment variables.
    
    Loads configuration from .env file or environment variables.
    Validates required Reddit credentials on initialization.
    """
    
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
    
    def __init__(self, **data):
        """Initialize settings and validate configuration."""
        super().__init__(**data)
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """Validate critical configuration settings."""
        if not self.REDDIT_CLIENT_ID or not self.REDDIT_CLIENT_SECRET:
            logger.warning(
                "Reddit credentials not configured. Reddit ingestion will be disabled. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env to enable."
            )
        if self.ENV not in ["dev", "staging", "prod"]:
            logger.warning(f"Unknown environment: {self.ENV}. Using 'dev' defaults.")

settings = Settings()

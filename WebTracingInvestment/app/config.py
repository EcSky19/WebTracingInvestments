"""Application configuration loaded from environment variables."""

import logging
from pydantic_settings import BaseSettings
from pydantic import Field, validator

__all__ = ["Settings", "settings"]

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings from environment variables.
    
    Loads configuration from .env file or environment variables.
    Supports dev, staging, and production environments.
    Includes advanced configuration for performance tuning.
    """
    
    # Environment
    ENV: str = Field(default="dev", description="Environment: dev, staging, prod")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./app.db",
        description="Database connection URL"
    )
    DB_POOL_SIZE: int = Field(default=10, ge=5, le=50, description="SQLite connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100, description="Max overflow connections")
    DB_POOL_RECYCLE: int = Field(default=3600, ge=600, description="Connection recycle time (seconds)")
    
    # Reddit API
    REDDIT_CLIENT_ID: str | None = Field(default=None, description="Reddit API client ID")
    REDDIT_CLIENT_SECRET: str | None = Field(default=None, description="Reddit API client secret")
    REDDIT_USER_AGENT: str | None = Field(default=None, description="Reddit API user agent")
    REDDIT_TIMEOUT: int = Field(default=16, ge=5, le=60, description="Reddit API timeout (seconds)")
    
    # Threads API (Meta)
    THREADS_ACCESS_TOKEN: str | None = Field(default=None, description="Threads API access token")
    THREADS_USER_ID: str | None = Field(default=None, description="Threads user ID")
    
    # Ingest settings
    INGEST_INTERVAL_MINUTES: int = Field(default=5, ge=1, le=60, description="Ingest job interval")
    INGEST_BATCH_SIZE: int = Field(default=50, ge=10, le=500, description="Posts per subreddit fetch")
    CLEANUP_DAYS: int = Field(default=90, ge=7, description="Retain posts for N days")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields from .env without validation errors
    
    @validator('ENV')
    def validate_env(cls, v):
        """Validate environment value."""
        if v not in ["dev", "staging", "prod"]:
            logger.warning(f"Unknown environment: {v}. Using 'dev' defaults.")
            return "dev"
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            logger.warning(f"Invalid log level: {v}. Using INFO.")
            return "INFO"
        return v.upper()
    
    def __init__(self, **data):
        """Initialize settings and validate configuration."""
        super().__init__(**data)
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """Validate critical configuration settings."""
        # Check Reddit credentials
        has_reddit = self.REDDIT_CLIENT_ID and self.REDDIT_CLIENT_SECRET and self.REDDIT_USER_AGENT
        if not has_reddit:
            logger.warning(
                "⚠ Reddit credentials not fully configured. Set REDDIT_CLIENT_ID, "
                "REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT in .env to enable Reddit ingestion."
            )
        else:
            logger.info("✓ Reddit credentials detected")
        
        # Check Threads credentials
        has_threads = self.THREADS_ACCESS_TOKEN and self.THREADS_USER_ID
        if not has_threads:
            logger.debug("Threads API not configured (optional)")
        else:
            logger.info("✓ Threads credentials detected")
        
        # Log environment
        logger.info(f"Environment: {self.ENV.upper()}")
        if self.DEBUG:
            logger.warning("Debug mode is ENABLED")
        
        # Log database settings
        logger.debug(f"Database: {self.DATABASE_URL}")
        logger.debug(f"Pool settings: size={self.DB_POOL_SIZE}, overflow={self.DB_MAX_OVERFLOW}, recycle={self.DB_POOL_RECYCLE}s")
        
        # Log ingest settings
        logger.debug(f"Ingest: every {self.INGEST_INTERVAL_MINUTES}min, batch_size={self.INGEST_BATCH_SIZE}")
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENV.lower() == "prod"
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.DEBUG or self.ENV.lower() == "dev"

settings = Settings()

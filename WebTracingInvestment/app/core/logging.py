"""Logging configuration module with structured logging support."""

import logging
from pathlib import Path
from app.config import settings

__all__ = ["setup_logging"]

# Formatters for different purposes
DETAILED_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
SIMPLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
ERROR_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s | %(exc_info)s"

def setup_logging() -> None:
    """Configure application logging with both console and file handlers.
    
    Sets up:
    - Console output at configured log level
    - File logging in logs/app.log
    - Error logging in logs/errors.log at ERROR level
    - Debug logging in logs/debug.log (when DEBUG enabled)
    
    Respects LOG_LEVEL and DEBUG settings from configuration.
    """
    
    # Create logs directory if needed
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Use detailed format in debug mode, simple otherwise
    formatter_str = DETAILED_FORMAT if settings.is_debug() else SIMPLE_FORMAT
    formatter = logging.Formatter(
        formatter_str,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for persistent logging
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler for capturing errors
    error_handler = logging.FileHandler(log_dir / "errors.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        ERROR_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Debug file handler (only in debug mode)
    if settings.is_debug():
        debug_handler = logging.FileHandler(log_dir / "debug.log", encoding="utf-8")
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(
            DETAILED_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        debug_handler.setFormatter(debug_formatter)
        root_logger.addHandler(debug_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    logging.getLogger("app").setLevel(log_level)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)  # Suppress SQL logs in normal mode
    if settings.is_debug():
        logging.getLogger("sqlalchemy").setLevel(logging.DEBUG)  # Show SQL in debug mode
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("praw").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Suppress urllib3 debug logs
    
    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info("═" * 70)
    logger.info(f"✓ Logging initialized")
    logger.info(f"  - Environment: {settings.ENV.upper()}")
    logger.info(f"  - Log level: {settings.LOG_LEVEL.upper()}")
    logger.info(f"  - Debug mode: {settings.is_debug()}")
    logger.info(f"  - Database: {settings.DATABASE_URL}")
    logger.info(f"  - Log directory: {log_dir.resolve()}")
    logger.info("═" * 70)

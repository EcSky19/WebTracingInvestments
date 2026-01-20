import logging
from pathlib import Path
from app.config import settings

def setup_logging():
    """Configure application logging with both console and file handlers."""
    
    # Create logs directory if needed
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatter with detailed information
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
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
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)  # Suppress SQL logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured | ENV: {settings.ENV} | Database: {settings.DATABASE_URL}")

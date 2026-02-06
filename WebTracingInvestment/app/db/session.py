"""Database session management with context manager support."""

import logging
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

__all__ = ["engine", "init_db", "get_session"]

logger = logging.getLogger(__name__)
engine = create_engine(settings.DATABASE_URL, echo=False)

def init_db() -> None:
    """Initialize database tables."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info(f"Database initialized: {settings.DATABASE_URL}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise

@contextmanager
def get_session():
    """Get a database session with proper context manager support.
    
    Usage:
        with get_session() as session:
            # Use session
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

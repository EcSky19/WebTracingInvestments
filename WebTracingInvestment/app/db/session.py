"""Database session management with context manager support."""

from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

__all__ = ["engine", "init_db", "get_session"]

engine = create_engine(settings.DATABASE_URL, echo=False)

def init_db():
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)

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

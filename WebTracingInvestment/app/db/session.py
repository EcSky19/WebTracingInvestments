"""Database session management with connection pooling and monitoring."""

import logging
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import QueuePool
from app.config import settings

__all__ = ["engine", "init_db", "get_session"]

logger = logging.getLogger(__name__)

# Create engine with connection pooling for better performance
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to keep in pool
    max_overflow=20,  # Allow up to 20 additional connections
    pool_pre_ping=True,  # Test connections before using (handles stale connections)
    pool_recycle=3600,  # Recycle connections every hour
)

def init_db() -> None:
    """Initialize database tables and verify connection.
    
    Sets up all tables defined in SQLModel and logs initialization status.
    Raises exception if database is not accessible.
    """
    try:
        SQLModel.metadata.create_all(engine)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        logger.info(f"✓ Database initialized: {settings.DATABASE_URL}")
        logger.info(f"  Pool: size=10, max_overflow=20, recycle=3600s")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}", exc_info=True)
        raise

@contextmanager
def get_session():
    """Get a database session with proper context manager support.
    
    Ensures sessions are properly closed after use, preventing connection leaks.
    Uses connection pooling for better performance under load.
    
    Usage:
        with get_session() as session:
            # Use session for queries
            result = session.exec(select(Post)).all()
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

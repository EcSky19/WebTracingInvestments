"""Database repository functions for data access with optimized queries."""

import logging
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select, func
from app.db.models import Post

__all__ = ["upsert_post", "list_recent_posts", "bulk_upsert_posts", "get_post_count", "cleanup_old_posts"]

logger = logging.getLogger(__name__)

def upsert_post(session: Session, post: Post) -> bool:
    """
    Insert a post if it doesn't already exist (idempotent operation).
    
    Uses the (source, source_id) unique index to detect duplicates.
    Useful for avoiding duplicate ingestion when re-running data sources.
    
    Args:
        session: Database session
        post: Post object to insert
        
    Returns:
        True if post was inserted (new)
        False if post already existed (duplicate)
        
    Example:
        >>> post = Post(source="reddit", source_id="abc123", text="...", ...)
        >>> upsert_post(session, post)
        True  # First time
        >>> upsert_post(session, post)  
        False  # Duplicate (same source + source_id)
    """
    try:
        exists = session.exec(
            select(Post).where(
                Post.source == post.source, 
                Post.source_id == post.source_id
            )
        ).first()
        if exists:
            return False
        session.add(post)
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Error upserting post {post.source}:{post.source_id}: {e}")
        session.rollback()
        raise


def bulk_upsert_posts(session: Session, posts: list[Post]) -> tuple[int, int]:
    """
    Efficiently insert multiple posts, skipping duplicates.
    
    Performs bulk upsert operation for better performance with large batches.
    
    Args:
        session: Database session
        posts: List of Post objects to insert
        
    Returns:
        Tuple of (inserted_count, duplicate_count)
        
    Example:
        >>> posts = [Post(...), Post(...), Post(...)]
        >>> inserted, duplicates = bulk_upsert_posts(session, posts)
        >>> print(f"Inserted {inserted}, skipped {duplicates} duplicates")
    """
    inserted = 0
    duplicates = 0
    
    try:
        for post in posts:
            if upsert_post(session, post):
                inserted += 1
            else:
                duplicates += 1
        return inserted, duplicates
    except Exception as e:
        logger.error(f"Error in bulk upsert: {e}")
        raise


def list_recent_posts(session: Session, limit: int = 100, symbol: str | None = None) -> list[Post]:
    """
    Retrieve recent posts ordered by creation date descending.
    
    Optionally filter by symbol for faster retrieval.
    
    Args:
        session: Database session
        limit: Maximum number of posts to return (default 100)
        symbol: Optional symbol filter for faster retrieval
        
    Returns:
        List of recent posts, newest first
        
    Example:
        >>> posts = list_recent_posts(session, limit=50, symbol="TSLA")
        >>> len(posts)
        50
    """
    try:
        q = select(Post).order_by(Post.created_at.desc())
        
        if symbol:
            q = q.where(Post.symbols.like(f"%{symbol}%"))
        
        return session.exec(q.limit(limit)).all()
    except Exception as e:
        logger.error(f"Error listing recent posts: {e}")
        return []


def get_post_count(session: Session, symbol: str | None = None, days: int | None = None) -> int:
    """
    Get total post count, optionally filtered by symbol and/or date range.
    
    Uses COUNT() for efficiency instead of loading all records.
    
    Args:
        session: Database session
        symbol: Optional symbol filter
        days: Optional number of days to look back
        
    Returns:
        Count of posts matching criteria
        
    Example:
        >>> count = get_post_count(session, symbol="AAPL", days=7)
        >>> print(f"Found {count} AAPL posts in last 7 days")
    """
    try:
        q = select(func.count(Post.id))
        
        if symbol:
            q = q.select_from(Post).where(Post.symbols.like(f"%{symbol}%"))
        
        if days:
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
            q = q.where(Post.created_at >= cutoff)
        
        return session.exec(q).scalar() or 0
    except Exception as e:
        logger.error(f"Error getting post count: {e}")
        return 0


def cleanup_old_posts(session: Session, days: int = 90) -> int:
    """
    Delete posts older than specified number of days.
    
    Useful for managing database size and improving query performance.
    
    Args:
        session: Database session
        days: Delete posts older than this many days (default 90)
        
    Returns:
        Number of posts deleted
        
    Example:
        >>> deleted = cleanup_old_posts(session, days=60)
        >>> print(f"Cleaned up {deleted} old posts")
    """
    try:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
        old_posts = session.exec(
            select(Post).where(Post.created_at < cutoff)
        ).all()
        
        deleted_count = len(old_posts)
        for post in old_posts:
            session.delete(post)
        
        session.commit()
        logger.info(f"Deleted {deleted_count} posts older than {days} days")
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up old posts: {e}")
        session.rollback()
        return 0

"""Database repository functions for data access."""

from sqlmodel import Session, select
from app.db.models import Post

__all__ = ["upsert_post", "list_recent_posts"]

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
    exists = session.exec(
        select(Post).where(Post.source == post.source, Post.source_id == post.source_id)
    ).first()
    if exists:
        return False
    session.add(post)
    session.commit()
    return True


def list_recent_posts(session: Session, limit: int = 100) -> list[Post]:
    """
    Retrieve recent posts ordered by creation date descending.
    
    Args:
        session: Database session
        limit: Maximum number of posts to return (default 100)
        
    Returns:
        List of recent posts, newest first
        
    Example:
        >>> posts = list_recent_posts(session, limit=50)
        >>> len(posts)
        50
    """
    return session.exec(select(Post).order_by(Post.created_at.desc()).limit(limit)).all()

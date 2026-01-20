"""Database repository functions for data access."""

from sqlmodel import Session, select
from app.db.models import Post

def upsert_post(session: Session, post: Post) -> bool:
    """
    Insert if not exists (by unique index).
    Returns True if inserted, False if already existed.
    """
    exists = session.exec(
        select(Post).where(Post.source == post.source, Post.source_id == post.source_id)
    ).first()
    if exists:
        return False
    session.add(post)
    session.commit()
    return True

def list_recent_posts(session: Session, limit: int = 100):
    return session.exec(select(Post).order_by(Post.created_at.desc()).limit(limit)).all()

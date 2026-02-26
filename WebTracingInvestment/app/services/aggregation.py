"""Sentiment aggregation service for hourly bucketing."""

import logging
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.db.models import Post, SentimentBucket

__all__ = ["floor_to_hour", "aggregate_hour"]

logger = logging.getLogger(__name__)

def floor_to_hour(dt: datetime) -> datetime:
    """
    Round a datetime down to the nearest hour boundary.
    
    Useful for bucketing posts into hourly sentiment aggregations.
    
    Args:
        dt: Datetime to round (any timezone)
        
    Returns:
        Datetime rounded down to hour start (MM:00:00.000000 UTC)
        
    Examples:
        >>> dt = datetime(2026, 1, 19, 14, 45, 30)
        >>> floor_to_hour(dt)
        datetime(2026, 1, 19, 14, 0, 0, tzinfo=UTC)
    """
    dt = dt.astimezone(timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0)


def aggregate_hour(session: Session, hour_start: datetime) -> None:
    """
    Recompute sentiment aggregates for a given hour using batch operations.
    
    Computes the average sentiment for each tracked symbol within a one-hour
    window and creates or updates SentimentBucket records in batch.
    
    This is called after each ingest cycle to keep aggregations up-to-date.
    
    Args:
        session: Database session
        hour_start: Start of the hour to aggregate (will be rounded)
        
    Note:
        MVP implementation: uses simple mean sentiment per symbol.
        
        Future enhancements could include:
        - Weighted sentiment by post engagement (upvotes, replies)
        - Separate weighting for reddit vs threads posts
        - Robust statistics (median, trimmed mean) instead of mean
    """
    from sqlalchemy import func, case, cast, Float
    
    hour_start = floor_to_hour(hour_start)
    hour_end = hour_start.replace(minute=59, second=59, microsecond=999999)

    # Fetch posts with sentiment in date range
    posts = session.exec(
        select(Post).where(
            Post.created_at >= hour_start,
            Post.created_at <= hour_end,
            Post.sentiment.isnot(None)
        )
    ).all()

    # Batch process: group by symbol and calculate aggregates in Python
    by_sym: dict[str, list[float]] = {}
    for p in posts:
        syms = [s.strip() for s in (p.symbols or "").split(",") if s.strip()]
        for s in syms:
            by_sym.setdefault(s, []).append(float(p.sentiment))

    # Batch upsert buckets
    symbols_processed = set()
    for sym, vals in by_sym.items():
        symbols_processed.add(sym)
        avg = sum(vals) / max(1, len(vals))
        post_count = len(vals)

        existing = session.exec(
            select(SentimentBucket).where(
                SentimentBucket.symbol == sym,
                SentimentBucket.bucket == "hour",
                SentimentBucket.bucket_start == hour_start,
            )
        ).first()

        if existing:
            existing.post_count = post_count
            existing.avg_sentiment = avg
        else:
            session.add(SentimentBucket(
                symbol=sym,
                bucket="hour",
                bucket_start=hour_start,
                post_count=post_count,
                avg_sentiment=avg,
            ))

    session.commit()
    logger.info(f"Aggregated sentiment for {len(symbols_processed)} symbols in hour {hour_start}")

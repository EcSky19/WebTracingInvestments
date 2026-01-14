import logging
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.db.models import Post, SentimentBucket

logger = logging.getLogger(__name__)

def floor_to_hour(dt: datetime) -> datetime:
    dt = dt.astimezone(timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0)

def aggregate_hour(session: Session, hour_start: datetime):
    """
    Recompute aggregates for a given hour.
    MVP: simple mean sentiment per symbol.
    Later:
    - weighted by upvotes/engagement
    - separate reddit vs threads weights
    - robust stats (median, trimmed mean)
    """
    hour_start = floor_to_hour(hour_start)
    hour_end = hour_start.replace(minute=59, second=59, microsecond=999999)

    posts = session.exec(
        select(Post).where(Post.created_at >= hour_start, Post.created_at <= hour_end)
    ).all()

    by_sym: dict[str, list[float]] = {}
    for p in posts:
        if p.sentiment is None:
            continue
        syms = [s for s in (p.symbols or "").split(",") if s]
        for s in syms:
            by_sym.setdefault(s, []).append(float(p.sentiment))

    for sym, vals in by_sym.items():
        avg = sum(vals) / max(1, len(vals))

        existing = session.exec(
            select(SentimentBucket).where(
                SentimentBucket.symbol == sym,
                SentimentBucket.bucket == "hour",
                SentimentBucket.bucket_start == hour_start,
            )
        ).first()

        if existing:
            existing.post_count = len(vals)
            existing.avg_sentiment = avg
            logger.debug(f"Updated {sym}: {len(vals)} posts, sentiment={avg:.3f}")
        else:
            session.add(SentimentBucket(
                symbol=sym,
                bucket="hour",
                bucket_start=hour_start,
                post_count=len(vals),
                avg_sentiment=avg,
            ))
            logger.debug(f"Created {sym}: {len(vals)} posts, sentiment={avg:.3f}")

    session.commit()
    logger.info(f"Aggregated sentiment for {len(by_sym)} symbols in hour {hour_start}")

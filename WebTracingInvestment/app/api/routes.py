from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from sqlmodel import select

from app.db.session import get_session
from app.db.models import SentimentBucket, Post
from app.api.schemas import BucketOut, SentimentDistribution, StockSentimentSummary, PostDetail, HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Health check with database status.
    Returns ok if database is accessible and has data.
    """
    try:
        with get_session() as session:
            # Try simple queries to verify database is working
            post_count = len(session.exec(select(Post)).all())
            bucket_count = len(session.exec(select(SentimentBucket)).all())
            
        return {
            "ok": True,
            "database": "connected",
            "posts_total": post_count,
            "sentiment_buckets": bucket_count,
        }
    except Exception as e:
        return {
            "ok": False,
            "database": "disconnected",
            "error": str(e),
        }

@router.get("/sentiment/hourly", response_model=list[BucketOut])
def hourly(symbol: str | None = None, hours: int = 24):
    """
    Returns last N hours of hourly sentiment.
    """
    now = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=hours)

    with get_session() as session:
        q = select(SentimentBucket).where(
            SentimentBucket.bucket == "hour",
            SentimentBucket.bucket_start >= start,
        ).order_by(SentimentBucket.bucket_start.asc())

        if symbol:
            q = q.where(SentimentBucket.symbol == symbol.upper())

        rows = session.exec(q).all()
        return [BucketOut(**r.model_dump()) for r in rows]

@router.get("/sentiment/distribution/{symbol}", response_model=SentimentDistribution)
def sentiment_distribution(symbol: str, hours: int = 24):
    """
    Returns sentiment distribution breakdown for a symbol (very negative, negative, neutral, positive, very positive).
    """
    now = datetime.now(tz=timezone.utc)
    start = now - timedelta(hours=hours)
    symbol = symbol.upper()

    with get_session() as session:
        # Get all posts and filter in Python since SQLite symbols are comma-separated
        posts = session.exec(
            select(Post).where(
                Post.created_at >= start,
                Post.sentiment.isnot(None),
            )
        ).all()

        # Filter for posts mentioning this symbol
        relevant_posts = [
            p for p in posts 
            if symbol in [s.strip() for s in (p.symbols or "").split(",")]
        ]

        very_negative = sum(1 for p in relevant_posts if p.sentiment <= -0.6)
        negative = sum(1 for p in relevant_posts if -0.6 < p.sentiment <= -0.2)
        neutral = sum(1 for p in relevant_posts if -0.2 < p.sentiment < 0.2)
        positive = sum(1 for p in relevant_posts if 0.2 <= p.sentiment < 0.6)
        very_positive = sum(1 for p in relevant_posts if p.sentiment >= 0.6)
        
        avg_sentiment = sum(p.sentiment for p in relevant_posts) / len(relevant_posts) if relevant_posts else 0.0

        return SentimentDistribution(
            symbol=symbol,
            very_negative=very_negative,
            negative=negative,
            neutral=neutral,
            positive=positive,
            very_positive=very_positive,
            total_posts=len(relevant_posts),
            avg_sentiment=avg_sentiment,
        )

@router.get("/sentiment/stocks", response_model=list[StockSentimentSummary])
def all_stocks(hours: int = 24):
    """
    Returns sentiment summary for all tracked stocks in the last N hours.
    Sorted by post count (most discussed first).
    """
    now = datetime.now(tz=timezone.utc)
    start = now - timedelta(hours=hours)

    with get_session() as session:
        posts = session.exec(
            select(Post).where(
                Post.created_at >= start,
                Post.sentiment.isnot(None),
            )
        ).all()

        # Group by symbol
        symbol_stats = {}
        for post in posts:
            symbols = [s.strip() for s in (post.symbols or "").split(",") if s.strip()]
            for sym in symbols:
                if sym not in symbol_stats:
                    symbol_stats[sym] = {"posts": [], "recent": post.created_at}
                symbol_stats[sym]["posts"].append(post.sentiment)
                symbol_stats[sym]["recent"] = max(symbol_stats[sym]["recent"], post.created_at)

        # Build response, sorted by post count
        results = []
        for sym, stats in sorted(symbol_stats.items(), key=lambda x: len(x[1]["posts"]), reverse=True):
            avg = sum(stats["posts"]) / len(stats["posts"])
            results.append(
                StockSentimentSummary(
                    symbol=sym,
                    total_posts=len(stats["posts"]),
                    avg_sentiment=avg,
                    most_recent_post=stats["recent"],
                )
            )
        return results

@router.get("/posts/{symbol}", response_model=list[PostDetail])
def get_posts(symbol: str, limit: int = 50):
    """
    Returns recent posts mentioning a symbol.
    """
    symbol = symbol.upper()
    
    with get_session() as session:
        posts = session.exec(
            select(Post).order_by(Post.created_at.desc())
        ).all()

        # Filter for posts mentioning this symbol and limit
        relevant_posts = [
            p for p in posts 
            if symbol in [s.strip() for s in (p.symbols or "").split(",")]
        ][:limit]

        return [
            PostDetail(
                source=p.source,
                author=p.author,
                created_at=p.created_at,
                text=p.text,
                symbols=p.symbols,
                sentiment=p.sentiment or 0.0,
                url=p.url,
            )
            for p in relevant_posts
        ]

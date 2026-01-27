"""API routes for sentiment analysis endpoints."""

from datetime import datetime, timedelta, timezone
import logging
from fastapi import APIRouter, Query
from sqlmodel import select

from app.db.session import get_session
from app.db.models import SentimentBucket, Post
from app.api.schemas import BucketOut, SentimentDistribution, StockSentimentSummary, PostDetail, HealthResponse

__all__ = ["router"]

logger = logging.getLogger(__name__)
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
            
        logger.info("Health check passed")
        return HealthResponse(
            ok=True,
            database="connected",
            posts_total=post_count,
            sentiment_buckets=bucket_count,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            ok=False,
            database="disconnected",
            error=str(e),
        )

@router.get("/sentiment/hourly", response_model=list[BucketOut])
def hourly(symbol: str | None = None, hours: int = Query(24, gt=0, le=720)) -> list[BucketOut]:
    """
    Returns last N hours of hourly sentiment.
    
    Args:
        symbol: Optional symbol filter (case-insensitive)
        hours: Number of hours to retrieve (1-720, default 24)
    
    Returns:
        List of hourly sentiment buckets
    """
    try:
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
            logger.debug(f"Retrieved {len(rows)} hourly buckets for {symbol or 'all symbols'}")
            return [BucketOut(**r.model_dump()) for r in rows]
    except Exception as e:
        logger.error(f"Error fetching hourly sentiment: {e}")
        raise

@router.get("/sentiment/distribution/{symbol}", response_model=SentimentDistribution)
def sentiment_distribution(symbol: str, hours: int = Query(24, gt=0, le=720)) -> SentimentDistribution:
    """
    Returns sentiment distribution breakdown for a symbol.
    
    Args:
        symbol: Stock symbol (case-insensitive)
        hours: Number of hours to analyze (1-720, default 24)
    
    Returns:
        Sentiment distribution with counts for each sentiment tier
    """
    try:
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

            logger.debug(f"Distribution for {symbol}: {len(relevant_posts)} posts, avg sentiment {avg_sentiment:.3f}")

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
    except Exception as e:
        logger.error(f"Error fetching sentiment distribution for {symbol}: {e}")
        raise

@router.get("/sentiment/stocks", response_model=list[StockSentimentSummary])
def all_stocks(hours: int = Query(24, gt=0, le=720)) -> list[StockSentimentSummary]:
    """
    Returns sentiment summary for all tracked stocks in the last N hours.
    Sorted by post count (most discussed first).
    
    Args:
        hours: Number of hours to analyze (1-720, default 24)
    
    Returns:
        List of stocks sorted by post count descending
    """
    try:
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
            logger.debug(f"Retrieved sentiment for {len(results)} stocks")
            return results
    except Exception as e:
        logger.error(f"Error fetching all stocks sentiment: {e}")
        raise

@router.get("/posts/{symbol}", response_model=list[PostDetail])
def get_posts(symbol: str, limit: int = Query(50, gt=0, le=1000)) -> list[PostDetail]:
    """
    Returns recent posts mentioning a symbol.
    
    Args:
        symbol: Stock symbol (case-insensitive)
        limit: Maximum number of posts to return (1-1000, default 50)
    
    Returns:
        List of recent posts mentioning the symbol
    """
    try:
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

            logger.debug(f"Retrieved {len(relevant_posts)} posts for symbol {symbol}")

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
    except Exception as e:
        logger.error(f"Error fetching posts for symbol {symbol}: {e}")
        raise

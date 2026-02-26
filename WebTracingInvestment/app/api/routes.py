"""API routes for sentiment analysis endpoints."""

from datetime import datetime, timedelta, timezone
import logging
from fastapi import APIRouter, Query, Response
from sqlmodel import select, func

from app.db.session import get_session
from app.db.models import SentimentBucket, Post
from app.api.schemas import BucketOut, SentimentDistribution, StockSentimentSummary, PostDetail, HealthResponse

__all__ = ["router"]

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    """
    Health check with database status.
    
    Returns ok if database is accessible and has data.
    Useful for monitoring and load balancer health checks.
    Sets cache headers for 30 second TTL to reduce repeated checks.
    """
    try:
        with get_session() as session:
            # Use COUNT for efficiency instead of loading all records
            post_count = session.query(func.count(Post.id)).scalar() or 0
            bucket_count = session.query(func.count(SentimentBucket.id)).scalar() or 0
            
        # Cache for 30 seconds - health changes are infrequent
        response.headers["Cache-Control"] = "public, max-age=30"
        
        logger.info("Health check passed")
        return HealthResponse(
            ok=True,
            database="connected",
            posts_total=post_count,
            sentiment_buckets=bucket_count,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        response.headers["Cache-Control"] = "no-cache"
        return HealthResponse(
            ok=False,
            database="disconnected",
            error=str(e),
        )

@router.get("/sentiment/hourly", response_model=list[BucketOut])
def hourly(symbol: str | None = None, hours: int = Query(24, gt=0, le=720), limit: int = Query(1000, gt=0, le=10000), response: Response = None) -> list[BucketOut]:
    """
    Returns last N hours of hourly sentiment with pagination.
    
    Args:
        symbol: Optional symbol filter (case-insensitive)
        hours: Number of hours to retrieve (1-720, default 24)
        limit: Max results to return (1-10000, default 1000)
    
    Returns:
        List of hourly sentiment buckets with 5-minute cache TTL
    """
    try:
        now = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
        start = now - timedelta(hours=hours)
        symbol_upper = symbol.upper() if symbol else None

        with get_session() as session:
            q = select(SentimentBucket).where(
                SentimentBucket.bucket == "hour",
                SentimentBucket.bucket_start >= start,
            ).order_by(SentimentBucket.bucket_start.asc())

            if symbol_upper:
                q = q.where(SentimentBucket.symbol == symbol_upper)

            q = q.limit(limit)  # Add pagination
            rows = session.exec(q).all()
            
        # Cache for 5 minutes - hourly data changes slowly
        if response:
            response.headers["Cache-Control"] = "public, max-age=300"
        
        logger.debug(f"Retrieved {len(rows)} hourly buckets for {symbol_upper or 'all symbols'}")
        return [BucketOut(**r.model_dump()) for r in rows]
    except Exception as e:
        logger.error(f"Error fetching hourly sentiment: {e}", exc_info=True)
        raise

@router.get("/sentiment/distribution/{symbol}", response_model=SentimentDistribution)
def sentiment_distribution(symbol: str, hours: int = Query(24, gt=0, le=720), response: Response = None) -> SentimentDistribution:
    """
    Returns sentiment distribution breakdown for a symbol.
    
    Args:
        symbol: Stock symbol (case-insensitive)
        hours: Number of hours to analyze (1-720, default 24)
    
    Returns:
        Sentiment distribution with counts for each sentiment tier
        Cached for 10 minutes to reduce database load
    """
    try:
        now = datetime.now(tz=timezone.utc)
        start = now - timedelta(hours=hours)
        symbol = symbol.upper()

        with get_session() as session:
            # Use database LIKE query for efficient symbol filtering
            posts = session.exec(
                select(Post).where(
                    Post.created_at >= start,
                    Post.sentiment.isnot(None),
                    Post.symbols.like(f"%{symbol}%"),  # Use DB-level LIKE filtering
                )
            ).all()

            # Filter for exact symbol match (LIKE catches partial matches)
            relevant_posts = [
                p for p in posts 
                if symbol in [s.strip() for s in (p.symbols or "").split(",")]
            ]

            # Single pass aggregation for efficiency
            very_negative = negative = neutral = positive = very_positive = 0
            total_sentiment = 0.0
            
            for p in relevant_posts:
                total_sentiment += p.sentiment
                if p.sentiment <= -0.6:
                    very_negative += 1
                elif p.sentiment <= -0.2:
                    negative += 1
                elif p.sentiment < 0.2:
                    neutral += 1
                elif p.sentiment < 0.6:
                    positive += 1
                else:
                    very_positive += 1
            
            avg_sentiment = total_sentiment / len(relevant_posts) if relevant_posts else 0.0
            
        # Cache for 10 minutes
        if response:
            response.headers["Cache-Control"] = "public, max-age=600"

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
def all_stocks(hours: int = Query(24, gt=0, le=720), limit: int = Query(100, gt=0, le=1000)) -> list[StockSentimentSummary]:
    """
    Returns sentiment summary for all tracked stocks in the last N hours.
    Sorted by post count (most discussed first).
    
    Args:
        hours: Number of hours to analyze (1-720, default 24)
        limit: Maximum stocks to return (1-1000, default 100)
    
    Returns:
        List of stocks sorted by post count descending
    """
    try:
        now = datetime.now(tz=timezone.utc)
        start = now - timedelta(hours=hours)

        with get_session() as session:
            # Query only necessary fields for efficiency
            posts = session.exec(
                select(Post).where(
                    Post.created_at >= start,
                    Post.sentiment.isnot(None),
                ).order_by(Post.created_at.desc())
            ).all()

            # Group by symbol with reduced memory footprint
            symbol_stats = {}
            for post in posts:
                symbols = [s.strip() for s in (post.symbols or "").split(",") if s.strip()]
                for sym in symbols:
                    if sym not in symbol_stats:
                        symbol_stats[sym] = {"sentiments": [], "recent": post.created_at}
                    symbol_stats[sym]["sentiments"].append(post.sentiment)
                    symbol_stats[sym]["recent"] = max(symbol_stats[sym]["recent"], post.created_at)

            # Build response, sorted by post count with limit
            results = []
            for sym, stats in sorted(symbol_stats.items(), key=lambda x: len(x[1]["sentiments"]), reverse=True):
                if len(results) >= limit:
                    break
                avg = sum(stats["sentiments"]) / len(stats["sentiments"])
                results.append(
                    StockSentimentSummary(
                        symbol=sym,
                        total_posts=len(stats["sentiments"]),
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
def get_posts(symbol: str, limit: int = Query(50, gt=0, le=1000), offset: int = Query(0, ge=0)) -> list[PostDetail]:
    """
    Returns recent posts mentioning a symbol with pagination.
    
    Args:
        symbol: Stock symbol (case-insensitive)
        limit: Maximum number of posts to return (1-1000, default 50)
        offset: Number of posts to skip for pagination (default 0)
    
    Returns:
        List of recent posts mentioning the symbol
    """
    try:
        symbol = symbol.upper()
        
        with get_session() as session:
            # Use database LIKE to filter before loading into memory
            posts = session.exec(
                select(Post).where(
                    Post.symbols.like(f"%{symbol}%"),  # DB-level filtering
                ).order_by(Post.created_at.desc())
            ).all()

            # Filter for exact symbol match and apply pagination
            relevant_posts = [
                p for p in posts 
                if symbol in [s.strip() for s in (p.symbols or "").split(",")]
            ][offset:offset+limit]

            logger.debug(f"Retrieved {len(relevant_posts)} posts for symbol {symbol} (offset={offset})")

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

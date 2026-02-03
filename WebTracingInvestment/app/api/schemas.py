"""API request and response schemas."""

from datetime import datetime
from pydantic import BaseModel

__all__ = [
    "HealthResponse",
    "BucketOut",
    "SentimentDistribution",
    "StockSentimentSummary",
    "PostDetail",
]

class HealthResponse(BaseModel):
    """
    Health check response for application status.
    
    Provides overall system health, database connectivity, and content statistics.
    Used by load balancers and monitoring systems to verify service availability.
    
    Attributes:
        ok: True if all systems operational, False if any critical system failed
        database: Database status message (e.g., 'connected', 'sqlite')
        posts_total: Total number of posts ingested (None on error)
        sentiment_buckets: Total sentiment analysis buckets (None on error)
        error: Error message if health check failed (None on success)
        
    Example:
        >>> response = HealthResponse(
        ...     ok=True,
        ...     database="sqlite",
        ...     posts_total=1500,
        ...     sentiment_buckets=45
        ... )
    """
    ok: bool
    database: str
    posts_total: int | None = None
    sentiment_buckets: int | None = None
    error: str | None = None

class BucketOut(BaseModel):
    """
    Hourly sentiment bucket for a stock symbol.
    
    Represents aggregated sentiment analysis results for a specific stock
    within a one-hour time window. Used for charting and trend analysis.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        bucket_start: Start time of the hour bucket (ISO 8601 datetime)
        bucket: Human-readable bucket label (e.g., '2026-02-02T15:00')
        post_count: Total posts analyzed in this bucket
        avg_sentiment: Average sentiment score (-1.0 to 1.0)
        
    Example:
        >>> bucket = BucketOut(
        ...     symbol="AAPL",
        ...     bucket_start=datetime(2026, 2, 2, 15, 0),
        ...     bucket="2026-02-02T15:00",
        ...     post_count=25,
        ...     avg_sentiment=0.35
        ... )
    """
    symbol: str
    bucket_start: datetime
    bucket: str
    post_count: int
    avg_sentiment: float

class SentimentDistribution(BaseModel):
    """
    Sentiment distribution histogram for a stock symbol.
    
    Breaks down sentiment analysis results into 5 bins: very negative, negative,
    neutral, positive, and very positive. Provides both count and average score.
    
    Sentiment Score Ranges:
        Very Negative: -1.0 to -0.6 (very bearish posts)
        Negative:      -0.6 to -0.2 (bearish posts)
        Neutral:       -0.2 to +0.2 (balanced/factual posts)
        Positive:      +0.2 to +0.6 (bullish posts)
        Very Positive: +0.6 to +1.0 (very bullish posts)
    
    Attributes:
        symbol: Stock ticker symbol
        very_negative: Count of very bearish posts
        negative: Count of bearish posts
        neutral: Count of neutral/factual posts
        positive: Count of bullish posts
        very_positive: Count of very bullish posts
        total_posts: Sum of all sentiment categories
        avg_sentiment: Weighted average sentiment (-1.0 to 1.0)
        
    Example:
        >>> dist = SentimentDistribution(
        ...     symbol="TSLA",
        ...     very_negative=2, negative=8, neutral=15,
        ...     positive=20, very_positive=10, total_posts=55,
        ...     avg_sentiment=0.42
        ... )
    """
    symbol: str
    very_negative: int  # -1.0 to -0.6
    negative: int       # -0.6 to -0.2
    neutral: int        # -0.2 to 0.2
    positive: int       # 0.2 to 0.6
    very_positive: int  # 0.6 to 1.0
    total_posts: int
    avg_sentiment: float

class StockSentimentSummary(BaseModel):
    """
    Summary statistics for a stock symbol across all time.
    
    High-level overview of sentiment analysis results for a stock,
    aggregated across all posts and time periods.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        total_posts: Total number of posts analyzed
        avg_sentiment: Weighted average sentiment score (-1.0 to 1.0)
        most_recent_post: Timestamp of the most recent post
        
    Example:
        >>> summary = StockSentimentSummary(
        ...     symbol="AAPL",
        ...     total_posts=5000,
        ...     avg_sentiment=0.38,
        ...     most_recent_post=datetime(2026, 2, 2, 21, 15)
        ... )
    """
    symbol: str
    total_posts: int
    avg_sentiment: float
    most_recent_post: datetime
    
class PostDetail(BaseModel):
    """
    Detailed post information with sentiment analysis results.
    
    Complete post record from a data source with extracted symbols
    and computed sentiment score. Used for drill-down analysis and
    detailed reviews of individual posts.
    
    Attributes:
        source: Data source identifier ('reddit', 'threads', etc.)
        author: Post author/username (None if anonymous)
        created_at: When the post was originally created
        text: Full post content/text
        symbols: Comma-separated stock symbols mentioned in post
        sentiment: Sentiment score (-1.0 to 1.0)
        url: Direct link to the post (None if not available)
        
    Example:
        >>> post = PostDetail(
        ...     source="reddit",
        ...     author="stock_analyst_123",
        ...     created_at=datetime(2026, 2, 2, 20, 30),
        ...     text="AAPL looking bullish with strong earnings!",
        ...     symbols="AAPL",
        ...     sentiment=0.72,
        ...     url="https://reddit.com/r/stocks/comments/abc123"
        ... )
    """
    source: str
    author: str | None
    created_at: datetime
    text: str
    symbols: str
    sentiment: float
    url: str | None

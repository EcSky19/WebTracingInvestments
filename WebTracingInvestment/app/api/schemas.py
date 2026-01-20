from datetime import datetime
from pydantic import BaseModel

class HealthResponse(BaseModel):
    """Health check response"""
    ok: bool
    database: str
    posts_total: int | None = None
    sentiment_buckets: int | None = None
    error: str | None = None

class BucketOut(BaseModel):
    symbol: str
    bucket_start: datetime
    bucket: str
    post_count: int
    avg_sentiment: float

class SentimentDistribution(BaseModel):
    """Breakdown of sentiment counts: very negative, negative, neutral, positive, very positive"""
    symbol: str
    very_negative: int  # -1.0 to -0.6
    negative: int       # -0.6 to -0.2
    neutral: int        # -0.2 to 0.2
    positive: int       # 0.2 to 0.6
    very_positive: int  # 0.6 to 1.0
    total_posts: int
    avg_sentiment: float

class StockSentimentSummary(BaseModel):
    """Summary of all stocks and their sentiment counts"""
    symbol: str
    total_posts: int
    avg_sentiment: float
    most_recent_post: datetime
    
class PostDetail(BaseModel):
    """Individual post with text and sentiment"""
    source: str
    author: str | None
    created_at: datetime
    text: str
    symbols: str
    sentiment: float
    url: str | None

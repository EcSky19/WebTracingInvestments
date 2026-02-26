"""Database models for ORM."""

from datetime import datetime
from sqlmodel import SQLModel, Field, Index

__all__ = ["Post", "SentimentBucket"]

class Post(SQLModel, table=True):
    """
    Raw social post/comment (normalized across sources).
    
    Stores minimal raw fields + clean text for NLP processing.
    Each post is uniquely identified by (source, source_id) pair.
    """
    id: int | None = Field(default=None, primary_key=True)

    source: str = Field(index=True, min_length=1, max_length=50)           # "reddit" | "threads" | ...
    source_id: str = Field(index=True, min_length=1, max_length=255)       # unique id per source
    url: str | None = Field(default=None, max_length=1024)

    author: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(index=True)

    # Raw and cleaned text
    title: str | None = Field(default=None, max_length=512)
    text: str = Field(max_length=8192)
    text_clean: str = Field(default="", max_length=8192)

    # NLP outputs - sentiment is -1..1 normalized
    symbols: str = Field(default="", max_length=1024)                     # comma-separated symbols for MVP
    sentiment: float | None = Field(default=None, index=True, ge=-1.0, le=1.0)  # -1..1 range

    # Lightweight dedupe: source + source_id should be unique
    __table_args__ = (
        Index("ix_post_source_source_id_unique", "source", "source_id", unique=True),
        Index("ix_post_symbols_sentiment", "symbols", "sentiment"),  # For symbol-sentiment queries
    )

class SentimentBucket(SQLModel, table=True):
    """
    Aggregated sentiment per symbol per time bucket (e.g., hourly).
    This is what your UI / trading signals read from.
    """
    id: int | None = Field(default=None, primary_key=True)

    symbol: str = Field(index=True, min_length=1, max_length=10)
    bucket_start: datetime = Field(index=True)   # start of hour/day bucket
    bucket: str = Field(index=True, min_length=3, max_length=10)          # "hour" | "day"

    post_count: int = Field(default=0, ge=0)
    avg_sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    
    # Composite index for common query pattern
    __table_args__ = (
        Index("ix_sentiment_bucket_composite", "bucket", "bucket_start", "symbol"),
    )

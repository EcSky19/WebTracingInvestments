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

    source: str = Field(index=True)           # "reddit" | "threads" | ...
    source_id: str = Field(index=True)        # unique id per source
    url: str | None = None

    author: str | None = None
    created_at: datetime = Field(index=True)

    # Raw and cleaned text
    title: str | None = None
    text: str
    text_clean: str = ""

    # NLP outputs
    symbols: str = ""                         # comma-separated symbols for MVP
    sentiment: float | None = Field(default=None, index=True)  # -1..1

    # Lightweight dedupe: source + source_id should be unique
    __table_args__ = (
        Index("ix_post_source_source_id_unique", "source", "source_id", unique=True),
    )

class SentimentBucket(SQLModel, table=True):
    """
    Aggregated sentiment per symbol per time bucket (e.g., hourly).
    This is what your UI / trading signals read from.
    """
    id: int | None = Field(default=None, primary_key=True)

    symbol: str = Field(index=True)
    bucket_start: datetime = Field(index=True)   # start of hour/day bucket
    bucket: str = Field(index=True)              # "hour" | "day"

    post_count: int = 0
    avg_sentiment: float = 0.0

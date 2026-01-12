from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Index

class Post(SQLModel, table=True):
    """
    Raw social post/comment (normalized across sources).
    Store minimal raw fields + clean text for NLP.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    source: str = Field(index=True)           # "reddit" | "threads" | ...
    source_id: str = Field(index=True)        # unique id per source
    url: Optional[str] = None

    author: Optional[str] = None
    created_at: datetime = Field(index=True)

    # Raw and cleaned text
    title: Optional[str] = None
    text: str
    text_clean: str = ""

    # NLP outputs
    symbols: str = ""                         # comma-separated symbols for MVP
    sentiment: Optional[float] = Field(default=None, index=True)  # -1..1

    # Lightweight dedupe: source + source_id should be unique
    __table_args__ = (
        Index("ix_post_source_source_id_unique", "source", "source_id", unique=True),
    )

class SentimentBucket(SQLModel, table=True):
    """
    Aggregated sentiment per symbol per time bucket (e.g., hourly).
    This is what your UI / trading signals read from.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    symbol: str = Field(index=True)
    bucket_start: datetime = Field(index=True)   # start of hour/day bucket
    bucket: str = Field(index=True)              # "hour" | "day"

    post_count: int = 0
    avg_sentiment: float = 0.0

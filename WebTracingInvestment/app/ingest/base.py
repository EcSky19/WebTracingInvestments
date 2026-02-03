"""Base classes and protocols for data ingestion adapters."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

__all__ = ["RawItem", "Adapter"]

@dataclass
class RawItem:
    """
    Canonical item produced by any adapter.
    
    Standard data structure used by all ingestion adapters. The entire
    pipeline (NLP analysis, database storage, API responses) expects items
    in this format. Adapters are responsible for transforming source-specific
    formats into this uniform RawItem representation.
    
    This is the contract between adapters and the rest of the system.
    Everything downstream assumes this shape.
    
    Attributes:
        source: Data source identifier (e.g., 'reddit', 'threads')
                Used to distinguish post origins in database/reports
        source_id: Unique ID from the source (post ID, comment ID, etc.)
                   Combined with source for deduplication
        created_at: When the item was created (timezone-aware datetime)
                    ISO 8601 format preferred
        author: Author/username (optional, may be None for anonymous sources)
                Used for attribution and user-based filtering
        url: Direct link to the item (optional, for deep-linking)
             Used in API responses for user drill-down
        title: Item title (optional, may be None for some sources)
               For display in listings/headlines
        text: Main text content (required)
              Used for NLP analysis (symbol detection, sentiment)
              
    Example:
        >>> item = RawItem(
        ...     source="reddit",
        ...     source_id="t3_abc123",
        ...     created_at=datetime(2026, 2, 2, 20, 30, tzinfo=timezone.utc),
        ...     author="InvestmentGuy",
        ...     url="https://reddit.com/r/stocks/comments/abc123",
        ...     title="Bullish on AAPL",
        ...     text="Strong earnings report signals growth ahead"
        ... )
    """
    source: str
    source_id: str
    created_at: datetime
    author: str | None
    url: str | None
    title: str | None
    text: str

class Adapter(Protocol):
    """
    Protocol for data source adapters.
    
    Defines the interface that all data ingestion adapters must implement.
    Each adapter is responsible for fetching items from a specific source
    (e.g., Reddit, Threads) and transforming them into RawItem objects.
    
    The pipeline calls fetch() on each adapter and processes the returned
    items through NLP analysis and database storage.
    
    Implementations:
        - RedditAdapter: Fetches posts from Reddit via PRAW
        - ThreadsAdapter: Fetches posts from Threads via Meta Graph API
    
    Methods:
        fetch(): Generator that yields RawItem objects from the source.
                Each implementation decides its own pagination strategy.
                
    Example:
        >>> adapter = RedditAdapter(limit=50)
        >>> for item in adapter.fetch():
        ...     print(f"Fetched: {item.source_id}")
    """
    
    def fetch(self) -> Iterable[RawItem]:
        """
        Fetch items from data source.
        
        Each adapter decides its own pagination and rate-limiting strategy.
        This is a generator that yields RawItem objects one at a time
        as they are fetched from the source API.
        
        Returns:
            Iterable of RawItem objects from the source
            
        Raises:
            Exception: Implementation-specific errors (API errors, network issues, etc.)
                       Should be caught and logged by the caller (pipeline).
        """
        ...

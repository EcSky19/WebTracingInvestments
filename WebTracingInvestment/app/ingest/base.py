"""Base classes and protocols for data ingestion adapters."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

__all__ = ["RawItem", "Adapter"]

@dataclass
class RawItem:
    """
    Canonical item produced by any adapter.
    Everything else in the pipeline expects THIS shape.
    
    Attributes:
        source: Data source identifier (e.g., 'reddit', 'threads')
        source_id: Unique ID from the source
        created_at: When the item was created
        author: Author/username (optional)
        url: Direct link to the item (optional)
        title: Item title (optional)
        text: Main text content
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

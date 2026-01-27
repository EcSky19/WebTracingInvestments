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
    """Protocol for data source adapters."""
    
    def fetch(self) -> Iterable[RawItem]:
        """Pull newest items. Each adapter decides its own pagination strategy."""
        ...

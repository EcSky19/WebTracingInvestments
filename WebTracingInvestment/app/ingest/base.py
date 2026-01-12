from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol, Optional

@dataclass
class RawItem:
    """
    Canonical item produced by any adapter.
    Everything else in the pipeline expects THIS shape.
    """
    source: str
    source_id: str
    created_at: datetime
    author: Optional[str]
    url: Optional[str]
    title: Optional[str]
    text: str

class Adapter(Protocol):
    def fetch(self) -> Iterable[RawItem]:
        """Pull newest items. Each adapter decides its own pagination strategy."""
        ...

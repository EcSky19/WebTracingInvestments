"""Data processing pipeline: ingestion → NLP → storage with performance tracking."""

import logging
import time
from typing import Dict, Any
from app.ingest.base import RawItem
from app.db.models import Post
from app.db.repo import upsert_post
from app.nlp.entity import clean_text, detect_symbols
from app.nlp.sentiment import score_sentiment
from sqlmodel import Session

__all__ = ["process_item", "process_batch", "get_pipeline_metrics"]

logger = logging.getLogger(__name__)

# Pipeline metrics tracking
_pipeline_metrics: Dict[str, Any] = {
    "items_processed": 0,
    "items_inserted": 0,
    "items_skipped": 0,
    "items_failed": 0,
    "total_time_ms": 0.0,
    "avg_time_per_item_ms": 0.0,
}

def get_pipeline_metrics() -> Dict[str, Any]:
    """Return current pipeline metrics for monitoring."""
    return _pipeline_metrics.copy()

def process_item(session: Session, item: RawItem) -> bool:
    """
    Process a single item through the entire pipeline.
    
    Performs the following steps:
    1. Clean text (remove URLs, normalize whitespace)
    2. Detect tracked symbols (company mentions)
    3. Score sentiment using VADER
    4. Store post and metadata in database
    
    Early filtering: Posts mentioning no tracked symbols are discarded
    before sentiment analysis to avoid processing irrelevant content.
    
    Args:
        session: Database session
        item: Raw item from an ingestion adapter
        
    Returns:
        True if post was inserted (new post)
        False if post already existed (duplicate) or no tracked symbols found
        
    Example:
        >>> item = RawItem(source="reddit", source_id="abc123", ...)
        >>> process_item(session, item)
        True  # Post was inserted
    """
    global _pipeline_metrics
    start_time = time.time()
    
    try:
        _pipeline_metrics["items_processed"] += 1
        
        # Step 1: Clean text
        text_clean = clean_text(item.text)
        
        # Step 2: Detect symbols - early filter for irrelevant posts
        symbols = detect_symbols(text_clean)
        if not symbols:
            _pipeline_metrics["items_skipped"] += 1
            logger.debug(f"[{item.source}:{item.source_id}] Skipped - no tracked symbols")
            return False

        # Step 3: Score sentiment
        sent = score_sentiment(text_clean)
        
        logger.debug(f"[{item.source}:{item.author}] ✓ Symbols: {symbols} | Sentiment: {sent:.3f}")

        # Step 4: Create and insert post
        post = Post(
            source=item.source,
            source_id=item.source_id,
            url=item.url,
            author=item.author,
            created_at=item.created_at,
            title=item.title or "",
            text=item.text,
            text_clean=text_clean,
            symbols=",".join(symbols),
            sentiment=sent,
        )

        # Insert post (returns False if duplicate)
        inserted = upsert_post(session, post)
        if inserted:
            _pipeline_metrics["items_inserted"] += 1
        else:
            _pipeline_metrics["items_skipped"] += 1
        
        return inserted
        
    except Exception as e:
        _pipeline_metrics["items_failed"] += 1
        logger.error(f"Error processing item {item.source}:{item.source_id}: {e}", exc_info=True)
        raise
    finally:
        # Update timing metrics
        elapsed_ms = (time.time() - start_time) * 1000
        _pipeline_metrics["total_time_ms"] += elapsed_ms
        if _pipeline_metrics["items_processed"] > 0:
            _pipeline_metrics["avg_time_per_item_ms"] = (
                _pipeline_metrics["total_time_ms"] / _pipeline_metrics["items_processed"]
            )


def process_batch(session: Session, items: list[RawItem]) -> tuple[int, int]:
    """
    Process a batch of items through the pipeline efficiently.
    
    Useful for bulk operations during ingestion cycles.
    
    Args:
        session: Database session
        items: List of RawItem objects to process
        
    Returns:
        Tuple of (inserted_count, processed_count)
        
    Example:
        >>> items = [RawItem(...), RawItem(...)]
        >>> inserted, processed = process_batch(session, items)
        >>> print(f"Inserted {inserted}/{processed} items")
    """
    inserted = 0
    processed = 0
    
    for item in items:
        try:
            if process_item(session, item):
                inserted += 1
            processed += 1
        except Exception as e:
            logger.warning(f"Skipped item {item.source}:{item.source_id}: {e}")
            processed += 1
    
    return inserted, processed

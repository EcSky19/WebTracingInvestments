"""Data processing pipeline: ingestion → NLP → storage."""

import logging
from app.ingest.base import RawItem
from app.db.models import Post
from app.db.repo import upsert_post
from app.nlp.entity import clean_text, detect_symbols
from app.nlp.sentiment import score_sentiment
from sqlmodel import Session

__all__ = ["process_item"]

logger = logging.getLogger(__name__)

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
    text_clean = clean_text(item.text)
    symbols = detect_symbols(text_clean)

    # If you only care about tracked symbols, drop irrelevant posts early
    if not symbols:
        return False

    sent = score_sentiment(text_clean)
    
    logger.debug(f"[{item.source}:{item.author}] Symbols: {symbols} | Sentiment: {sent:.3f}")

    post = Post(
        source=item.source,
        source_id=item.source_id,
        url=item.url,
        author=item.author,
        created_at=item.created_at,
        title=item.title,
        text=item.text,
        text_clean=text_clean,
        symbols=",".join(symbols),
        sentiment=sent,
    )

    return upsert_post(session, post)

import logging
from app.ingest.base import RawItem
from app.db.models import Post
from app.db.repo import upsert_post
from app.nlp.entity import clean_text, detect_symbols
from app.nlp.sentiment import score_sentiment
from sqlmodel import Session

logger = logging.getLogger(__name__)

def process_item(session: Session, item: RawItem) -> bool:
    """
    One item through the whole pipeline.
    Returns True if inserted (new), False if duplicate.
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

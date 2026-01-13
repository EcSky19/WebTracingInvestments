from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from sqlmodel import select

from app.db.session import get_session
from app.db.models import SentimentBucket
from app.api.schemas import BucketOut

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}

@router.get("/sentiment/hourly", response_model=list[BucketOut])
def hourly(symbol: str | None = None, hours: int = 24):
    """
    Returns last N hours of hourly sentiment.
    """
    now = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=hours)

    with get_session() as session:
        q = select(SentimentBucket).where(
            SentimentBucket.bucket == "hour",
            SentimentBucket.bucket_start >= start,
        ).order_by(SentimentBucket.bucket_start.asc())

        if symbol:
            q = q.where(SentimentBucket.symbol == symbol.upper())

        rows = session.exec(q).all()
        return [BucketOut(**r.model_dump()) for r in rows]

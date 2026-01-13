from datetime import datetime
from pydantic import BaseModel

class BucketOut(BaseModel):
    symbol: str
    bucket_start: datetime
    bucket: str
    post_count: int
    avg_sentiment: float

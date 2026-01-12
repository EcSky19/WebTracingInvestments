from datetime import datetime, timezone
from typing import Iterable, List
import praw

from app.config import settings
from app.ingest.base import RawItem, Adapter

class RedditAdapter(Adapter):
    """
    MVP approach:
    - Pull hot/new posts from a handful of subreddits
    - Later: add comment streams, keyword search, rate-limit backoff, etc.
    """
    def __init__(self, subreddits: List[str] | None = None, limit: int = 50):
        self.subreddits = subreddits or ["stocks", "wallstreetbets", "investing", "technology", "CryptoCurrency"]
        self.limit = limit

        if not (settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET and settings.REDDIT_USER_AGENT):
            raise RuntimeError("Missing Reddit credentials in .env")

        self.client = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )

    def fetch(self) -> Iterable[RawItem]:
        for sr in self.subreddits:
            subreddit = self.client.subreddit(sr)
            # Choose one: .new(), .hot(), .top(time_filter="day")
            for submission in subreddit.new(limit=self.limit):
                created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                text = (submission.selftext or "").strip()
                title = (submission.title or "").strip()

                # Skip empty content posts (optional)
                if not title and not text:
                    continue

                yield RawItem(
                    source="reddit",
                    source_id=submission.id,
                    created_at=created,
                    author=str(submission.author) if submission.author else None,
                    url=f"https://www.reddit.com{submission.permalink}",
                    title=title,
                    text=(title + "\n\n" + text).strip(),
                )

import logging
import time
from datetime import datetime, timezone
from typing import Iterable
import praw
from praw.exceptions import PRAWException

from app.config import settings
from app.ingest.base import RawItem, Adapter

logger = logging.getLogger(__name__)

class RedditAdapter(Adapter):
    """
    Reddit adapter with rate limit handling.
    - Pulls new posts from tracked subreddits
    - Gracefully handles rate limits with backoff
    - Logs errors without breaking the pipeline
    """
    def __init__(self, subreddits: list[str] | None = None, limit: int = 50):
        self.subreddits = subreddits or ["stocks", "wallstreetbets", "investing", "technology", "CryptoCurrency"]
        self.limit = limit

        if not (settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET and settings.REDDIT_USER_AGENT):
            raise RuntimeError("Missing Reddit credentials in .env")

        self.client = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )
        
        logger.debug("Reddit client initialized")

    def fetch(self) -> Iterable[RawItem]:
        for sr in self.subreddits:
            try:
                subreddit = self.client.subreddit(sr)
                post_count = 0
                retry_count = 0
                max_retries = 3
                
                # Choose one: .new(), .hot(), .top(time_filter="day")
                while retry_count < max_retries:
                    try:
                        for submission in subreddit.new(limit=self.limit):
                            created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                            text = (submission.selftext or "").strip()
                            title = (submission.title or "").strip()

                            # Skip empty content posts (optional)
                            if not title and not text:
                                continue

                            post_count += 1
                            yield RawItem(
                                source="reddit",
                                source_id=submission.id,
                                created_at=created,
                                author=str(submission.author) if submission.author else None,
                                url=f"https://www.reddit.com{submission.permalink}",
                                title=title,
                                text=(title + "\n\n" + text).strip(),
                            )
                        logger.info(f"Reddit r/{sr}: Fetched {post_count} posts")
                        break  # Success, exit retry loop
                        
                    except PRAWException as e:
                        retry_count += 1
                        if "429" in str(e) or "rate limit" in str(e).lower():
                            wait_time = 2 ** retry_count  # Exponential backoff
                            logger.warning(f"Reddit r/{sr}: Rate limited, waiting {wait_time}s before retry {retry_count}/{max_retries}")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Reddit r/{sr}: API error - {e}")
                            break
                
                if post_count == 0 and retry_count > 0:
                    logger.warning(f"Reddit r/{sr}: No posts fetched after {retry_count} retries")
                    
            except Exception as e:
                logger.error(f"Reddit r/{sr}: Failed - {e}")

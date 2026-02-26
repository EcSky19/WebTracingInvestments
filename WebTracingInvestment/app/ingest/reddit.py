"""Reddit data ingestion adapter with rate limit handling and metrics."""

import logging
import time
from datetime import datetime, timezone
from typing import Iterable, Dict, Any
import praw
from praw.exceptions import PRAWException

from app.config import settings
from app.ingest.base import RawItem, Adapter

__all__ = ["RedditAdapter"]

logger = logging.getLogger(__name__)

# Metrics tracking
_reddit_metrics: Dict[str, Any] = {
    "fetches": 0,
    "posts_fetched": 0,
    "rate_limits_hit": 0,
    "errors": 0,
}

class RedditAdapter(Adapter):
    """
    Reddit data ingestion adapter with exponential backoff retry logic and metrics.
    
    Fetches new posts from specified subreddits, normalizes them to RawItem format,
    and handles rate limiting gracefully with exponential backoff. Tracks performance
    metrics for monitoring.
    
    Requires Reddit API credentials in .env:
    - REDDIT_CLIENT_ID
    - REDDIT_CLIENT_SECRET
    - REDDIT_USER_AGENT
    
    Attributes:
        subreddits: List of subreddit names to fetch from
        limit: Number of posts per subreddit per fetch (default 50)
        client: Authenticated PRAW Reddit client
        read_timeout: Timeout for Reddit API calls (default 16s)
        
    Example:
        >>> adapter = RedditAdapter(
        ...     subreddits=["stocks", "technology"],
        ...     limit=30
        ... )
        >>> for item in adapter.fetch():
        ...     print(item.source_id, item.text[:50])
    """
    def __init__(self, subreddits: list[str] | None = None, limit: int = 50, read_timeout: int = 16):
        """
        Initialize Reddit adapter with optional subreddits list.
        
        Args:
            subreddits: List of subreddit names. If None, uses defaults
            limit: Max posts per subreddit per fetch (default 50)
            read_timeout: Timeout for API calls in seconds (default 16)
            
        Raises:
            RuntimeError: If Reddit credentials are missing from .env
        """
        self.subreddits = subreddits or [
            "stocks", "wallstreetbets", "investing", "technology", "CryptoCurrency",
            "SecurityAnalysis", "ValueInvesting"
        ]
        self.limit = limit
        self.read_timeout = read_timeout

        if not (settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET and settings.REDDIT_USER_AGENT):
            raise RuntimeError("Missing Reddit credentials in .env: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT")

        try:
            self.client = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
                read_timeout=read_timeout,
            )
            # Verify credentials work
            self.client.user.me()  # This will raise if credentials are invalid
            logger.info("✓ Reddit client initialized and authenticated")
        except Exception as e:
            logger.error(f"✗ Reddit authentication failed: {e}")
            raise RuntimeError(f"Reddit API authentication failed: {e}")

    def fetch(self) -> Iterable[RawItem]:
        """
        Fetch new posts from Reddit subreddits with rate limit handling.
        
        Uses exponential backoff for rate limit errors.
        Tracks metrics for monitoring ingest health.
        """
        global _reddit_metrics
        
        for sr in self.subreddits:
            try:
                subreddit = self.client.subreddit(sr)
                post_count = 0
                retry_count = 0
                max_retries = 3
                
                # Choose one: .new(), .hot(), .top(time_filter="day")
                while retry_count < max_retries:
                    try:
                        logger.debug(f"Fetching from r/{sr} (limit={self.limit})")
                        
                        for submission in subreddit.new(limit=self.limit):
                            created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                            text = (submission.selftext or "").strip()
                            title = (submission.title or "").strip()

                            # Skip empty content posts
                            if not title and not text:
                                continue

                            post_count += 1
                            yield RawItem(
                                source="reddit",
                                source_id=submission.id,
                                created_at=created,
                                author=str(submission.author) if submission.author else "unknown",
                                url=f"https://www.reddit.com{submission.permalink}",
                                title=title,
                                text=(title + "\n\n" + text).strip(),
                            )
                        
                        logger.info(f"✓ r/{sr}: Fetched {post_count} posts")
                        _reddit_metrics["posts_fetched"] += post_count
                        _reddit_metrics["fetches"] += 1
                        break  # Success, exit retry loop
                        
                    except PRAWException as e:
                        retry_count += 1
                        error_str = str(e).lower()
                        
                        if "429" in str(e) or "rate limit" in error_str:
                            wait_time = min(2 ** retry_count, 60)  # Cap at 60s
                            _reddit_metrics["rate_limits_hit"] += 1
                            logger.warning(f"⏱ r/{sr}: Rate limited - waiting {wait_time}s (retry {retry_count}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"✗ r/{sr}: API error - {e}")
                            _reddit_metrics["errors"] += 1
                            break
                
                if post_count == 0 and retry_count > 0:
                    logger.warning(f"⚠ r/{sr}: No posts fetched after {retry_count} retries")
                    
            except Exception as e:
                logger.error(f"✗ r/{sr}: Error during fetch - {e}", exc_info=True)
                _reddit_metrics["errors"] += 1

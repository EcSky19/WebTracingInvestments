"""Threads (Meta) data ingestion adapter using Graph API."""

import logging
from typing import Iterable
from datetime import datetime, timezone
import httpx

from app.config import settings
from app.ingest.base import RawItem, Adapter

__all__ = ["ThreadsAdapter"]

logger = logging.getLogger(__name__)

class ThreadsAdapter(Adapter):
    """
    Threads (Meta) data ingestion adapter using Graph API.
    
    Fetches posts from Meta's Threads social media platform using the Graph API.
    This adapter is optional and gracefully degrades if credentials are missing.
    
    Requires Threads API credentials in .env (optional):
    - THREADS_ACCESS_TOKEN: Meta Graph API access token
    - THREADS_USER_ID: Your Threads user ID
    
    API Endpoint: GET /{user_id}/threads
    
    Fields: id, text, timestamp, permalink_url, username
    
    Attributes:
        limit: Number of posts to fetch per request (default 50)
        token: Graph API access token (optional)
        user_id: Threads user ID (optional)
        
    Note:
        If credentials are missing, this adapter returns no items (no-op).
        It will not raise an error, allowing the pipeline to continue.
    """
    def __init__(self, limit: int = 50):
        """
        Initialize Threads adapter (optional credentials).
        
        Args:
            limit: Max posts per fetch (default 50)
        """
        self.limit = limit
        self.token = settings.THREADS_ACCESS_TOKEN
        self.user_id = settings.THREADS_USER_ID
        
        if self.token and self.user_id:
            logger.info(f"✓ Threads adapter initialized (user_id: {self.user_id})")
        else:
            logger.warning("✗ Threads adapter: Missing credentials (THREADS_ACCESS_TOKEN or THREADS_USER_ID)")

    def fetch(self) -> Iterable[RawItem]:
        """
        Fetch new posts from Threads API (no-op if credentials missing).
        
        Uses the Meta Graph API to retrieve user's recent posts.
        Rate limit: 200 requests/hour per user.
        
        Returns:
            Iterable of RawItem dictionaries with posts fetched from Threads.
            Returns empty iterator if credentials are missing.
            
        Raises:
            httpx.RequestError: If API request fails (connection, timeout, etc.)
            httpx.HTTPStatusError: If API returns error status (401, 404, 429, etc.)
            json.JSONDecodeError: If response is not valid JSON.
        """
        if not (self.token and self.user_id):
            return  # no-op if credentials missing

        try:
            # Meta Graph API endpoint for user's threads
            url = f"https://graph.threads.net/v1.0/{self.user_id}/threads"
            params = {
                "fields": "id,text,timestamp,permalink_url,username",
                "limit": self.limit,
                "access_token": self.token,
            }
            
            logger.debug(f"Fetching from Threads API: {url}")
            
            with httpx.Client(timeout=20) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            post_count = 0
            for item in data.get("data", []):
                try:
                    # Parse timestamp (ISO 8601 format)
                    created_str = item.get("timestamp", datetime.now(tz=timezone.utc).isoformat())
                    created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    
                    post_count += 1
                    yield RawItem(
                        source="threads",
                        source_id=str(item["id"]),
                        created_at=created,
                        author=item.get("username"),
                        url=item.get("permalink_url"),
                        title=None,
                        text=item.get("text", ""),
                    )
                except Exception as e:
                    logger.debug(f"Error parsing Threads post {item.get('id')}: {e}")
                    continue
            
            logger.info(f"Threads API: Fetched {post_count} posts")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Threads API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            logger.error(f"Threads API error: {e}")

from typing import Iterable
from datetime import datetime, timezone
import httpx

from app.config import settings
from app.ingest.base import RawItem, Adapter

class ThreadsAdapter(Adapter):
    """
    Placeholder adapter.
    Reality: Threads API access is the main friction point.
    If you have Graph API endpoints available, implement them here.

    MVP option:
    - Fetch recent posts from your own account (or a test account)
    - Or query a curated list of accounts/hashtags if allowed by API
    """
    def __init__(self, limit: int = 50):
        self.limit = limit
        self.token = settings.THREADS_ACCESS_TOKEN
        self.user_id = settings.THREADS_USER_ID

    def fetch(self) -> Iterable[RawItem]:
        if not (self.token and self.user_id):
            return  # silently no-op for MVP until you have access

        # TODO: Replace with real Threads Graph API endpoint you’re authorized for.
        # Example pseudo:
        # GET /{user_id}/threads?fields=id,text,timestamp,permalink_url,username&access_token=...
        url = "https://graph.facebook.com/v19.0/..."
        headers = {"Authorization": f"Bearer {self.token}"}

        with httpx.Client(timeout=20) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        for item in data.get("data", []):
            # TODO: map actual fields
            created = datetime.now(tz=timezone.utc)
            yield RawItem(
                source="threads",
                source_id=str(item["id"]),
                created_at=created,
                author=item.get("username"),
                url=item.get("permalink_url"),
                title=None,
                text=item.get("text", ""),
            )

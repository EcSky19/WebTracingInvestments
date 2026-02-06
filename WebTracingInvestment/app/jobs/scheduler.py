"""Background job scheduler for periodic ingestion tasks."""

import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import get_session
from app.ingest.reddit import RedditAdapter
from app.ingest.threads import ThreadsAdapter
from app.services.pipeline import process_item
from app.services.aggregation import aggregate_hour, floor_to_hour

__all__ = ["run_ingest_once", "start_scheduler", "scheduler"]

logger = logging.getLogger(__name__)
scheduler: BackgroundScheduler | None = None

def run_ingest_once():
    """
    Pull from sources, push through pipeline.
    """
    start_time = datetime.now(tz=timezone.utc)
    logger.info("=== Starting ingest cycle ===")
    
    adapters = []

    # Reddit will throw if creds missing (good; fail loud)
    try:
        adapters.append(RedditAdapter(limit=30))
        logger.info("✓ Reddit adapter initialized")
    except Exception as e:
        logger.warning(f"✗ Reddit adapter failed: {e}")

    # Threads is no-op unless token/user_id set
    adapters.append(ThreadsAdapter(limit=30))

    inserted = 0
    total_posts = 0
    with get_session() as session:
        for ad in adapters:
            adapter_name = ad.__class__.__name__
            adapter_posts = 0
            try:
                for item in ad.fetch():
                    total_posts += 1
                    adapter_posts += 1
                    if process_item(session, item):
                        inserted += 1
                logger.info(f"[{adapter_name}] Processed {adapter_posts} posts, {inserted} new total")
            except Exception as e:
                logger.error(f"[{adapter_name}] Error: {e}")

        # After ingest, update current hour aggregate
        now = datetime.now(tz=timezone.utc)
        aggregate_hour(session, floor_to_hour(now))
        logger.info(f"✓ Aggregated sentiment for hour: {floor_to_hour(now)}")

    elapsed = (datetime.now(tz=timezone.utc) - start_time).total_seconds()
    logger.info(f"=== Ingest cycle complete: {inserted}/{total_posts} new posts in {elapsed:.2f}s ===")
    return inserted

def start_scheduler() -> BackgroundScheduler:
    """Initialize and start the background scheduler."""
    global scheduler
    try:
        scheduler = BackgroundScheduler(timezone="UTC")
        # MVP cadence: every 5 minutes
        scheduler.add_job(run_ingest_once, "interval", minutes=5, id="ingest")
        scheduler.start()
        logger.info("Background scheduler started successfully")
        return scheduler
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise

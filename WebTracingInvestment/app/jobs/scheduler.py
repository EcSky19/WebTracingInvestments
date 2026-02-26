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
    Pull from sources, push through pipeline with improved error handling.
    """
    start_time = datetime.now(tz=timezone.utc)
    logger.info("=== Starting ingest cycle ===")
    
    adapters = []

    # Reddit will throw if creds missing (good; fail loud)
    try:
        adapters.append(RedditAdapter(limit=30))
        logger.info("✓ Reddit adapter initialized")
    except Exception as e:
        logger.warning(f"✗ Reddit adapter failed to initialize: {e}")

    # Threads is no-op unless token/user_id set
    try:
        adapters.append(ThreadsAdapter(limit=30))
    except Exception as e:
        logger.warning(f"✗ Threads adapter failed to initialize: {e}")

    inserted = 0
    total_posts = 0
    errors_by_adapter = {}
    
    try:
        with get_session() as session:
            for ad in adapters:
                adapter_name = ad.__class__.__name__
                adapter_posts = 0
                adapter_errors = 0
                
                try:
                    for item in ad.fetch():
                        total_posts += 1
                        adapter_posts += 1
                        try:
                            if process_item(session, item):
                                inserted += 1
                        except Exception as e:
                            adapter_errors += 1
                            logger.debug(f"[{adapter_name}] Failed to process item: {e}")
                            if adapter_errors > 10:  # Circuit breaker: stop after 10 errors
                                logger.error(f"[{adapter_name}] Too many processing errors, skipping remaining")
                                break
                    
                    if adapter_errors > 0:
                        errors_by_adapter[adapter_name] = adapter_errors
                    logger.info(f"[{adapter_name}] Processed {adapter_posts} posts, {inserted} new total, {adapter_errors} errors")
                except Exception as e:
                    logger.error(f"[{adapter_name}] Fatal error during fetch: {e}", exc_info=True)
                    errors_by_adapter[adapter_name] = str(e)

            # After ingest, update current hour aggregate
            try:
                now = datetime.now(tz=timezone.utc)
                aggregate_hour(session, floor_to_hour(now))
                logger.info(f"✓ Aggregated sentiment for hour: {floor_to_hour(now)}")
            except Exception as e:
                logger.error(f"Failed to aggregate hour: {e}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Fatal error in ingest cycle: {e}", exc_info=True)

    elapsed = (datetime.now(tz=timezone.utc) - start_time).total_seconds()
    status = f"{inserted}/{total_posts} new posts in {elapsed:.2f}s"
    if errors_by_adapter:
        status += f" | Errors: {errors_by_adapter}"
    logger.info(f"=== Ingest cycle complete: {status} ===")
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

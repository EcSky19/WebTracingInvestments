"""Background job scheduler for periodic ingestion tasks."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import get_session
from app.ingest.reddit import RedditAdapter
from app.ingest.threads import ThreadsAdapter
from app.services.pipeline import process_item
from app.services.aggregation import aggregate_hour, floor_to_hour

__all__ = ["run_ingest_once", "start_scheduler", "scheduler", "get_ingest_metrics"]

logger = logging.getLogger(__name__)
scheduler: BackgroundScheduler | None = None

# Metrics tracking for monitoring
_ingest_metrics: Dict[str, Any] = {
    "total_cycles": 0,
    "total_posts_processed": 0,
    "total_posts_inserted": 0,
    "total_errors": 0,
    "last_run": None,
    "last_run_duration": 0.0,
}

def get_ingest_metrics() -> Dict[str, Any]:
    """Return current ingest metrics for monitoring."""
    return _ingest_metrics.copy()

def run_ingest_once():
    """
    Pull from sources, push through pipeline with improved error handling and metrics.
    """
    global _ingest_metrics
    
    start_time = datetime.now(tz=timezone.utc)
    logger.info("═" * 60)
    logger.info("Starting ingest cycle")
    logger.info("═" * 60)
    
    adapters = []
    adapter_init_errors = []

    # Reddit will throw if creds missing (good; fail loud)
    try:
        adapters.append(RedditAdapter(limit=30))
        logger.info("✓ Reddit adapter initialized")
    except Exception as e:
        logger.warning(f"✗ Reddit adapter failed to initialize: {e}")
        adapter_init_errors.append(("Reddit", str(e)))

    # Threads is no-op unless token/user_id set
    try:
        adapters.append(ThreadsAdapter(limit=30))
        logger.info("✓ Threads adapter initialized")
    except Exception as e:
        logger.warning(f"✗ Threads adapter failed to initialize: {e}")
        adapter_init_errors.append(("Threads", str(e)))

    if not adapters:
        logger.error("No adapters available to ingest - check credentials")
        return 0

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
                            _ingest_metrics["total_errors"] += 1
                            logger.debug(f"[{adapter_name}] Failed to process item: {e}")
                            if adapter_errors > 10:  # Circuit breaker: stop after 10 errors
                                logger.error(f"[{adapter_name}] Circuit breaker triggered - too many errors")
                                break
                    
                    if adapter_errors > 0:
                        errors_by_adapter[adapter_name] = adapter_errors
                    logger.info(f"[{adapter_name}] ✓ {adapter_posts} posts, {inserted} new, {adapter_errors} errors")
                except Exception as e:
                    logger.error(f"[{adapter_name}] ✗ Fatal error: {e}", exc_info=True)
                    errors_by_adapter[adapter_name] = {"error": str(e), "type": type(e).__name__}

            # After ingest, update current hour aggregate
            try:
                now = datetime.now(tz=timezone.utc)
                aggregate_hour(session, floor_to_hour(now))
                logger.info(f"✓ Aggregation complete for {floor_to_hour(now)}")
            except Exception as e:
                logger.error(f"Aggregation failed: {e}", exc_info=True)
                _ingest_metrics["total_errors"] += 1
    
    except Exception as e:
        logger.error(f"Fatal error in ingest cycle: {e}", exc_info=True)
        _ingest_metrics["total_errors"] += 1
        return inserted

    # Update metrics
    elapsed = (datetime.now(tz=timezone.utc) - start_time).total_seconds()
    _ingest_metrics["total_cycles"] += 1
    _ingest_metrics["total_posts_processed"] += total_posts
    _ingest_metrics["total_posts_inserted"] += inserted
    _ingest_metrics["last_run"] = start_time.isoformat()
    _ingest_metrics["last_run_duration"] = elapsed

    # Log summary
    logger.info(f"═ Summary ═ {inserted}/{total_posts} new posts in {elapsed:.2f}s")
    if errors_by_adapter:
        logger.warning(f"Adapter errors: {errors_by_adapter}")
    if adapter_init_errors:
        logger.warning(f"Init errors: {adapter_init_errors}")
    logger.info("═" * 60)
    
    return inserted
        logger.error(f"Fatal error in ingest cycle: {e}", exc_info=True)

    elapsed = (datetime.now(tz=timezone.utc) - start_time).total_seconds()
    status = f"{inserted}/{total_posts} new posts in {elapsed:.2f}s"
    if errors_by_adapter:
        status += f" | Errors: {errors_by_adapter}"
    logger.info(f"=== Ingest cycle complete: {status} ===")
    return inserted

def start_scheduler() -> BackgroundScheduler:
    """Initialize and start the background scheduler with monitoring."""
    global scheduler
    try:
        scheduler = BackgroundScheduler(timezone="UTC")
        # MVP cadence: every 5 minutes
        scheduler.add_job(run_ingest_once, "interval", minutes=5, id="ingest", 
                         name="Reddit/Threads Ingestion", replace_existing=True)
        scheduler.start()
        logger.info("✓ Background scheduler initialized successfully")
        logger.info(f"  - Ingest job: every 5 minutes")
        logger.info(f"  - Running in timezone: UTC")
        return scheduler
    except Exception as e:
        logger.error(f"✗ Failed to start scheduler: {e}", exc_info=True)
        raise

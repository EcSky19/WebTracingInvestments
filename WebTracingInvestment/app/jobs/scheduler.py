from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import get_session
from app.ingest.reddit import RedditAdapter
from app.ingest.threads import ThreadsAdapter
from app.services.pipeline import process_item
from app.services.aggregation import aggregate_hour, floor_to_hour

def run_ingest_once():
    """
    Pull from sources, push through pipeline.
    """
    adapters = []

    # Reddit will throw if creds missing (good; fail loud)
    adapters.append(RedditAdapter(limit=30))

    # Threads is no-op unless token/user_id set
    adapters.append(ThreadsAdapter(limit=30))

    inserted = 0
    with get_session() as session:
        for ad in adapters:
            for item in ad.fetch():
                if process_item(session, item):
                    inserted += 1

        # After ingest, update current hour aggregate
        now = datetime.now(tz=timezone.utc)
        aggregate_hour(session, floor_to_hour(now))

    return inserted

def start_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="UTC")

    # MVP cadence: every 5 minutes
    sched.add_job(run_ingest_once, "interval", minutes=5, id="ingest")

    sched.start()
    return sched

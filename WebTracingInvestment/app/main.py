"""Main application factory and entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.logging import setup_logging
from app.db.session import init_db
from app.api.routes import router
from app.jobs.scheduler import start_scheduler, scheduler

__all__ = ["app", "create_app"]

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events for the application."""
    # Startup
    logger.info("Application starting up...")
    yield
    # Shutdown
    logger.info("Application shutting down...")
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown complete")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Initialize logging and database with error handling
    try:
        setup_logging()
        logger.info("Logging initialized")
    except Exception as e:
        logger.error(f"Failed to initialize logging: {e}", exc_info=True)
        raise
    
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise

    app = FastAPI(
        title="Social Sentiment MVP",
        description="Real-time sentiment analysis for stock market research",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(router)

    # Start scheduler in-process with error handling.
    # Later: move this to a separate worker container (cleaner + scalable).
    try:
        start_scheduler()
        logger.info("Background scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {e}", exc_info=True)
        # Don't crash app if scheduler fails - it's background work
        logger.warning("Continuing without background scheduler")

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI
from app.core.logging import setup_logging
from app.db.session import init_db
from app.api.routes import router
from app.jobs.scheduler import start_scheduler

def create_app() -> FastAPI:
    setup_logging()
    init_db()

    app = FastAPI(title="Social Sentiment MVP")
    app.include_router(router)

    # Start scheduler in-process.
    # Later: move this to a separate worker container (cleaner + scalable).
    start_scheduler()

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

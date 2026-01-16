import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)  # Suppress SQL logs
    logging.getLogger("httpx").setLevel(logging.WARNING)

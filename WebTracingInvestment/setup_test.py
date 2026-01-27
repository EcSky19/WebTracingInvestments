#!/usr/bin/env python
"""Setup verification script to test all components are working.

Run this after configuring .env to verify the system.

Usage:
    python setup_test.py
"""

import sys
import logging
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("setup_test")

def test_config():
    """Test that configuration loads"""
    try:
        from app.config import settings
        logger.info("✓ Config loaded successfully")
        logger.info(f"  - ENV: {settings.ENV}")
        logger.info(f"  - DATABASE_URL: {settings.DATABASE_URL}")
        
        if settings.REDDIT_CLIENT_ID:
            logger.info("✓ Reddit credentials configured")
        else:
            logger.warning("✗ Reddit credentials not configured (Reddit ingestion will fail)")
        
        if settings.THREADS_ACCESS_TOKEN:
            logger.info("✓ Threads credentials configured")
        else:
            logger.warning("✗ Threads credentials not configured (Threads will be skipped)")
        
        return True
    except Exception as e:
        logger.error(f"✗ Config failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    try:
        from app.db.session import init_db, get_session
        from app.db.models import Post, SentimentBucket
        
        logger.info("Testing database...")
        init_db()
        logger.info("✓ Database initialized")
        
        with get_session() as session:
            logger.info("✓ Database connection successful")
        
        return True
    except Exception as e:
        logger.error(f"✗ Database failed: {e}")
        return False

def test_nlp():
    """Test NLP components"""
    try:
        from app.nlp.entity import detect_symbols, clean_text
        from app.nlp.sentiment import score_sentiment
        
        logger.info("Testing NLP...")
        
        test_text = "TSLA is amazing! Elon Musk is a genius. Tesla stock will moon."
        
        # Test cleaning
        cleaned = clean_text(test_text)
        logger.info(f"  - Text cleaned: {cleaned[:50]}...")
        
        # Test symbol detection
        symbols = detect_symbols(cleaned)
        logger.info(f"✓ Symbol detection: found {symbols}")
        
        # Test sentiment
        sentiment = score_sentiment(cleaned)
        logger.info(f"✓ Sentiment scoring: {sentiment:.3f}")
        
        return True
    except Exception as e:
        logger.error(f"✗ NLP failed: {e}")
        return False

def test_reddit():
    """Test Reddit adapter (if credentials available)"""
    try:
        from app.config import settings
        
        if not settings.REDDIT_CLIENT_ID:
            logger.info("⊘ Reddit test skipped (no credentials)")
            return True
        
        from app.ingest.reddit import RedditAdapter
        
        logger.info("Testing Reddit adapter...")
        adapter = RedditAdapter(limit=1)
        
        # Try to fetch one post
        posts = []
        for post in adapter.fetch():
            posts.append(post)
            if len(posts) >= 1:
                break
        
        if posts:
            logger.info(f"✓ Reddit adapter working (fetched {len(posts)} posts)")
        else:
            logger.warning("⊘ Reddit adapter returned no posts")
        
        return True
    except Exception as e:
        logger.error(f"✗ Reddit adapter failed: {e}")
        return False

def test_api():
    """Test API endpoints"""
    try:
        from app.api.routes import router
        
        logger.info("Testing API...")
        
        # Check routes exist
        routes = [route.path for route in router.routes]
        required = ["/health", "/sentiment/hourly", "/sentiment/distribution", "/sentiment/stocks", "/posts"]
        
        found = []
        missing = []
        for req in required:
            if any(req in route for route in routes):
                found.append(req)
            else:
                missing.append(req)
        
        logger.info(f"✓ API routes found: {found}")
        if missing:
            logger.warning(f"✗ Missing routes: {missing}")
        
        return len(missing) == 0
    except Exception as e:
        logger.error(f"✗ API test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("WebTracingInvestment Setup Verification")
    logger.info("=" * 60)
    
    tests = [
        ("Configuration", test_config),
        ("Database", test_database),
        ("NLP", test_nlp),
        ("Reddit Adapter", test_reddit),
        ("API Routes", test_api),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info("")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"✗ {name} test failed: {e}")
            results.append((name, False))
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        logger.info(f"{status} {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n✓ All systems ready! Start the server with:")
        logger.info("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return 0
    else:
        logger.warning("\n✗ Some tests failed. Check configuration and dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

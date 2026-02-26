"""Sentiment analysis module using VADER sentiment analyzer with caching."""

import logging
from functools import lru_cache
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

__all__ = ["score_sentiment", "get_sentiment_details", "clear_sentiment_cache"]

logger = logging.getLogger(__name__)

# Initialize VADER analyzer once at module load
_analyzer = SentimentIntensityAnalyzer()


@lru_cache(maxsize=10000)
def score_sentiment(text: str) -> float:
    """
    Analyze sentiment of text and return a compound score using VADER.
    
    Uses VADER (Valence Aware Dictionary and sEntiment Reasoner) sentiment
    analyzer, which works well for social media text including slang and emojis.
    
    Results are cached for improved performance on repeated text inputs.
    
    Args:
        text: Text to analyze for sentiment (must be hashable string)
        
    Returns:
        Sentiment score in range [-1.0, 1.0] where:
        - Negative values indicate negative sentiment (-1 = most negative)
        - Positive values indicate positive sentiment (+1 = most positive)
        - Values near 0 indicate neutral sentiment
        
    Note:
        This is NOT finance-aware. It's an MVP baseline using general sentiment.
        Consider upgrading to FinBERT for domain-specific accuracy.
        
        Upgrade path:
        - FinBERT / domain-specific financial sentiment model
        - Separate scores for hype vs fear vs uncertainty
        - Sarcasm detection heuristics for Reddit/WSB-style posts
        - Portfolio impact weighting
    """
    try:
        vs = _analyzer.polarity_scores(text)
        compound = float(vs["compound"])
        return compound
    except Exception as e:
        logger.error(f"Error scoring sentiment: {e}")
        return 0.0  # Return neutral if error


def get_sentiment_details(text: str) -> dict:
    """
    Get detailed sentiment breakdown including component scores.
    
    Returns individual positive, negative, neutral scores in addition to compound.
    Useful for debugging and understanding sentiment composition.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with keys:
        - compound: Overall sentiment (-1 to 1)
        - positive: Proportion of positive words (0-1)
        - negative: Proportion of negative words (0-1)
        - neutral: Proportion of neutral words (0-1)
        
    Example:
        >>> details = get_sentiment_details("I love this stock! 🚀")
        >>> print(details['compound'])  # High positive
        >>> print(details['positive'])  # High proportion
    """
    try:
        vs = _analyzer.polarity_scores(text)
        return {
            "compound": float(vs.get("compound", 0.0)),
            "positive": float(vs.get("pos", 0.0)),
            "negative": float(vs.get("neg", 0.0)),
            "neutral": float(vs.get("neu", 0.0)),
        }
    except Exception as e:
        logger.error(f"Error getting sentiment details: {e}")
        return {
            "compound": 0.0,
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 1.0,
        }


def clear_sentiment_cache() -> None:
    """
    Clear the sentiment analysis cache.
    
    Useful after model updates or when you want to re-analyze text.
    """
    score_sentiment.cache_clear()
    logger.info("Sentiment analysis cache cleared")

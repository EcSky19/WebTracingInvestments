"""Sentiment analysis module using VADER sentiment analyzer."""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

__all__ = ["score_sentiment"]

_analyzer = SentimentIntensityAnalyzer()


def score_sentiment(text: str) -> float:
    """
    Analyze sentiment of text and return a compound score.
    
    Uses VADER (Valence Aware Dictionary and sEntiment Reasoner) sentiment
    analyzer, which works well for social media text.
    
    Args:
        text: Text to analyze for sentiment
        
    Returns:
        Sentiment score in range [-1.0, 1.0] where:
        - Negative values indicate negative sentiment
        - Positive values indicate positive sentiment
        - Values near 0 indicate neutral sentiment
        
    Note:
        This is NOT finance-aware. It's an MVP baseline.
        Consider upgrading to FinBERT for domain-specific accuracy.
        
    Upgrade path:
        - FinBERT / domain-specific model
        - separate scores for hype vs fear vs uncertainty
        - sarcasm detection heuristics for WSB-style posts
    """
    vs = _analyzer.polarity_scores(text)
    return float(vs["compound"])

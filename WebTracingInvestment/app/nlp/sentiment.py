"""Sentiment analysis module using VADER sentiment analyzer."""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

__all__ = ["score_sentiment"]

def score_sentiment(text: str) -> float:
    """
    Returns compound sentiment in [-1, 1].
    This is NOT finance-aware. It’s an MVP baseline.

    Upgrade path:
    - FinBERT / domain model
    - separate scores for hype vs fear vs uncertainty
    - sarcasm heuristics for WSB-style posts
    """
    vs = _analyzer.polarity_scores(text)
    return float(vs["compound"])

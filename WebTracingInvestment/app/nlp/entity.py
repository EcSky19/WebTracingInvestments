"""Entity extraction and symbol detection from text."""

import re
from app.core.symbols import all_aliases_upper

__all__ = ["detect_symbols", "clean_text"]

ALIAS_MAP = all_aliases_upper()

def detect_symbols(text: str) -> list[str]:
    """
    Detect stock ticker symbols mentioned in text.
    
    Uses simple but fast substring matching against a pre-built alias map.
    Text is converted to uppercase and checked for exact matches with known
    company aliases (ticker symbols, company names, product names, CEO names, etc.)
    
    Args:
        text: Text to search for symbol mentions
        
    Returns:
        List of detected stock symbols (ticker codes like 'TSLA', 'AAPL', etc.)
        
    Note:
        This is a simple MVP approach. Later upgrades could include:
        - Word-boundary regex to avoid false positives
        - Cashtag detection ($TSLA)
        - Disambiguation (e.g., "Apple" fruit vs Apple Inc.)
    """
    t = text.upper()
    hits = []
    for sym, aliases in ALIAS_MAP.items():
        if any(a in t for a in aliases):
            hits.append(sym)
    return hits

def clean_text(text: str) -> str:
    """
    Normalize text for sentiment analysis.
    
    Removes URLs and extra whitespace that could interfere with sentiment
    scoring. This helps prevent links and formatting from distorting results.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text with URLs removed and whitespace normalized
    """
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

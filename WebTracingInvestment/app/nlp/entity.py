"""Entity extraction and symbol detection from text."""

import re
from app.core.symbols import all_aliases_upper

__all__ = ["detect_symbols", "clean_text"]

ALIAS_MAP = all_aliases_upper()

# Precompile regex patterns for performance
_URL_PATTERN = re.compile(r"http\S+")
_WHITESPACE_PATTERN = re.compile(r"\s+")

# Build compiled symbol patterns once at startup for efficiency
_SYMBOL_PATTERNS = {}
for sym, aliases in ALIAS_MAP.items():
    # Create one pattern per symbol combining all aliases with OR
    pattern_parts = [re.escape(alias) for alias in aliases]
    pattern_str = r'\b(' + '|'.join(pattern_parts) + r')\b'
    _SYMBOL_PATTERNS[sym] = re.compile(pattern_str, re.IGNORECASE)

def detect_symbols(text: str) -> list[str]:
    """
    Detect stock ticker symbols mentioned in text.
    
    Uses pre-compiled word-boundary regex matching against known aliases.
    Text is checked for matches with known company aliases (ticker symbols, 
    company names, product names, CEO names, etc.). Compiled patterns are 
    cached for performance.
    
    Args:
        text: Text to search for symbol mentions
        
    Returns:
        List of detected stock symbols (ticker codes like 'TSLA', 'AAPL', etc.)
        Deduped and sorted for consistency.
        
    Note:
        Uses word boundaries to avoid false positives. 
        Patterns are pre-compiled at module load for speed.
        
        Future upgrades:
        - Cashtag detection ($TSLA)
        - Disambiguation (e.g., "Apple" fruit vs Apple Inc.)
    """
    hits = set()  # Use set to avoid duplicates
    
    # Check pre-compiled patterns for efficiency
    for sym, pattern in _SYMBOL_PATTERNS.items():
        if pattern.search(text):
            hits.add(sym)
    
    return sorted(hits)  # Return sorted for consistent output

def clean_text(text: str) -> str:
    """
    Normalize text for sentiment analysis.
    
    Removes URLs and normalizes whitespace that could interfere with sentiment
    scoring. Uses pre-compiled regex patterns for efficiency.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text with URLs removed and whitespace normalized
    """
    text = _URL_PATTERN.sub(" ", text)
    text = _WHITESPACE_PATTERN.sub(" ", text).strip()
    return text

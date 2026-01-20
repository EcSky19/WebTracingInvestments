"""Entity extraction and symbol detection from text."""
import re
from app.core.symbols import all_aliases_upper

ALIAS_MAP = all_aliases_upper()

def detect_symbols(text: str) -> list[str]:
    """
    Dumb-but-fast matching:
    - Uppercase text
    - Exact substring match against alias list

    Later upgrades:
    - word-boundary regex per alias
    - $TSLA cashtags
    - disambiguation (e.g., "Apple" fruit vs company)
    """
    t = text.upper()
    hits = []
    for sym, aliases in ALIAS_MAP.items():
        if any(a in t for a in aliases):
            hits.append(sym)
    return hits

def clean_text(text: str) -> str:
    """
    Basic normalization so sentiment doesn’t get wrecked by links/markup.
    """
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

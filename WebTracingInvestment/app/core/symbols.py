"""Central configuration for tracked symbols and aliases.

This module defines which companies/stocks are tracked and their various
aliases (ticker symbols, company names, product names, CEO names, etc.)

Update TRACKED dict to add more symbols or refine existing aliases based on
what you observe in real social media posts.
"""

__all__ = ["TRACKED", "all_aliases_upper"]

# Central truth for what you track.
# You will expand aliases over time based on what you see in real posts.
# Tip: keep aliases mostly uppercase terms and common company/product names.

TRACKED = {
    "NVDA": {
        "name": "NVIDIA",
        "aliases": ["NVDA", "NVIDIA", "GEFORCE", "RTX", "JENSEN", "HUANG"],
        "ceo": "Jensen Huang",
    },
    "AMD": {
        "name": "AMD",
        "aliases": ["AMD", "ADVANCED MICRO DEVICES", "RYZEN", "RADEON", "LISA SU"],
        "ceo": "Lisa Su",
    },
    "AVGO": {
        "name": "Broadcom",
        "aliases": ["AVGO", "BROADCOM", "VMWARE"],
        "ceo": "Hock Tan",
    },
    "TSLA": {"name": "Tesla", "aliases": ["TSLA", "TESLA", "ELON", "MUSK"], "ceo": "Elon Musk"},
    "NFLX": {"name": "Netflix", "aliases": ["NFLX", "NETFLIX"], "ceo": "Greg Peters"},
    "AAPL": {"name": "Apple", "aliases": ["AAPL", "APPLE", "IPHONE", "TIM COOK"], "ceo": "Tim Cook"},
    "GOOG": {"name": "Alphabet", "aliases": ["GOOG", "GOOGL", "ALPHABET", "GOOGLE", "SUNDAR"], "ceo": "Sundar Pichai"},
    "META": {"name": "Meta", "aliases": ["META", "FACEBOOK", "INSTAGRAM", "WHATSAPP", "ZUCK"], "ceo": "Mark Zuckerberg"},
    "AMZN": {"name": "Amazon", "aliases": ["AMZN", "AMAZON", "AWS", "JASSY"], "ceo": "Andy Jassy"},
    "PLTR": {"name": "Palantir", "aliases": ["PLTR", "PALANTIR", "KARP"], "ceo": "Alex Karp"},
    "MSFT": {"name": "Microsoft", "aliases": ["MSFT", "MICROSOFT", "AZURE", "SATYA"], "ceo": "Satya Nadella"},
    "OKLO": {"name": "Oklo", "aliases": ["OKLO", "OKLO INC"], "ceo": "Jacob DeWitte"},
    "VST": {"name": "Vistra", "aliases": ["VST", "VISTRA"], "ceo": "Jim Burke"},
    "ORCL": {"name": "Oracle", "aliases": ["ORCL", "ORACLE", "LARRY ELLISON"], "ceo": "Safra Catz"},
    "BTC": {"name": "Bitcoin", "aliases": ["BTC", "BITCOIN", "IBIT"], "ceo": None},
}

def all_aliases_upper():
    # For fast matching
    out = {}
    for sym, meta in TRACKED.items():
        out[sym] = {a.upper() for a in meta["aliases"]}
    return out

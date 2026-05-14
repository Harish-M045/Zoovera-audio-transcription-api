import re
from typing import Tuple

_POS_WORDS = {
    "good", "great", "happy", "love", "excellent", "awesome", "nice", "positive", "best", "win", "success", "like"
}
_NEG_WORDS = {
    "bad", "sad", "terrible", "hate", "awful", "worst", "angry", "problem", "loss", "fail", "negative"
}

def _tokenize(text: str):
    return re.findall(r"\b\w+\b", (text or "").lower())

def sentiment_from_text(text: str) -> Tuple[float, str]:
    if not text or not text.strip():
        return 0.5, "neutral"

    tokens = _tokenize(text)
    pos = sum(1 for t in tokens if t in _POS_WORDS)
    neg = sum(1 for t in tokens if t in _NEG_WORDS)
    total = pos + neg

    if total == 0:
        if "!" in text and len(text) < 200:
            return 0.8, "positive"
        return 0.5, "neutral"

    ratio = (pos - neg) / total
    normalized = max(0.0, min(1.0, (ratio + 1.0) / 2.0))
    if normalized >= 0.6:
        label = "positive"
    elif normalized <= 0.4:
        label = "negative"
    else:
        label = "neutral"
    return round(normalized, 3), label

"""
src/validator/sentiment.py
VADER sentiment analysis wrapper for open-text tone scoring.
"""

from __future__ import annotations
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer: SentimentIntensityAnalyzer | None = None


def get_analyzer() -> SentimentIntensityAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def score_sentiment(text: str) -> dict[str, float]:
    """Return VADER polarity scores for a text string.

    Returns:
        dict with keys: neg, neu, pos, compound
    """
    return get_analyzer().polarity_scores(text)


def compound_score(text: str) -> float:
    """Return just the compound sentiment score (-1.0 to +1.0)."""
    return score_sentiment(text)["compound"]

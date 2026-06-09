"""
src/validator/coherence.py
Coherence validator. Combines VADER sentiment + rule engine to produce
a numeric coherence score per response.
"""

from __future__ import annotations
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .sentiment import compound_score
from .rules import ALL_RULES

if TYPE_CHECKING:
    from src.generator.pipeline import SurveyResponse

PENALTY_PER_VIOLATION = 0.35   # Each violation deducts 0.35; 1 violation → 0.65, 2 → 0.30

# Pre-compute which rules need the compound score argument (done once at import)
_RULES_NEED_COMPOUND: dict = {
    rule_fn: "compound" in inspect.signature(rule_fn).parameters
    for rule_fn in ALL_RULES
}


@dataclass
class CoherenceResult:
    score: float                       # 0.0 – 1.0
    is_coherent: bool                  # score >= threshold
    violations: list[str]              # List of violation codes
    sentiment_compound: float          # VADER compound score of Q5
    threshold: float = 0.6


def validate_coherence(
    response: "SurveyResponse",
    threshold: float = 0.6,
) -> CoherenceResult:
    """Run all coherence rules and compute a score.

    Args:
        response: The SurveyResponse to validate.
        threshold: Minimum score to be considered coherent.

    Returns:
        CoherenceResult with score, is_coherent flag, and violation list.
    """
    compound = compound_score(response.q5_open_text)
    violations: list[str] = []

    for rule_fn, needs_compound in _RULES_NEED_COMPOUND.items():
        violation = rule_fn(response, compound) if needs_compound else rule_fn(response)
        if violation:
            violations.append(violation)

    score = max(0.0, 1.0 - len(violations) * PENALTY_PER_VIOLATION)
    is_coherent = score >= threshold

    return CoherenceResult(
        score=round(score, 4),
        is_coherent=is_coherent,
        violations=violations,
        sentiment_compound=round(compound, 4),
        threshold=threshold,
    )

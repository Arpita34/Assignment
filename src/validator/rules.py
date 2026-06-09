"""
src/validator/rules.py
Coherence rule engine. All rules are pure-Python, no LLM calls.
Each rule returns a violation string or None.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.generator.pipeline import SurveyResponse


def rule_tone_mismatch_high_sat(response: "SurveyResponse", compound: float) -> str | None:
    """High satisfaction (4–5) should not have very negative text."""
    if response.q1_satisfaction >= 4 and compound < -0.05:
        return f"tone_mismatch:high_sat({response.q1_satisfaction})_negative_text(compound={compound:.2f})"
    return None


def rule_tone_mismatch_low_sat(response: "SurveyResponse", compound: float) -> str | None:
    """Low satisfaction (1–2) should not have positive text."""
    if response.q1_satisfaction <= 2 and compound > 0.05:
        return f"tone_mismatch:low_sat({response.q1_satisfaction})_positive_text(compound={compound:.2f})"
    return None


def rule_nps_sat_mismatch(response: "SurveyResponse") -> str | None:
    """NPS and satisfaction should be directionally aligned.

    Threshold: |nps_normalized - sat_normalized| > 0.4
    """
    nps_norm = response.q2_nps / 10.0
    sat_norm = (response.q1_satisfaction - 1) / 4.0
    divergence = abs(nps_norm - sat_norm)
    if divergence > 0.4:
        return (
            f"nps_sat_divergence:sat={response.q1_satisfaction},"
            f"nps={response.q2_nps},divergence={divergence:.2f}"
        )
    return None


def rule_promoter_low_sat(response: "SurveyResponse") -> str | None:
    """NPS promoter (9–10) with very low satisfaction (1–2) is incoherent."""
    if response.q2_nps >= 9 and response.q1_satisfaction <= 2:
        return f"promoter_low_sat:nps={response.q2_nps},sat={response.q1_satisfaction}"
    return None


def rule_detractor_high_sat(response: "SurveyResponse") -> str | None:
    """NPS detractor (0–3) with very high satisfaction (5) is incoherent."""
    if response.q2_nps <= 3 and response.q1_satisfaction == 5:
        return f"detractor_high_sat:nps={response.q2_nps},sat={response.q1_satisfaction}"
    return None


# Registry of all rules
ALL_RULES = [
    rule_tone_mismatch_high_sat,
    rule_tone_mismatch_low_sat,
    rule_nps_sat_mismatch,
    rule_promoter_low_sat,
    rule_detractor_high_sat,
]

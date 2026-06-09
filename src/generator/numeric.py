"""
src/generator/numeric.py
Deterministic NumPy-based sampling for Q1, Q2, Q3, Q4.
Zero LLM calls — all answers derived from behavior profile.
"""

from __future__ import annotations
import numpy as np
from src.profiler.correlation import BehaviorProfile
from src.personas.generator import Persona

CATEGORIES = ["Electronics", "Clothing", "Home", "Other"]


def sample_q1(profile: BehaviorProfile, rng: np.random.Generator) -> int:
    """Sample Q1 satisfaction (1–5) from the profile's sat_range."""
    lo, hi = profile.sat_range
    return int(rng.integers(lo, hi + 1))


def sample_q2(profile: BehaviorProfile, q1: int, rng: np.random.Generator) -> int:
    """Sample Q2 NPS (0–10) correlated with the sat_range and actual Q1 value.

    We use the profile NPS range but bias toward the actual Q1 to ensure
    high Pearson correlation between Q1 and Q2.
    """
    lo, hi = profile.nps_range
    # Bias the NPS toward the natural Q1 ratio
    q1_ratio = (q1 - 1) / 4.0          # 0.0 → 1.0
    nps_center = lo + q1_ratio * (hi - lo)
    # Add small noise
    nps_float = nps_center + rng.normal(0, 0.5)
    return int(np.clip(round(nps_float), lo, hi))


def sample_q3(persona: Persona, rng: np.random.Generator) -> str:
    """Use the persona's category preference (already sampled during persona gen)."""
    return persona.category_pref


def sample_q4(profile: BehaviorProfile) -> bool:
    """Q4 is already determined by the profiler (delivery_on_time)."""
    return profile.delivery_on_time


def sample_numeric_answers(
    persona: Persona,
    profile: BehaviorProfile,
    rng: np.random.Generator,
) -> dict:
    """Sample all deterministic answers (Q1–Q4) for a single response.

    Returns:
        dict with keys: q1_satisfaction, q2_nps, q3_category, q4_delivery_on_time
    """
    q1 = sample_q1(profile, rng)
    q2 = sample_q2(profile, q1, rng)
    q3 = sample_q3(persona, rng)
    q4 = sample_q4(profile)

    return {
        "q1_satisfaction": q1,
        "q2_nps": q2,
        "q3_category": q3,
        "q4_delivery_on_time": q4,
    }

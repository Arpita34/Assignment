"""
src/profiler/correlation.py
Pure-Python correlation rule engine. Maps each persona + delivery status
to expected answer ranges for Q1–Q4. Zero LLM calls in this module.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from loguru import logger

from src.personas.archetypes import ARCHETYPES, ArchetypeProfile


@dataclass
class BehaviorProfile:
    """The sampled behavior profile for a single response."""
    sat_range: tuple[int, int]        # Q1 (satisfaction 1–5)
    nps_range: tuple[int, int]        # Q2 (NPS 0–10)
    delivery_on_time: bool            # Q4
    q5_tone: str                      # Tone hint for LLM prompt
    q5_topics: list[str]              # Topic hints for LLM prompt
    archetype: str


# ─── Delivery rate per archetype ─────────────────────────────────────────────
# Controls what % of personas in this archetype experience late delivery
DELIVERY_LATE_RATE: dict[str, float] = {
    "happy_customer":        0.15,   # 15% get late delivery
    "neutral_passive":       0.30,
    "frustrated_detractor":  0.50,   # More likely to have had bad experience
    "delivery_focused":      0.40,
    "value_seeker":          0.20,
}

# Tone overrides when delivery is late
LATE_TONE_MAP: dict[str, str] = {
    "happy_customer":        "mixed_delay",
    "neutral_passive":       "mildly_negative",
    "frustrated_detractor":  "very_negative",
    "delivery_focused":      "delivery_negative",
    "value_seeker":          "price_quality_negative",
}

# Topic additions for late delivery
LATE_TOPIC_ADDITIONS: list[str] = ["delivery delay", "late shipment", "tracking issues"]


def get_behavior_profile(
    archetype_name: str,
    late_delivery: bool,
    rng: np.random.Generator | None = None,
) -> BehaviorProfile:
    """Compute behavior profile for a persona.

    Args:
        archetype_name: One of the 5 archetype keys.
        late_delivery: Whether delivery was late for this persona.
        rng: Optional numpy random generator for reproducibility.

    Returns:
        BehaviorProfile with sampled answer ranges.
    """
    if rng is None:
        rng = np.random.default_rng()

    profile: ArchetypeProfile = ARCHETYPES[archetype_name]

    sat_min, sat_max = profile.sat_range
    nps_min, nps_max = profile.nps_range
    tone = profile.q5_tone
    topics = list(profile.q5_topics)

    if late_delivery:
        # Apply penalties (clamped to valid ranges)
        pen_sat_min, pen_sat_max = profile.late_sat_penalty
        pen_nps_min, pen_nps_max = profile.late_nps_penalty

        sat_min = max(1, sat_min + pen_sat_min)
        sat_max = max(sat_min, sat_max + pen_sat_max)
        nps_min = max(0, nps_min + pen_nps_min)
        nps_max = max(nps_min, nps_max + pen_nps_max)

        tone = LATE_TONE_MAP.get(archetype_name, "mildly_negative")
        topics = topics + LATE_TOPIC_ADDITIONS

    return BehaviorProfile(
        sat_range=(sat_min, sat_max),
        nps_range=(nps_min, nps_max),
        delivery_on_time=not late_delivery,
        q5_tone=tone,
        q5_topics=topics[:6],         # Cap topics list
        archetype=archetype_name,
    )


def sample_delivery(archetype_name: str, rng: np.random.Generator) -> bool:
    """Sample whether delivery was late for a given archetype."""
    late_rate = DELIVERY_LATE_RATE.get(archetype_name, 0.25)
    return bool(rng.random() < late_rate)

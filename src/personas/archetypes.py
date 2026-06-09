"""
src/personas/archetypes.py
Five persona archetypes with weighted distributions and behavioral profiles.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ArchetypeProfile:
    name: str
    weight: float                    # Proportion of total responses
    sat_range: tuple[int, int]       # Q1 satisfaction range
    nps_range: tuple[int, int]       # Q2 NPS range
    delivery_sensitivity: float      # 0.0 (low) – 1.0 (very high)
    q5_tone: str                     # Primary tone for open text
    q5_topics: list[str]             # Likely topics in feedback
    description: str = ""

    # Delivery penalty: how much late delivery shifts sat/nps down
    late_sat_penalty: tuple[int, int] = (0, 0)   # (min_shift, max_shift)
    late_nps_penalty: tuple[int, int] = (0, 0)


# ─── Archetype Definitions ──────────────────────────────────────────────────

ARCHETYPES: dict[str, ArchetypeProfile] = {
    "happy_customer": ArchetypeProfile(
        name="happy_customer",
        weight=0.30,
        sat_range=(4, 5),
        nps_range=(8, 10),
        delivery_sensitivity=0.2,
        q5_tone="positive",
        q5_topics=["quality", "experience", "minor suggestions", "praise"],
        late_sat_penalty=(-1, -2),
        late_nps_penalty=(-1, -3),
        description="Overall satisfied; delivery issues reduce NPS but stay positive",
    ),
    "neutral_passive": ArchetypeProfile(
        name="neutral_passive",
        weight=0.25,
        sat_range=(3, 3),
        nps_range=(6, 7),
        delivery_sensitivity=0.5,
        q5_tone="neutral",
        q5_topics=["mild suggestions", "price", "website UX", "packaging"],
        late_sat_penalty=(-1, -1),
        late_nps_penalty=(-1, -2),
        description="Middle-of-the-road; small delivery impact",
    ),
    "frustrated_detractor": ArchetypeProfile(
        name="frustrated_detractor",
        weight=0.20,
        sat_range=(1, 2),
        nps_range=(0, 3),
        delivery_sensitivity=0.8,
        q5_tone="negative",
        q5_topics=["product quality", "customer service", "return policy", "damage"],
        late_sat_penalty=(-1, -1),   # Already at floor, clamped
        late_nps_penalty=(-1, -2),
        description="Dissatisfied; very negative feedback regardless of delivery",
    ),
    "delivery_focused": ArchetypeProfile(
        name="delivery_focused",
        weight=0.15,
        sat_range=(4, 5),            # Good when on-time; adjusted in profiler
        nps_range=(7, 9),
        delivery_sensitivity=1.0,
        q5_tone="delivery_positive",
        q5_topics=["delivery speed", "packaging", "tracking", "courier"],
        late_sat_penalty=(-3, -3),   # Hard drop when late
        late_nps_penalty=(-5, -6),
        description="Satisfaction almost entirely driven by delivery outcome",
    ),
    "value_seeker": ArchetypeProfile(
        name="value_seeker",
        weight=0.10,
        sat_range=(3, 4),
        nps_range=(5, 7),
        delivery_sensitivity=0.3,
        q5_tone="price_quality",
        q5_topics=["pricing", "value for money", "discounts", "alternatives"],
        late_sat_penalty=(-1, -1),
        late_nps_penalty=(-1, -2),
        description="Focused on price/quality ratio; moderate delivery sensitivity",
    ),
}


def get_archetype(name: str) -> ArchetypeProfile:
    """Return an archetype profile by name."""
    if name not in ARCHETYPES:
        raise KeyError(f"Unknown archetype: '{name}'. Valid: {list(ARCHETYPES)}")
    return ARCHETYPES[name]


def archetype_names() -> list[str]:
    return list(ARCHETYPES.keys())


def archetype_weights() -> list[float]:
    return [a.weight for a in ARCHETYPES.values()]

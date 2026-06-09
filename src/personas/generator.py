"""
src/personas/generator.py
Generate N personas using Faker for demographics and archetype weights.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
import numpy as np
from faker import Faker
from loguru import logger

from .archetypes import ARCHETYPES, archetype_names, archetype_weights

fake = Faker()
Faker.seed(42)

PRODUCT_CATEGORIES = ["Electronics", "Clothing", "Home", "Other"]
# Category preferences vary by archetype
CATEGORY_WEIGHTS: dict[str, list[float]] = {
    "happy_customer":        [0.30, 0.30, 0.25, 0.15],
    "neutral_passive":       [0.25, 0.35, 0.25, 0.15],
    "frustrated_detractor":  [0.35, 0.25, 0.25, 0.15],
    "delivery_focused":      [0.35, 0.25, 0.25, 0.15],
    "value_seeker":          [0.20, 0.30, 0.25, 0.25],
}


@dataclass
class Persona:
    id: str
    archetype: str
    age: int
    region: str
    city: str
    category_pref: str
    delivery_sensitivity: float
    tone_tendency: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def generate_personas(n: int, seed: int = 42) -> list[Persona]:
    """Generate N personas using Faker demographics + archetype weighting.

    Args:
        n: Number of personas to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of Persona instances.
    """
    rng = np.random.default_rng(seed)
    Faker.seed(seed)

    names = archetype_names()
    weights = archetype_weights()

    # Sample archetypes according to weights
    chosen_archetypes = rng.choice(names, size=n, p=weights).tolist()

    personas: list[Persona] = []
    for archetype_name in chosen_archetypes:
        profile = ARCHETYPES[archetype_name]

        cat_weights = CATEGORY_WEIGHTS[archetype_name]
        category = rng.choice(PRODUCT_CATEGORIES, p=cat_weights)

        # Jitter delivery sensitivity slightly per person
        sensitivity = float(
            np.clip(
                profile.delivery_sensitivity + rng.normal(0, 0.1),
                0.0,
                1.0,
            )
        )

        persona = Persona(
            id=str(uuid.uuid4()),
            archetype=archetype_name,
            age=int(rng.integers(18, 71)),
            region=fake.state(),
            city=fake.city(),
            category_pref=str(category),
            delivery_sensitivity=round(sensitivity, 3),
            tone_tendency=profile.q5_tone,
        )
        personas.append(persona)

    logger.info(f"Generated {len(personas)} personas.")
    _log_archetype_distribution(personas)
    return personas


def _log_archetype_distribution(personas: list[Persona]) -> None:
    from collections import Counter
    counts = Counter(p.archetype for p in personas)
    total = len(personas)
    for name, count in sorted(counts.items()):
        pct = count / total * 100
        logger.debug(f"  {name:25s}: {count:4d}  ({pct:.1f}%)")

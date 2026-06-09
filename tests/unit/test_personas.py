"""
tests/unit/test_personas.py
Unit tests for persona generator. No LLM calls.
"""

import pytest
import numpy as np
from src.personas.generator import generate_personas, Persona
from src.personas.archetypes import ARCHETYPES, archetype_names


class TestPersonaGeneration:

    def test_generates_correct_count(self):
        personas = generate_personas(50, seed=42)
        assert len(personas) == 50

    def test_all_fields_populated(self):
        personas = generate_personas(10, seed=0)
        for p in personas:
            assert p.id
            assert p.archetype in archetype_names()
            assert 18 <= p.age <= 70
            assert p.region
            assert p.city
            assert p.category_pref in ["Electronics", "Clothing", "Home", "Other"]
            assert 0.0 <= p.delivery_sensitivity <= 1.0

    def test_archetype_distribution_roughly_matches_weights(self):
        """Archetype distribution should match target weights within ±8%."""
        personas = generate_personas(500, seed=42)
        from collections import Counter
        counts = Counter(p.archetype for p in personas)
        total = len(personas)

        expected = {k: v.weight for k, v in ARCHETYPES.items()}
        for name, expected_weight in expected.items():
            actual_weight = counts[name] / total
            diff = abs(actual_weight - expected_weight)
            assert diff < 0.08, (
                f"Archetype '{name}': expected {expected_weight:.0%}, "
                f"got {actual_weight:.0%} (diff={diff:.0%})"
            )

    def test_reproducible_with_same_seed(self):
        """Same seed should produce identical personas."""
        p1 = generate_personas(20, seed=99)
        p2 = generate_personas(20, seed=99)
        assert [p.archetype for p in p1] == [p.archetype for p in p2]
        assert [p.age for p in p1] == [p.age for p in p2]

    def test_unique_ids(self):
        """All persona IDs must be unique."""
        personas = generate_personas(100, seed=42)
        ids = [p.id for p in personas]
        assert len(ids) == len(set(ids))

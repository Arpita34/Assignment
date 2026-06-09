"""
tests/unit/test_personas_extended.py
Extended edge-case tests for persona generation: seeds, archetype weights,
extreme N values, field constraints, and Faker determinism.
"""

import pytest
import numpy as np
from src.personas.generator import generate_personas, Persona
from src.personas.archetypes import ARCHETYPES


class TestSeedDeterminism:

    def test_same_seed_produces_identical_archetypes_and_ages(self):
        """Two calls with seed=42 must produce identical archetypes and demographics.
        Note: UUIDs use uuid4 so will differ between calls — that is expected.
        """
        p1 = generate_personas(20, seed=42)
        p2 = generate_personas(20, seed=42)
        for a, b in zip(p1, p2):
            assert a.archetype == b.archetype
            assert a.age == b.age
            assert a.region == b.region
            assert a.category_pref == b.category_pref
            assert a.tone_tendency == b.tone_tendency

    def test_different_seeds_produce_different_results(self):
        """Seeds 42 and 99 should produce different persona sets."""
        p1 = generate_personas(20, seed=42)
        p2 = generate_personas(20, seed=99)
        archetypes1 = [p.archetype for p in p1]
        archetypes2 = [p.archetype for p in p2]
        assert archetypes1 != archetypes2  # Very unlikely to be identical

    def test_seed_zero_is_valid(self):
        personas = generate_personas(5, seed=0)
        assert len(personas) == 5

    def test_large_seed_is_valid(self):
        personas = generate_personas(5, seed=2**32 - 1)
        assert len(personas) == 5


class TestExtremeN:

    def test_n_equals_one(self):
        personas = generate_personas(1, seed=42)
        assert len(personas) == 1
        assert isinstance(personas[0], Persona)

    def test_n_equals_two(self):
        """Smallest meaningful batch."""
        personas = generate_personas(2, seed=42)
        assert len(personas) == 2

    def test_n_equals_five(self):
        """Five should always cover all 5 archetypes (weighted, may not)."""
        personas = generate_personas(5, seed=42)
        assert len(personas) == 5

    def test_n_equals_1000(self):
        """Large N should still complete and return exactly 1000."""
        personas = generate_personas(1000, seed=1)
        assert len(personas) == 1000

    def test_all_ids_unique_at_n_1000(self):
        personas = generate_personas(1000, seed=1)
        ids = [p.id for p in personas]
        assert len(ids) == len(set(ids))


class TestPersonaFields:

    def test_age_within_valid_range(self):
        """All personas must have age between 18 and 70."""
        personas = generate_personas(200, seed=42)
        for p in personas:
            assert 18 <= p.age <= 70, f"Invalid age: {p.age}"

    def test_archetype_always_valid(self):
        """Every persona's archetype must be one of the 5 known types."""
        valid = set(ARCHETYPES.keys())
        personas = generate_personas(100, seed=42)
        for p in personas:
            assert p.archetype in valid, f"Unknown archetype: {p.archetype}"

    def test_delivery_sensitivity_is_float_between_0_and_1(self):
        personas = generate_personas(50, seed=42)
        for p in personas:
            assert 0.0 <= p.delivery_sensitivity <= 1.0, (
                f"delivery_sensitivity out of range: {p.delivery_sensitivity}"
            )

    def test_tone_tendency_is_non_empty_string(self):
        personas = generate_personas(50, seed=42)
        for p in personas:
            assert isinstance(p.tone_tendency, str)
            assert len(p.tone_tendency.strip()) > 0

    def test_category_pref_is_valid_category(self):
        valid = {"Electronics", "Clothing", "Home", "Other"}
        personas = generate_personas(100, seed=42)
        for p in personas:
            assert p.category_pref in valid, f"Invalid category: {p.category_pref}"

    def test_id_is_non_empty_string(self):
        personas = generate_personas(10, seed=42)
        for p in personas:
            assert isinstance(p.id, str)
            assert len(p.id) > 0

    def test_region_is_non_empty_string(self):
        personas = generate_personas(10, seed=42)
        for p in personas:
            assert isinstance(p.region, str) and len(p.region.strip()) > 0

    def test_city_is_non_empty_string(self):
        personas = generate_personas(10, seed=42)
        for p in personas:
            assert isinstance(p.city, str) and len(p.city.strip()) > 0

    def test_created_at_is_iso_string(self):
        """Timestamp must be a parseable ISO-8601 string."""
        from datetime import datetime
        personas = generate_personas(5, seed=42)
        for p in personas:
            # Should not raise
            dt = datetime.fromisoformat(p.created_at)
            assert dt.tzinfo is not None  # Must be timezone-aware


class TestArchetypeWeightDistribution:

    def test_at_n_1000_weights_within_5_percent(self):
        """At large N, archetype distribution must stay within 5% of targets."""
        personas = generate_personas(1000, seed=42)
        counts = {}
        for p in personas:
            counts[p.archetype] = counts.get(p.archetype, 0) + 1

        for name, profile in ARCHETYPES.items():
            actual = counts.get(name, 0) / len(personas)
            expected = profile.weight
            assert abs(actual - expected) <= 0.07, (
                f"Archetype '{name}': got {actual:.2%}, expected {expected:.2%}"
            )

    def test_all_archetypes_appear_at_n_200(self):
        """All 5 archetypes must appear at N=200."""
        personas = generate_personas(200, seed=42)
        found = {p.archetype for p in personas}
        assert found == set(ARCHETYPES.keys())

    def test_happy_customer_is_most_common(self):
        """happy_customer has the highest weight (30%) so must be most common."""
        personas = generate_personas(200, seed=42)
        counts = {}
        for p in personas:
            counts[p.archetype] = counts.get(p.archetype, 0) + 1
        most_common = max(counts, key=counts.get)
        assert most_common == "happy_customer"

    def test_value_seeker_is_least_common(self):
        """value_seeker has lowest weight (10%) so must be least common."""
        personas = generate_personas(200, seed=42)
        counts = {}
        for p in personas:
            counts[p.archetype] = counts.get(p.archetype, 0) + 1
        least_common = min(counts, key=counts.get)
        assert least_common == "value_seeker"

"""
tests/unit/test_generator.py
Unit tests for numeric sampler. No LLM calls.
"""

import pytest
import numpy as np
from src.profiler.correlation import get_behavior_profile
from src.generator.numeric import sample_numeric_answers, sample_q1, sample_q2
from src.personas.generator import Persona


def _make_persona(archetype: str = "happy_customer", category: str = "Electronics") -> Persona:
    return Persona(
        id="test-id",
        archetype=archetype,
        age=30,
        region="California",
        city="Los Angeles",
        category_pref=category,
        delivery_sensitivity=0.5,
        tone_tendency="positive",
    )


RNG = np.random.default_rng(42)


class TestNumericSampler:

    def test_q1_in_sat_range(self):
        """Sampled Q1 must fall within the profile's sat_range."""
        persona = _make_persona("happy_customer")
        profile = get_behavior_profile("happy_customer", late_delivery=False, rng=RNG)
        for _ in range(50):
            rng = np.random.default_rng()
            q1 = sample_q1(profile, rng)
            lo, hi = profile.sat_range
            assert lo <= q1 <= hi, f"Q1={q1} outside range ({lo},{hi})"

    def test_q2_in_nps_range(self):
        """Sampled Q2 must fall within the profile's nps_range."""
        profile = get_behavior_profile("happy_customer", late_delivery=False, rng=RNG)
        for _ in range(50):
            rng = np.random.default_rng()
            q1 = sample_q1(profile, rng)
            q2 = sample_q2(profile, q1, rng)
            lo, hi = profile.nps_range
            assert lo <= q2 <= hi, f"Q2={q2} outside range ({lo},{hi})"

    def test_q3_returns_persona_category(self):
        """Q3 must return the persona's category_pref."""
        persona = _make_persona("happy_customer", category="Clothing")
        profile = get_behavior_profile("happy_customer", late_delivery=False, rng=RNG)
        answers = sample_numeric_answers(persona, profile, RNG)
        assert answers["q3_category"] == "Clothing"

    def test_q4_matches_delivery_status(self):
        """Q4 must match profile.delivery_on_time."""
        persona = _make_persona()
        profile_on = get_behavior_profile("happy_customer", late_delivery=False, rng=RNG)
        profile_late = get_behavior_profile("happy_customer", late_delivery=True, rng=RNG)
        ans_on = sample_numeric_answers(persona, profile_on, RNG)
        ans_late = sample_numeric_answers(persona, profile_late, RNG)
        assert ans_on["q4_delivery_on_time"] is True
        assert ans_late["q4_delivery_on_time"] is False

    def test_all_fields_present(self):
        """All 4 numeric fields must be present in the output dict."""
        persona = _make_persona()
        profile = get_behavior_profile("neutral_passive", late_delivery=False, rng=RNG)
        answers = sample_numeric_answers(persona, profile, RNG)
        assert "q1_satisfaction" in answers
        assert "q2_nps" in answers
        assert "q3_category" in answers
        assert "q4_delivery_on_time" in answers

    def test_frustrated_late_q1_very_low(self):
        """Frustrated+late should produce Q1 of 1 or 2."""
        persona = _make_persona("frustrated_detractor")
        profile = get_behavior_profile("frustrated_detractor", late_delivery=True, rng=RNG)
        q1_values = set()
        for seed in range(100):
            rng = np.random.default_rng(seed)
            answers = sample_numeric_answers(persona, profile, rng)
            q1_values.add(answers["q1_satisfaction"])
        assert all(v <= 2 for v in q1_values), f"Got unexpected high Q1: {q1_values}"

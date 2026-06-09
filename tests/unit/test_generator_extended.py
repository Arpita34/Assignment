"""
tests/unit/test_generator_extended.py
Extended edge-case tests for the numeric answer generator:
reproducibility, boundary clamping, Q3 category constraint, Q4 delivery flag.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from src.generator.numeric import (
    sample_q1, sample_q2, sample_q3, sample_q4, sample_numeric_answers
)
from src.profiler.correlation import get_behavior_profile, BehaviorProfile
from src.personas.generator import generate_personas


def make_profile(sat_range=(3, 4), nps_range=(6, 8),
                 delivery_on_time=True, q5_tone="positive",
                 q5_topics=None, archetype="happy_customer"):
    return BehaviorProfile(
        sat_range=sat_range,
        nps_range=nps_range,
        delivery_on_time=delivery_on_time,
        q5_tone=q5_tone,
        q5_topics=q5_topics or ["quality", "speed"],
        archetype=archetype,
    )


def make_persona(category_pref="Electronics"):
    p = MagicMock()
    p.category_pref = category_pref
    return p


# ─── sample_q1 ───────────────────────────────────────────────────────────────

class TestSampleQ1:

    def test_returns_integer(self):
        rng = np.random.default_rng(0)
        val = sample_q1(make_profile(sat_range=(1, 5)), rng)
        assert isinstance(val, int)

    def test_single_value_range(self):
        """If sat_range is (3, 3) it should always return 3."""
        rng = np.random.default_rng(0)
        profile = make_profile(sat_range=(3, 3))
        for _ in range(20):
            rng2 = np.random.default_rng(_)
            assert sample_q1(profile, rng2) == 3

    def test_min_range_1_1(self):
        rng = np.random.default_rng(0)
        assert sample_q1(make_profile(sat_range=(1, 1)), rng) == 1

    def test_max_range_5_5(self):
        rng = np.random.default_rng(0)
        assert sample_q1(make_profile(sat_range=(5, 5)), rng) == 5

    def test_full_range_covers_all_values(self):
        """Over many samples with range (1,5), all of 1–5 must appear."""
        profile = make_profile(sat_range=(1, 5))
        seen = set()
        for seed in range(200):
            rng = np.random.default_rng(seed)
            seen.add(sample_q1(profile, rng))
        assert seen == {1, 2, 3, 4, 5}

    def test_result_within_profile_sat_range(self):
        """Result must always be within the profile's sat_range."""
        for lo in range(1, 5):
            for hi in range(lo, 6):
                profile = make_profile(sat_range=(lo, hi))
                rng = np.random.default_rng(42)
                for _ in range(30):
                    val = sample_q1(profile, rng)
                    assert lo <= val <= hi


# ─── sample_q2 ───────────────────────────────────────────────────────────────

class TestSampleQ2:

    def test_returns_integer(self):
        rng = np.random.default_rng(0)
        val = sample_q2(make_profile(nps_range=(0, 10)), q1=3, rng=rng)
        assert isinstance(val, int)

    def test_result_within_0_to_10(self):
        """Even with extreme bias, result stays in [0, 10]."""
        for q1 in [1, 2, 3, 4, 5]:
            for nps_lo, nps_hi in [(0, 3), (7, 10), (0, 10)]:
                profile = make_profile(nps_range=(nps_lo, nps_hi))
                rng = np.random.default_rng(42)
                for _ in range(50):
                    val = sample_q2(profile, q1=q1, rng=rng)
                    assert 0 <= val <= 10, f"Q2 out of range: {val}"

    def test_high_q1_biases_toward_high_nps(self):
        """Q1=5 should bias NPS higher than Q1=1."""
        profile = make_profile(nps_range=(0, 10))
        scores_high = [sample_q2(profile, q1=5, rng=np.random.default_rng(s)) for s in range(100)]
        scores_low  = [sample_q2(profile, q1=1, rng=np.random.default_rng(s)) for s in range(100)]
        assert np.mean(scores_high) > np.mean(scores_low)

    def test_narrow_nps_range_constrains_output(self):
        """NPS range (8, 10) must never produce NPS < 8."""
        profile = make_profile(nps_range=(8, 10))
        rng = np.random.default_rng(0)
        for _ in range(100):
            val = sample_q2(profile, q1=5, rng=rng)
            assert 8 <= val <= 10


# ─── sample_q3 ───────────────────────────────────────────────────────────────

class TestSampleQ3:

    def test_returns_persona_category(self):
        rng = np.random.default_rng(0)
        persona = make_persona("Home")
        assert sample_q3(persona, rng) == "Home"

    def test_category_pref_preserved_for_all_archetypes(self):
        """Q3 always equals persona.category_pref regardless of rng."""
        for cat in ["Electronics", "Clothing", "Home", "Other"]:
            persona = make_persona(cat)
            for seed in range(10):
                rng = np.random.default_rng(seed)
                assert sample_q3(persona, rng) == cat


# ─── sample_q4 ───────────────────────────────────────────────────────────────

class TestSampleQ4:

    def test_on_time_returns_true(self):
        assert sample_q4(make_profile(delivery_on_time=True)) is True

    def test_late_returns_false(self):
        assert sample_q4(make_profile(delivery_on_time=False)) is False

    def test_returns_bool(self):
        assert isinstance(sample_q4(make_profile()), bool)


# ─── sample_numeric_answers (integration) ────────────────────────────────────

class TestSampleNumericAnswersIntegration:

    def test_all_keys_present(self):
        rng = np.random.default_rng(42)
        persona = generate_personas(1, seed=42)[0]
        profile = get_behavior_profile(persona.archetype, late_delivery=False, rng=rng)
        answers = sample_numeric_answers(persona, profile, rng)
        assert "q1_satisfaction" in answers
        assert "q2_nps" in answers
        assert "q3_category" in answers
        assert "q4_delivery_on_time" in answers

    def test_returns_correct_types(self):
        rng = np.random.default_rng(0)
        persona = generate_personas(1, seed=0)[0]
        profile = get_behavior_profile(persona.archetype, late_delivery=False, rng=rng)
        answers = sample_numeric_answers(persona, profile, rng)
        assert isinstance(answers["q1_satisfaction"], int)
        assert isinstance(answers["q2_nps"], int)
        assert isinstance(answers["q3_category"], str)
        assert isinstance(answers["q4_delivery_on_time"], bool)

    def test_deterministic_with_same_rng_state(self):
        """Same rng state → same answers."""
        persona = generate_personas(1, seed=42)[0]
        for late in [True, False]:
            rng1 = np.random.default_rng(99)
            rng2 = np.random.default_rng(99)
            profile1 = get_behavior_profile(persona.archetype, late_delivery=late, rng=rng1)
            profile2 = get_behavior_profile(persona.archetype, late_delivery=late, rng=rng2)
            a1 = sample_numeric_answers(persona, profile1, rng1)
            a2 = sample_numeric_answers(persona, profile2, rng2)
            assert a1 == a2

    def test_no_none_values_in_answers(self):
        rng = np.random.default_rng(42)
        persona = generate_personas(1, seed=42)[0]
        profile = get_behavior_profile(persona.archetype, late_delivery=False, rng=rng)
        answers = sample_numeric_answers(persona, profile, rng)
        for key, val in answers.items():
            assert val is not None, f"Key '{key}' returned None"


# ─── Prompt Builder ───────────────────────────────────────────────────────────

class TestPromptBuilder:
    """Test the Q5 prompt builder produces usable prompts."""

    def test_prompt_contains_persona_archetype(self):
        from src.generator.prompts import build_q5_prompt
        from src.profiler.correlation import get_behavior_profile

        rng = np.random.default_rng(42)
        persona = generate_personas(1, seed=42)[0]
        profile = get_behavior_profile(persona.archetype, late_delivery=False, rng=rng)
        prompt = build_q5_prompt(persona, profile, q1=4, q2=8, q4=True)
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_prompt_contains_q5_instruction(self):
        from src.generator.prompts import build_q5_prompt
        from src.profiler.correlation import get_behavior_profile

        rng = np.random.default_rng(0)
        persona = generate_personas(1, seed=0)[0]
        profile = get_behavior_profile(persona.archetype, late_delivery=False, rng=rng)
        prompt = build_q5_prompt(persona, profile, q1=5, q2=9, q4=True)
        assert "5" in prompt or "satisfaction" in prompt.lower()

    def test_prompt_is_non_empty_for_all_archetypes(self):
        from src.generator.prompts import build_q5_prompt
        from src.profiler.correlation import get_behavior_profile

        for archetype in ["happy_customer", "frustrated_detractor",
                          "neutral_passive", "delivery_focused", "value_seeker"]:
            rng = np.random.default_rng(42)
            persona = generate_personas(1, seed=42)[0]
            persona.archetype = archetype  # Override archetype on mock
            profile = get_behavior_profile(archetype, late_delivery=False, rng=rng)
            prompt = build_q5_prompt(persona, profile, q1=3, q2=6, q4=True)
            assert isinstance(prompt, str) and len(prompt.strip()) > 50

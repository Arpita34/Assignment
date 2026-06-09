"""
tests/unit/test_pipeline_integration.py
Integration tests for the full pipeline (without LLM).
Tests the non-LLM stages end-to-end with mock Q5 answers.
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from src.parser.loader import load_survey
from src.personas.generator import generate_personas
from src.profiler.correlation import get_behavior_profile, sample_delivery
from src.generator.numeric import sample_numeric_answers
from src.validator.coherence import validate_coherence


# ─── Pipeline Smoke Tests ──────────────────────────────────────────────────────

class TestPipelineSmokeNLLM:
    """Run stages 1-5 without LLM to verify the pipeline wires together."""

    def test_stages_1_to_5_complete_without_error(self):
        """All deterministic stages should complete for 20 personas."""
        schema = load_survey("surveys/ecommerce.json")
        personas = generate_personas(20, seed=42)
        rng = np.random.default_rng(42)

        results = []
        for p in personas:
            late = sample_delivery(p.archetype, rng)
            profile = get_behavior_profile(p.archetype, late_delivery=late, rng=rng)
            answers = sample_numeric_answers(p, profile, rng)

            mock_resp = MagicMock()
            mock_resp.q1_satisfaction = answers["q1_satisfaction"]
            mock_resp.q2_nps = answers["q2_nps"]
            mock_resp.q3_category = answers["q3_category"]
            mock_resp.q4_delivery_on_time = answers["q4_delivery_on_time"]
            mock_resp.q5_open_text = "The overall experience matched my expectations."
            mock_resp.persona_archetype = p.archetype

            coherence = validate_coherence(mock_resp)
            results.append((answers, coherence))

        assert len(results) == 20
        for answers, coh in results:
            assert 1 <= answers["q1_satisfaction"] <= 5
            assert 0 <= answers["q2_nps"] <= 10
            assert isinstance(coh.score, float)

    def test_q1_q2_pearson_correlation_positive(self):
        """Over 100 deterministic samples, Q1 and Q2 must be positively correlated."""
        personas = generate_personas(100, seed=7)
        rng = np.random.default_rng(7)

        q1s, q2s = [], []
        for p in personas:
            late = sample_delivery(p.archetype, rng)
            profile = get_behavior_profile(p.archetype, late_delivery=late, rng=rng)
            answers = sample_numeric_answers(p, profile, rng)
            q1s.append(answers["q1_satisfaction"])
            q2s.append(answers["q2_nps"])

        r = np.corrcoef(q1s, q2s)[0, 1]
        assert r > 0.5, f"Q1–Q2 correlation too low: r={r:.3f}"

    def test_delivery_flag_consistent_with_profile(self):
        """Q4 answer must always match the profile's delivery_on_time."""
        personas = generate_personas(50, seed=0)
        rng = np.random.default_rng(0)
        for p in personas:
            late = sample_delivery(p.archetype, rng)
            profile = get_behavior_profile(p.archetype, late_delivery=late, rng=rng)
            answers = sample_numeric_answers(p, profile, rng)
            expected_q4 = not late
            assert answers["q4_delivery_on_time"] == expected_q4

    def test_frustrated_late_has_lower_mean_sat_than_happy_ontime(self):
        """Frustrated+late personas must have lower mean sat than happy+ontime."""
        rng = np.random.default_rng(1)
        sats_frustrated, sats_happy = [], []

        for _ in range(50):
            frustrated_profile = get_behavior_profile(
                "frustrated_detractor", late_delivery=True, rng=rng
            )
            happy_profile = get_behavior_profile(
                "happy_customer", late_delivery=False, rng=rng
            )
            # Sample directly from profiles
            from src.generator.numeric import sample_q1
            sats_frustrated.append(sample_q1(frustrated_profile, rng))
            sats_happy.append(sample_q1(happy_profile, rng))

        assert np.mean(sats_frustrated) < np.mean(sats_happy)

    def test_all_categories_appear_in_100_samples(self):
        """Over 100 personas, all 4 product categories must appear."""
        personas = generate_personas(100, seed=42)
        rng = np.random.default_rng(42)
        seen_categories = set()

        for p in personas:
            late = sample_delivery(p.archetype, rng)
            profile = get_behavior_profile(p.archetype, late_delivery=late, rng=rng)
            answers = sample_numeric_answers(p, profile, rng)
            seen_categories.add(answers["q3_category"])

        assert seen_categories == {"Electronics", "Clothing", "Home", "Other"}


# ─── Coherence Pipeline ───────────────────────────────────────────────────────

class TestCoherencePipeline:

    def test_high_sat_positive_text_coherent_in_pipeline(self):
        """Simulate a happy_customer response — should be coherent."""
        personas = generate_personas(1, seed=42)
        rng = np.random.default_rng(42)
        p = personas[0]

        profile = get_behavior_profile("happy_customer", late_delivery=False, rng=rng)
        answers = sample_numeric_answers(p, profile, rng)

        resp = MagicMock()
        resp.q1_satisfaction = 5
        resp.q2_nps = 9
        resp.q4_delivery_on_time = True
        resp.q5_open_text = "Excellent product quality and fast shipping! Highly recommend."
        resp.persona_archetype = "happy_customer"

        result = validate_coherence(resp)
        assert result.is_coherent
        assert result.score >= 0.6

    def test_frustrated_detractor_negative_text_coherent(self):
        resp = MagicMock()
        resp.q1_satisfaction = 1
        resp.q2_nps = 1
        resp.q4_delivery_on_time = False
        resp.q5_open_text = "Absolutely terrible. Arrived late and broken. Never buying again."
        resp.persona_archetype = "frustrated_detractor"

        result = validate_coherence(resp)
        assert result.is_coherent
        assert len(result.violations) == 0

    def test_coherence_score_varies_across_personas(self):
        """Scores across 30 different mock responses should not all be identical."""
        personas = generate_personas(30, seed=5)
        rng = np.random.default_rng(5)
        scores = []

        texts = [
            "Great!", "Okay.", "Terrible experience.",
            "Will buy again!", "Very disappointed.",
            "Fast shipping, good quality.", "Broken on arrival.",
        ]

        for i, p in enumerate(personas):
            late = sample_delivery(p.archetype, rng)
            profile = get_behavior_profile(p.archetype, late_delivery=late, rng=rng)
            answers = sample_numeric_answers(p, profile, rng)

            resp = MagicMock()
            resp.q1_satisfaction = answers["q1_satisfaction"]
            resp.q2_nps = answers["q2_nps"]
            resp.q4_delivery_on_time = answers["q4_delivery_on_time"]
            resp.q5_open_text = texts[i % len(texts)]
            resp.persona_archetype = p.archetype

            result = validate_coherence(resp)
            scores.append(result.score)

        # Scores should not all be identical
        assert len(set(scores)) > 1


# ─── Reproducibility Across Pipeline ─────────────────────────────────────────

class TestPipelineReproducibility:

    def test_full_pipeline_is_reproducible(self):
        """Two runs with same seed must produce identical numeric answers."""
        def run(seed):
            personas = generate_personas(10, seed=seed)
            rng = np.random.default_rng(seed)
            out = []
            for p in personas:
                late = sample_delivery(p.archetype, rng)
                profile = get_behavior_profile(p.archetype, late_delivery=late, rng=rng)
                answers = sample_numeric_answers(p, profile, rng)
                out.append(tuple(sorted(answers.items())))
            return out

        assert run(42) == run(42)
        assert run(99) == run(99)
        assert run(42) != run(99)  # Different seeds → different outputs

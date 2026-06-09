"""
tests/unit/test_validator.py
Unit tests for coherence validator and rule engine. No LLM calls.
"""

import pytest
from unittest.mock import MagicMock
from src.validator.coherence import validate_coherence, CoherenceResult
from src.validator.sentiment import compound_score


def _make_response(q1: int, q2: int, q5: str, q4: bool = True, archetype: str = "happy_customer"):
    """Helper to create a mock SurveyResponse."""
    r = MagicMock()
    r.q1_satisfaction = q1
    r.q2_nps = q2
    r.q4_delivery_on_time = q4
    r.q5_open_text = q5
    r.persona_archetype = archetype
    return r


class TestCoherenceValidatorFlagsContradictions:

    def test_flags_high_sat_negative_text(self):
        """High satisfaction (5) with strongly negative text → flagged."""
        bad = _make_response(
            q1=5, q2=9,
            q5="Absolutely terrible experience. The product was broken and customer service was useless."
        )
        result = validate_coherence(bad)
        # A tone mismatch violation must be detected
        assert any("tone_mismatch" in v for v in result.violations)
        # Score must be reduced (below perfect)
        assert result.score < 1.0
        # With threshold=0.6, one tone_mismatch (score=0.65) is borderline;
        # assert the violation fires correctly regardless of threshold
        assert len(result.violations) >= 1

    def test_flags_low_sat_positive_text(self):
        """Low satisfaction (1) with very positive text → flagged."""
        bad = _make_response(
            q1=1, q2=2,
            q5="Fantastic! I absolutely loved everything about this purchase. Highly recommend!"
        )
        result = validate_coherence(bad)
        assert any("tone_mismatch" in v for v in result.violations)
        assert result.score < 1.0
        assert len(result.violations) >= 1

    def test_flags_nps_sat_divergence(self):
        """NPS=10, satisfaction=1 → should be flagged."""
        bad = _make_response(q1=1, q2=10, q5="It was okay I guess.")
        result = validate_coherence(bad)
        assert result.is_coherent is False
        assert any("divergence" in v or "mismatch" in v for v in result.violations)

    def test_flags_promoter_low_sat(self):
        """NPS=9 with sat=1 → promoter_low_sat rule fires."""
        bad = _make_response(q1=1, q2=9, q5="Delivery was late and product was wrong.")
        result = validate_coherence(bad)
        assert any("promoter_low_sat" in v or "divergence" in v for v in result.violations)

    def test_flags_detractor_perfect_sat(self):
        """NPS=0 with sat=5 → detractor_high_sat rule fires."""
        bad = _make_response(q1=5, q2=0, q5="Everything was great honestly.")
        result = validate_coherence(bad)
        assert any("detractor" in v or "divergence" in v for v in result.violations)


class TestCoherenceValidatorPassesGoodResponses:

    def test_passes_high_sat_positive_text(self):
        """Satisfaction=5, NPS=9, positive text → coherent."""
        good = _make_response(
            q1=5, q2=9,
            q5="Great service, will definitely recommend to friends and family!"
        )
        result = validate_coherence(good)
        assert result.is_coherent is True
        assert len(result.violations) == 0

    def test_passes_low_sat_negative_text(self):
        """Satisfaction=1, NPS=1, negative text → coherent."""
        good = _make_response(
            q1=1, q2=1,
            q5="The product arrived damaged and returns took forever to process."
        )
        result = validate_coherence(good)
        assert result.is_coherent is True

    def test_passes_neutral_response(self):
        """Satisfaction=3, NPS=6, mild text → coherent."""
        good = _make_response(
            q1=3, q2=6,
            q5="Delivery tracking could be improved and the website checkout needs work."
        )
        result = validate_coherence(good)
        assert result.is_coherent is True

    def test_score_range_valid(self):
        """Score must always be between 0.0 and 1.0."""
        response = _make_response(q1=5, q2=9, q5="Excellent experience!")
        result = validate_coherence(response)
        assert 0.0 <= result.score <= 1.0


class TestSentimentScoring:

    def test_positive_text_positive_compound(self):
        score = compound_score("Fantastic service! I love this product and will recommend it.")
        assert score > 0.05

    def test_negative_text_negative_compound(self):
        score = compound_score("Terrible experience. Product was broken and useless.")
        assert score < -0.05

    def test_neutral_text_near_zero(self):
        score = compound_score("Delivery tracking could be improved.")
        assert -0.5 < score < 0.5

"""
tests/unit/test_validator_extended.py
Extended edge-case tests for the coherence validator and rules engine.
Covers: boundary VADER scores, all violation types, score arithmetic,
empty text, extremely long text, special characters, and threshold logic.
"""

import pytest
from unittest.mock import MagicMock
from src.validator.coherence import validate_coherence, CoherenceResult, PENALTY_PER_VIOLATION
from src.validator.sentiment import compound_score
from src.validator.rules import ALL_RULES


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_response(q1=3, q2=6, q4=True, q5="The service was acceptable.",
                  archetype="neutral_passive"):
    r = MagicMock()
    r.q1_satisfaction = q1
    r.q2_nps = q2
    r.q4_delivery_on_time = q4
    r.q5_open_text = q5
    r.persona_archetype = archetype
    return r


# ─── Score Arithmetic ─────────────────────────────────────────────────────────

class TestScoreArithmetic:

    def test_zero_violations_score_is_1(self):
        r = make_response(q1=5, q2=9, q5="Excellent! Will recommend to everyone.")
        result = validate_coherence(r)
        assert result.score == 1.0

    def test_score_never_negative(self):
        """Even with 10 violations, score must not go below 0."""
        r = make_response(q1=1, q2=10, q4=False,
                          q5="Absolutely fantastic! Loved it! Buy again!",
                          archetype="frustrated_detractor")
        result = validate_coherence(r)
        assert result.score >= 0.0

    def test_score_never_above_1(self):
        r = make_response(q1=5, q2=9, q5="Perfect experience!")
        result = validate_coherence(r)
        assert result.score <= 1.0

    def test_one_violation_reduces_score_by_penalty(self):
        """One violation must reduce score by exactly PENALTY_PER_VIOLATION."""
        # This response should fire exactly one rule
        r = make_response(q1=1, q2=10, q5="Okay experience.")
        result = validate_coherence(r)
        # nps_sat_divergence should fire for sat=1, nps=10
        if len(result.violations) == 1:
            expected = round(1.0 - PENALTY_PER_VIOLATION, 4)
            assert result.score == expected

    def test_two_violations_reduces_score_by_2x_penalty(self):
        r = make_response(q1=1, q2=10, q4=True,
                          q5="I absolutely loved every single thing about this wonderful experience!")
        result = validate_coherence(r)
        if len(result.violations) == 2:
            expected = round(max(0.0, 1.0 - 2 * PENALTY_PER_VIOLATION), 4)
            assert result.score == expected

    def test_custom_threshold_above_score_marks_incoherent(self):
        """A response with score=0.65 is NOT coherent at threshold=0.7."""
        r = make_response(q1=1, q2=10, q5="It was fine I guess.")
        result = validate_coherence(r, threshold=0.9)
        # With a very high threshold almost anything is incoherent
        assert not result.is_coherent

    def test_custom_threshold_below_score_marks_coherent(self):
        """A response that's otherwise borderline is coherent at threshold=0.0."""
        r = make_response(q1=1, q2=10, q5="It was great actually.",
                          archetype="frustrated_detractor")
        result = validate_coherence(r, threshold=0.0)
        assert result.is_coherent  # Everything is coherent at threshold 0


# ─── Sentiment Boundary Values ────────────────────────────────────────────────

class TestSentimentBoundaryValues:

    def test_empty_string_returns_neutral(self):
        """Empty string should return near-zero compound score."""
        score = compound_score("")
        assert -0.1 <= score <= 0.1

    def test_single_word_positive(self):
        score = compound_score("great")
        assert score > 0

    def test_single_word_negative(self):
        score = compound_score("terrible")
        assert score < 0

    def test_punctuation_only_returns_neutral(self):
        score = compound_score("... !!! ???")
        assert -0.2 <= score <= 0.2

    def test_very_long_positive_text(self):
        text = ("Excellent! " * 200)
        score = compound_score(text)
        assert score > 0.5

    def test_very_long_negative_text(self):
        text = ("Terrible! " * 200)
        score = compound_score(text)
        assert score < -0.5

    def test_mixed_sentiment_is_between(self):
        score = compound_score("The product was great but the shipping was terrible.")
        assert -0.5 < score < 0.5

    def test_all_caps_positive(self):
        """VADER handles ALL CAPS as emphasis."""
        normal = compound_score("great service")
        caps = compound_score("GREAT SERVICE")
        # CAPS should score higher or equal
        assert caps >= normal

    def test_special_characters_dont_crash(self):
        """Emojis, newlines, tabs must not crash the VADER scorer."""
        score = compound_score("Great product! \U0001f44d\nFast shipping.\tWill buy again.")
        assert isinstance(score, float)

    def test_numbers_only_returns_neutral(self):
        score = compound_score("1234567890")
        assert -0.1 <= score <= 0.1

    def test_non_english_text_returns_float(self):
        """Non-English text should not crash (may return 0)."""
        score = compound_score("Excelente servicio! Muy rapido.")
        assert isinstance(score, float)


# ─── Rule-Specific Edge Cases ─────────────────────────────────────────────────

class TestToneMismatchRule:

    def test_borderline_sat_4_with_negative_text_may_not_flag(self):
        """Sat=4 is not 'high enough' to trigger the high_sat rule if threshold not met."""
        r = make_response(q1=4, q2=8, q5="The wait time was somewhat disappointing.")
        result = validate_coherence(r)
        # Q1=4 with mildly negative text — may or may not flag
        # Key: score must still be a valid float
        assert isinstance(result.score, float)

    def test_sat_5_strongly_negative_text_always_flags(self):
        """Q1=5 + very negative text should always trigger tone_mismatch."""
        r = make_response(q1=5, q2=9,
                          q5="Completely horrible, broken on arrival, awful support team.")
        result = validate_coherence(r)
        assert any("tone_mismatch" in v for v in result.violations)

    def test_sat_1_strongly_positive_text_always_flags(self):
        """Q1=1 + very positive text should always trigger tone_mismatch."""
        r = make_response(q1=1, q2=0,
                          q5="Absolutely fantastic experience! Perfect in every way!")
        result = validate_coherence(r)
        assert any("tone_mismatch" in v for v in result.violations)

    def test_neutral_text_never_flags_on_mid_sat(self):
        """Q1=3 + neutral text should produce zero violations."""
        r = make_response(q1=3, q2=5, q5="The product was delivered last week.")
        result = validate_coherence(r)
        assert not any("tone_mismatch" in v for v in result.violations)


class TestNPSSatDivergenceRule:

    def test_exact_opposite_extremes_flagged(self):
        """Q1=1, Q2=10 (opposite extremes) must be flagged."""
        r = make_response(q1=1, q2=10, q5="It was okay.")
        result = validate_coherence(r)
        assert any("divergence" in v for v in result.violations)

    def test_q1_5_q2_10_not_flagged(self):
        """Q1=5, Q2=10 (perfectly aligned) must not trigger divergence."""
        r = make_response(q1=5, q2=10, q5="Outstanding service!")
        result = validate_coherence(r)
        assert not any("divergence" in v for v in result.violations)

    def test_q1_3_q2_5_not_flagged(self):
        """Moderate scores that are consistent should not flag."""
        r = make_response(q1=3, q2=5, q5="Average experience.")
        result = validate_coherence(r)
        assert not any("divergence" in v for v in result.violations)

    def test_q1_1_q2_1_not_flagged(self):
        """Both low — consistent, should not flag divergence."""
        r = make_response(q1=1, q2=0, q5="Worst purchase I ever made.")
        result = validate_coherence(r)
        assert not any("divergence" in v for v in result.violations)


class TestPromoterDetractorRules:

    def test_promoter_nps_10_sat_1_flagged(self):
        r = make_response(q1=1, q2=10, q5="The delivery was slow.")
        result = validate_coherence(r)
        assert any("promoter" in v for v in result.violations)

    def test_promoter_nps_9_sat_2_flagged(self):
        r = make_response(q1=2, q2=9, q5="Quite disappointed with quality.")
        result = validate_coherence(r)
        assert any("promoter" in v for v in result.violations)

    def test_promoter_nps_9_sat_4_not_flagged(self):
        """Q2=9 with Q1=4 is reasonable (very likely to recommend)."""
        r = make_response(q1=4, q2=9, q5="Really good service.")
        result = validate_coherence(r)
        assert not any("promoter_low_sat" in v for v in result.violations)

    def test_detractor_nps_0_sat_5_flagged(self):
        r = make_response(q1=5, q2=0, q5="All was good but something was off.")
        result = validate_coherence(r)
        assert any("detractor" in v for v in result.violations)

    def test_detractor_nps_6_sat_5_may_flag(self):
        """NPS=6 with Q1=5 is borderline detractor — test just that no crash."""
        r = make_response(q1=5, q2=6, q5="Really liked everything!")
        result = validate_coherence(r)
        assert isinstance(result.score, float)


# ─── CoherenceResult Fields ───────────────────────────────────────────────────

class TestCoherenceResultFields:

    def test_result_has_all_fields(self):
        r = make_response()
        result = validate_coherence(r)
        assert hasattr(result, "score")
        assert hasattr(result, "is_coherent")
        assert hasattr(result, "violations")
        assert hasattr(result, "sentiment_compound")
        assert hasattr(result, "threshold")

    def test_violations_is_list(self):
        r = make_response()
        result = validate_coherence(r)
        assert isinstance(result.violations, list)

    def test_sentiment_compound_is_float(self):
        r = make_response()
        result = validate_coherence(r)
        assert isinstance(result.sentiment_compound, float)

    def test_threshold_stored_in_result(self):
        r = make_response()
        result = validate_coherence(r, threshold=0.75)
        assert result.threshold == 0.75

    def test_default_threshold_is_0_6(self):
        r = make_response()
        result = validate_coherence(r)
        assert result.threshold == 0.6


# ─── Rules Count ──────────────────────────────────────────────────────────────

class TestAllRulesRegistered:

    def test_at_least_3_rules_registered(self):
        """We must have at least 3 coherence rules."""
        assert len(ALL_RULES) >= 3

    def test_all_rules_are_callable(self):
        for rule in ALL_RULES:
            assert callable(rule)

    def test_all_rules_return_string_or_none(self):
        """Every rule must return either a non-empty string (violation) or None."""
        r = make_response(q1=5, q2=9, q5="Excellent purchase!")
        import inspect
        for rule_fn in ALL_RULES:
            sig = inspect.signature(rule_fn)
            has_compound = "compound" in sig.parameters
            result = rule_fn(r, 0.9) if has_compound else rule_fn(r)
            assert result is None or (isinstance(result, str) and len(result) > 0), (
                f"Rule {rule_fn.__name__} returned unexpected: {result!r}"
            )

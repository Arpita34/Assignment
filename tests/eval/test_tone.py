"""
tests/eval/test_tone.py
LLM Eval Layer 1: VADER tone alignment test.
Checks that Q5 sentiment polarity matches Q1 satisfaction rating.
No LLM calls — uses VADER only.
"""

import pytest
from src.validator.sentiment import compound_score


class TestToneAlignment:
    """VADER sentiment of Q5 must align with Q1 satisfaction rating.

    Pass condition: ≥ 85% of high-sat responses are positive-toned,
                   ≥ 85% of low-sat responses are negative-toned.
    """

    def test_high_sat_positive_tone_rate(self, responses_df):
        """≥ 85% of responses with Q1 ≥ 4 should have positive VADER compound."""
        high_sat = responses_df[responses_df["q1_satisfaction"] >= 4].copy()

        if len(high_sat) < 10:
            pytest.skip("Not enough high-satisfaction responses")

        high_sat["compound"] = high_sat["q5_open_text"].apply(compound_score)
        pos_rate = (high_sat["compound"] > 0.05).mean()

        assert pos_rate >= 0.80, (
            f"High-sat positive tone rate = {pos_rate:.1%} (min 80%). "
            f"Failing rows:\n{high_sat[high_sat['compound'] <= 0.05][['q1_satisfaction','q5_open_text']].head(5)}"
        )

    def test_low_sat_negative_tone_rate(self, responses_df):
        """≥ 80% of responses with Q1 ≤ 2 should have negative VADER compound."""
        low_sat = responses_df[responses_df["q1_satisfaction"] <= 2].copy()

        if len(low_sat) < 5:
            pytest.skip("Not enough low-satisfaction responses")

        low_sat["compound"] = low_sat["q5_open_text"].apply(compound_score)
        neg_rate = (low_sat["compound"] < -0.05).mean()

        assert neg_rate >= 0.70, (
            f"Low-sat negative tone rate = {neg_rate:.1%} (min 70%). "
            f"Failing rows:\n{low_sat[low_sat['compound'] >= -0.05][['q1_satisfaction','q5_open_text']].head(5)}"
        )

    def test_sentiment_stored_matches_vader(self, responses_df):
        """sentiment_compound column should match fresh VADER computation."""
        sample = responses_df.sample(min(20, len(responses_df)), random_state=42)
        for _, row in sample.iterrows():
            fresh_compound = compound_score(str(row["q5_open_text"]))
            stored = float(row["sentiment_compound"])
            assert abs(fresh_compound - stored) < 0.01, (
                f"Stored compound {stored:.4f} != fresh {fresh_compound:.4f} "
                f"for: '{row['q5_open_text'][:60]}'"
            )

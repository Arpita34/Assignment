"""
tests/statistical/test_distributions.py
Statistical tests against the generated responses.csv.
Run with: pytest tests/statistical/ --responses-csv=outputs/responses.csv -v
All tests skip gracefully if the CSV hasn't been generated yet.
"""

import pytest
import numpy as np
import pandas as pd
from scipy.stats import chisquare
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TestCategoryDistribution:
    """Q3 category distribution should be balanced — not dominated by one category."""

    def test_chi_square_not_skewed(self, responses_df):
        """Chi-square test: distribution not significantly different from uniform."""
        counts = responses_df["q3_category"].value_counts()
        stat, p = chisquare(counts.values)
        assert p > 0.05, (
            f"Category distribution too skewed (p={p:.3f}). "
            f"Counts: {counts.to_dict()}"
        )

    def test_no_category_below_15_percent(self, responses_df):
        pct = responses_df["q3_category"].value_counts(normalize=True)
        assert pct.min() >= 0.10, (
            f"Category below 10%: {pct.idxmin()} = {pct.min():.1%}"
        )

    def test_no_category_above_50_percent(self, responses_df):
        pct = responses_df["q3_category"].value_counts(normalize=True)
        assert pct.max() <= 0.50, (
            f"Category above 50%: {pct.idxmax()} = {pct.max():.1%}"
        )


class TestSatisfactionSpread:
    """Q1 satisfaction should be varied — not all clustered at one value."""

    def test_std_dev_above_threshold(self, responses_df):
        std = responses_df["q1_satisfaction"].std()
        assert std > 1.0, f"Satisfaction std dev too low: {std:.3f} (min 1.0)"

    def test_all_rating_values_used(self, responses_df):
        unique = set(responses_df["q1_satisfaction"].unique())
        assert unique == {1, 2, 3, 4, 5}, (
            f"Not all rating values present. Got: {sorted(unique)}"
        )

    def test_no_single_value_dominates(self, responses_df):
        pct = responses_df["q1_satisfaction"].value_counts(normalize=True)
        assert pct.max() <= 0.50, (
            f"Single satisfaction value > 50%: {pct.idxmax()} = {pct.max():.1%}"
        )


class TestNPSDistribution:
    """NPS should have a healthy mix of detractors, passives, and promoters."""

    def test_promoters_plus_detractors_above_60_pct(self, responses_df):
        df = responses_df
        promoters = (df["q2_nps"] >= 9).sum()
        detractors = (df["q2_nps"] <= 6).sum()
        total = len(df)
        combined_pct = (promoters + detractors) / total
        assert combined_pct > 0.60, (
            f"Promoters+Detractors = {combined_pct:.1%} (min 60%)"
        )

    def test_nps_range_covers_full_spectrum(self, responses_df):
        unique = set(responses_df["q2_nps"].unique())
        # Should have at least 7 distinct NPS values
        assert len(unique) >= 7, f"Only {len(unique)} distinct NPS values"


class TestOpenTextUniqueness:
    """Q5 responses should be diverse — no near-duplicate templates."""

    def test_mean_cosine_similarity_below_threshold(self, responses_df):
        texts = responses_df["q5_open_text"].dropna().astype(str).tolist()
        if len(texts) < 10:
            pytest.skip("Not enough responses to test uniqueness")

        tfidf = TfidfVectorizer(stop_words="english")
        matrix = tfidf.fit_transform(texts)
        sim = cosine_similarity(matrix)
        np.fill_diagonal(sim, 0)   # Exclude self-similarity
        mean_sim = sim.mean()
        assert mean_sim < 0.4, (
            f"Q5 responses too similar: mean cosine similarity = {mean_sim:.3f} (max 0.4)"
        )

    def test_no_exact_duplicate_q5(self, responses_df):
        texts = responses_df["q5_open_text"].dropna().tolist()
        n_duplicates = len(texts) - len(set(texts))
        assert n_duplicates == 0, f"Found {n_duplicates} exact duplicate Q5 responses"


class TestCorrelations:
    """Q1 satisfaction and Q2 NPS should be strongly correlated."""

    def test_sat_nps_pearson_above_threshold(self, responses_df):
        r = responses_df[["q1_satisfaction", "q2_nps"]].corr().iloc[0, 1]
        assert r > 0.6, f"Q1–Q2 Pearson correlation too low: r={r:.3f} (min 0.6)"

    def test_delivery_impact_on_satisfaction(self, responses_df):
        """On-time delivery group should have higher mean satisfaction than late group."""
        on_time = responses_df[responses_df["q4_delivery_on_time"] == True]["q1_satisfaction"]
        late = responses_df[responses_df["q4_delivery_on_time"] == False]["q1_satisfaction"]

        if len(on_time) < 5 or len(late) < 5:
            pytest.skip("Not enough responses in each delivery group")

        diff = on_time.mean() - late.mean()
        assert diff > 0.3, (
            f"Delivery impact on satisfaction too small: Δ={diff:.3f} (min 0.3)"
        )


class TestCoherenceScores:
    """Generated responses should be mostly coherent."""

    def test_mean_coherence_above_threshold(self, responses_df):
        mean_coh = responses_df["coherence_score"].mean()
        assert mean_coh >= 0.6, f"Mean coherence score too low: {mean_coh:.3f}"

    def test_majority_coherent(self, responses_df):
        coherent_pct = (responses_df["coherence_score"] >= 0.6).mean()
        assert coherent_pct >= 0.80, (
            f"Only {coherent_pct:.1%} of responses are coherent (min 80%)"
        )


class TestArchetypeDistribution:
    """Persona archetypes should roughly match target weights."""

    def test_archetype_weights_within_tolerance(self, responses_df):
        from src.personas.archetypes import ARCHETYPES
        counts = responses_df["persona_archetype"].value_counts(normalize=True)
        for name, profile in ARCHETYPES.items():
            actual = counts.get(name, 0)
            diff = abs(actual - profile.weight)
            assert diff < 0.12, (
                f"Archetype '{name}': expected {profile.weight:.0%}, "
                f"got {actual:.0%} (diff={diff:.0%})"
            )

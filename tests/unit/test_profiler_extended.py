"""
tests/unit/test_profiler_extended.py
Extended edge-case tests for behavior profiler:
delivery sampling, all archetypes, penalty clamping, boundary NPS/sat ranges.
"""

import pytest
import numpy as np
from src.profiler.correlation import (
    get_behavior_profile,
    sample_delivery,
    BehaviorProfile,
    DELIVERY_LATE_RATE,
)
from src.personas.archetypes import ARCHETYPES


ALL_ARCHETYPES = list(ARCHETYPES.keys())


class TestBehaviorProfileAllArchetypes:
    """Every archetype must produce a valid BehaviorProfile in both delivery states."""

    @pytest.mark.parametrize("archetype", ALL_ARCHETYPES)
    def test_on_time_profile_valid(self, archetype):
        rng = np.random.default_rng(42)
        profile = get_behavior_profile(archetype, late_delivery=False, rng=rng)
        assert isinstance(profile, BehaviorProfile)
        assert profile.delivery_on_time is True

    @pytest.mark.parametrize("archetype", ALL_ARCHETYPES)
    def test_late_profile_valid(self, archetype):
        rng = np.random.default_rng(42)
        profile = get_behavior_profile(archetype, late_delivery=True, rng=rng)
        assert isinstance(profile, BehaviorProfile)
        assert profile.delivery_on_time is False

    @pytest.mark.parametrize("archetype", ALL_ARCHETYPES)
    def test_sat_range_always_valid(self, archetype):
        """sat_range lo ≤ hi, both within [1, 5]."""
        rng = np.random.default_rng(7)
        for late in [True, False]:
            profile = get_behavior_profile(archetype, late_delivery=late, rng=rng)
            lo, hi = profile.sat_range
            assert 1 <= lo <= hi <= 5, (
                f"{archetype} late={late}: sat_range={profile.sat_range} invalid"
            )

    @pytest.mark.parametrize("archetype", ALL_ARCHETYPES)
    def test_nps_range_always_valid(self, archetype):
        """nps_range lo ≤ hi, both within [0, 10]."""
        rng = np.random.default_rng(7)
        for late in [True, False]:
            profile = get_behavior_profile(archetype, late_delivery=late, rng=rng)
            lo, hi = profile.nps_range
            assert 0 <= lo <= hi <= 10, (
                f"{archetype} late={late}: nps_range={profile.nps_range} invalid"
            )

    @pytest.mark.parametrize("archetype", ALL_ARCHETYPES)
    def test_q5_tone_is_non_empty_string(self, archetype):
        rng = np.random.default_rng(1)
        profile = get_behavior_profile(archetype, late_delivery=False, rng=rng)
        assert isinstance(profile.q5_tone, str) and len(profile.q5_tone) > 0

    @pytest.mark.parametrize("archetype", ALL_ARCHETYPES)
    def test_q5_topics_is_list(self, archetype):
        rng = np.random.default_rng(1)
        profile = get_behavior_profile(archetype, late_delivery=False, rng=rng)
        assert isinstance(profile.q5_topics, list)
        assert len(profile.q5_topics) > 0

    @pytest.mark.parametrize("archetype", ALL_ARCHETYPES)
    def test_late_delivery_lowers_sat_or_nps(self, archetype):
        """Late delivery must reduce or equal (never increase) sat/nps ranges."""
        rng = np.random.default_rng(42)
        on_time = get_behavior_profile(archetype, late_delivery=False, rng=rng)
        rng2 = np.random.default_rng(42)
        late = get_behavior_profile(archetype, late_delivery=True, rng=rng2)
        # At minimum, combined mean NPS should not increase
        on_time_mean_nps = (on_time.nps_range[0] + on_time.nps_range[1]) / 2
        late_mean_nps = (late.nps_range[0] + late.nps_range[1]) / 2
        assert late_mean_nps <= on_time_mean_nps + 0.5, (
            f"{archetype}: late NPS mean {late_mean_nps} > on-time {on_time_mean_nps}"
        )


class TestDeliverySampling:

    def test_delivery_returns_bool(self):
        rng = np.random.default_rng(42)
        result = sample_delivery("happy_customer", rng)
        assert isinstance(result, bool)

    def test_happy_customer_mostly_on_time_at_large_n(self):
        """At N=1000, happy_customer late rate should be ~15%."""
        rng = np.random.default_rng(0)
        late_count = sum(sample_delivery("happy_customer", rng) for _ in range(1000))
        rate = late_count / 1000
        # Expect around 15% ± 5%
        assert 0.08 <= rate <= 0.25, f"happy_customer late rate = {rate:.2%}"

    def test_frustrated_detractor_often_late(self):
        """frustrated_detractor late rate ~50%."""
        rng = np.random.default_rng(0)
        late_count = sum(sample_delivery("frustrated_detractor", rng) for _ in range(1000))
        rate = late_count / 1000
        assert 0.38 <= rate <= 0.62, f"frustrated_detractor late rate = {rate:.2%}"

    def test_all_archetypes_have_delivery_rate(self):
        """All archetypes should have a defined late rate between 0 and 1."""
        for archetype in ALL_ARCHETYPES:
            rate = DELIVERY_LATE_RATE.get(archetype, None)
            assert rate is not None, f"{archetype} has no late delivery rate"
            assert 0.0 <= rate <= 1.0


class TestProfilePenaltyClamping:

    def test_frustrated_late_sat_never_below_1(self):
        """Even with maximum penalties, sat_min must stay >= 1."""
        rng = np.random.default_rng(42)
        profile = get_behavior_profile("frustrated_detractor", late_delivery=True, rng=rng)
        assert profile.sat_range[0] >= 1

    def test_frustrated_late_nps_never_below_0(self):
        """Even with maximum penalties, nps_min must stay >= 0."""
        rng = np.random.default_rng(42)
        profile = get_behavior_profile("frustrated_detractor", late_delivery=True, rng=rng)
        assert profile.nps_range[0] >= 0

    def test_happy_customer_late_sat_still_positive(self):
        """Even a happy customer who got late delivery should have sat >= 1."""
        rng = np.random.default_rng(42)
        profile = get_behavior_profile("happy_customer", late_delivery=True, rng=rng)
        assert profile.sat_range[0] >= 1

    def test_late_topics_include_delivery_keywords(self):
        """Late delivery profiles must include delivery-related topics."""
        rng = np.random.default_rng(42)
        profile = get_behavior_profile("happy_customer", late_delivery=True, rng=rng)
        topics_str = " ".join(profile.q5_topics).lower()
        assert any(kw in topics_str for kw in ["delivery", "late", "shipping", "tracking"]), (
            f"No delivery keywords in topics: {profile.q5_topics}"
        )


class TestUnknownArchetype:

    def test_unknown_archetype_raises_key_error(self):
        """Passing an archetype not in ARCHETYPES should raise KeyError."""
        rng = np.random.default_rng(42)
        with pytest.raises(KeyError):
            get_behavior_profile("nonexistent_archetype", late_delivery=False, rng=rng)


class TestNumericSamplerExtended:
    """Extended tests for the numeric answer sampler."""

    def test_q1_always_in_1_to_5(self):
        """Q1 must always be 1–5 regardless of archetype or delivery."""
        import numpy as np
        from src.generator.numeric import sample_numeric_answers

        rng = np.random.default_rng(42)
        for archetype in ALL_ARCHETYPES:
            for late in [True, False]:
                profile = get_behavior_profile(archetype, late_delivery=late, rng=rng)
                from src.personas.generator import generate_personas
                persona = generate_personas(1, seed=42)[0]
                answers = sample_numeric_answers(persona, profile, rng)
                assert 1 <= answers["q1_satisfaction"] <= 5

    def test_q2_always_in_0_to_10(self):
        import numpy as np
        from src.generator.numeric import sample_numeric_answers
        from src.personas.generator import generate_personas

        rng = np.random.default_rng(0)
        persona = generate_personas(1, seed=0)[0]
        for archetype in ALL_ARCHETYPES:
            for late in [True, False]:
                profile = get_behavior_profile(archetype, late_delivery=late, rng=rng)
                answers = sample_numeric_answers(persona, profile, rng)
                assert 0 <= answers["q2_nps"] <= 10

    def test_q4_matches_profile_delivery(self):
        import numpy as np
        from src.generator.numeric import sample_numeric_answers
        from src.personas.generator import generate_personas

        rng = np.random.default_rng(0)
        persona = generate_personas(1, seed=0)[0]
        for late in [True, False]:
            profile = get_behavior_profile("happy_customer", late_delivery=late, rng=rng)
            answers = sample_numeric_answers(persona, profile, rng)
            assert answers["q4_delivery_on_time"] == (not late)

    def test_q1_q2_correlation_over_100_samples(self):
        """Over 100 samples, Q1 and Q2 must have Pearson r > 0.5."""
        import numpy as np
        from src.generator.numeric import sample_numeric_answers
        from src.personas.generator import generate_personas
        from src.profiler.correlation import sample_delivery

        personas = generate_personas(100, seed=1)
        rng = np.random.default_rng(1)
        q1s, q2s = [], []
        for p in personas:
            late = sample_delivery(p.archetype, rng)
            profile = get_behavior_profile(p.archetype, late_delivery=late, rng=rng)
            answers = sample_numeric_answers(p, profile, rng)
            q1s.append(answers["q1_satisfaction"])
            q2s.append(answers["q2_nps"])

        r = np.corrcoef(q1s, q2s)[0, 1]
        assert r > 0.5, f"Q1-Q2 Pearson correlation too low: r={r:.3f}"

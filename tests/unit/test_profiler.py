"""
tests/unit/test_profiler.py
Unit tests for behavior profiler correlation rules. No LLM calls.
"""

import pytest
import numpy as np
from src.profiler.correlation import get_behavior_profile, sample_delivery, BehaviorProfile


RNG = np.random.default_rng(42)


class TestBehaviorRulesFrustratedLate:
    """Frustrated detractor + late delivery → very low sat and NPS."""

    def test_frustrated_late_sat_range(self):
        profile = get_behavior_profile("frustrated_detractor", late_delivery=True, rng=RNG)
        lo, hi = profile.sat_range
        assert lo >= 1
        assert hi <= 2, f"Frustrated+late sat_max should be ≤ 2, got {hi}"

    def test_frustrated_late_nps_range(self):
        profile = get_behavior_profile("frustrated_detractor", late_delivery=True, rng=RNG)
        lo, hi = profile.nps_range
        assert lo >= 0
        assert hi <= 3, f"Frustrated+late nps_max should be ≤ 3, got {hi}"

    def test_frustrated_late_delivery_flag(self):
        profile = get_behavior_profile("frustrated_detractor", late_delivery=True, rng=RNG)
        assert profile.delivery_on_time is False

    def test_frustrated_late_tone_is_negative(self):
        profile = get_behavior_profile("frustrated_detractor", late_delivery=True, rng=RNG)
        assert "negative" in profile.q5_tone


class TestBehaviorRulesHappyOnTime:
    """Happy customer + on-time delivery → high sat and NPS."""

    def test_happy_ontime_sat_range(self):
        profile = get_behavior_profile("happy_customer", late_delivery=False, rng=RNG)
        lo, hi = profile.sat_range
        assert lo >= 4, f"Happy+on-time sat_min should be ≥ 4, got {lo}"
        assert hi <= 5

    def test_happy_ontime_nps_range(self):
        profile = get_behavior_profile("happy_customer", late_delivery=False, rng=RNG)
        lo, hi = profile.nps_range
        assert lo >= 8, f"Happy+on-time nps_min should be ≥ 8, got {lo}"
        assert hi <= 10

    def test_happy_ontime_delivery_flag(self):
        profile = get_behavior_profile("happy_customer", late_delivery=False, rng=RNG)
        assert profile.delivery_on_time is True

    def test_happy_ontime_tone_is_positive(self):
        profile = get_behavior_profile("happy_customer", late_delivery=False, rng=RNG)
        assert profile.q5_tone == "positive"


class TestBehaviorRulesNeutral:
    """Neutral passive + on-time → mid sat and NPS."""

    def test_neutral_ontime_sat_is_3(self):
        profile = get_behavior_profile("neutral_passive", late_delivery=False, rng=RNG)
        lo, hi = profile.sat_range
        assert lo == 3 and hi == 3, f"Neutral+on-time sat should be (3,3), got ({lo},{hi})"

    def test_neutral_ontime_nps_in_range(self):
        profile = get_behavior_profile("neutral_passive", late_delivery=False, rng=RNG)
        lo, hi = profile.nps_range
        assert lo >= 6 and hi <= 7

    def test_neutral_late_nps_lower_than_ontime(self):
        p_on = get_behavior_profile("neutral_passive", late_delivery=False, rng=RNG)
        p_late = get_behavior_profile("neutral_passive", late_delivery=True, rng=RNG)
        # Late should have lower or equal NPS max
        assert p_late.nps_range[1] <= p_on.nps_range[1]


class TestBehaviorRulesDeliveryFocused:
    """Delivery-focused persona responds sharply to delivery outcome."""

    def test_delivery_focused_late_sat_very_low(self):
        profile = get_behavior_profile("delivery_focused", late_delivery=True, rng=RNG)
        lo, hi = profile.sat_range
        assert hi <= 2, f"Delivery-focused+late sat_max should be ≤ 2, got {hi}"

    def test_delivery_focused_ontime_sat_high(self):
        profile = get_behavior_profile("delivery_focused", late_delivery=False, rng=RNG)
        lo, hi = profile.sat_range
        assert lo >= 4


class TestSampleDelivery:
    """Test delivery sampling rates per archetype."""

    def test_happy_customer_mostly_on_time(self):
        rng = np.random.default_rng(0)
        late_count = sum(sample_delivery("happy_customer", rng) for _ in range(1000))
        # Should be roughly 15%
        assert 80 < late_count < 250, f"Expected ~150 late, got {late_count}"

    def test_frustrated_detractor_often_late(self):
        rng = np.random.default_rng(0)
        late_count = sum(sample_delivery("frustrated_detractor", rng) for _ in range(1000))
        # Should be roughly 50%
        assert 350 < late_count < 650, f"Expected ~500 late, got {late_count}"

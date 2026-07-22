"""Tests for power / sample-size / MDE analysis."""

import numpy as np
import pytest

from abtest import (
    mde_means,
    mde_proportions,
    power_means,
    power_proportions,
    sample_size_means,
    sample_size_proportions,
    simulate_binary,
    two_proportion_ztest,
)


def test_power_increases_with_sample_size():
    p1, p2 = 0.10, 0.12
    powers = [power_proportions(p1, p2, n) for n in (500, 2000, 8000, 32000)]
    assert powers == sorted(powers)
    assert powers[0] < powers[-1]
    assert 0.0 < powers[0] and powers[-1] < 1.0


def test_sample_size_then_power_hits_target():
    p1, mde = 0.10, 0.02
    n = sample_size_proportions(p1, mde, alpha=0.05, power=0.80)
    achieved = power_proportions(p1, p1 + mde, n, alpha=0.05)
    assert achieved == pytest.approx(0.80, abs=0.01)


def test_mde_proportions_roundtrip():
    """MDE inverted from (n, power) should give exactly that power back."""
    p1, n = 0.10, 6000
    mde = mde_proportions(p1, n, alpha=0.05, power=0.80)
    back = power_proportions(p1, p1 + mde, n, alpha=0.05)
    assert back == pytest.approx(0.80, abs=1e-3)


def test_mde_means_roundtrip():
    sigma, n = 2.0, 4000
    mde = mde_means(sigma, n, alpha=0.05, power=0.80)
    back = power_means(mde, sigma, n, alpha=0.05)
    assert back == pytest.approx(0.80, abs=1e-3)


def test_sample_size_means_then_power():
    n = sample_size_means(mean_diff=0.3, sigma=2.0, alpha=0.05, power=0.90)
    achieved = power_means(0.3, 2.0, n, alpha=0.05)
    assert achieved == pytest.approx(0.90, abs=0.01)


def test_empirical_power_matches_prediction():
    """Simulate at the sample size for 80% power; empirical rejection ~ 80%."""
    p1, mde = 0.10, 0.03
    n = int(sample_size_proportions(p1, mde, alpha=0.05, power=0.80))
    predicted = power_proportions(p1, p1 + mde, n, alpha=0.05)
    rejects, n_sims = 0, 300
    for s in range(n_sims):
        exp = simulate_binary(n, n, p1, p1 + mde, seed=2000 + s)
        if two_proportion_ztest(exp.control, exp.treatment, alpha=0.05).significant:
            rejects += 1
    rate = rejects / n_sims
    assert abs(rate - predicted) < 0.07

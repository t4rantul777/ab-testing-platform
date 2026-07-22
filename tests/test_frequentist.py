"""Tests for the fixed-horizon frequentist tests.

Where possible each property is checked against an *independent* reference
(statsmodels, or an algebraic identity) rather than the same code path.
"""

import numpy as np
import pytest
from statsmodels.stats.proportion import proportions_ztest

from abtest import (
    MetricType,
    analyze,
    chi_square_test,
    simulate_binary,
    simulate_continuous,
    two_proportion_ztest,
    welch_ttest,
)
from abtest.datamodel import Alternative


def test_two_proportion_matches_statsmodels():
    exp = simulate_binary(4000, 4000, 0.10, 0.13, seed=1)
    res = two_proportion_ztest(exp.control, exp.treatment)
    count = np.array([exp.treatment.sum(), exp.control.sum()])
    nobs = np.array([len(exp.treatment), len(exp.control)])
    z_sm, p_sm = proportions_ztest(count, nobs)  # pooled by default
    assert res.p_value == pytest.approx(p_sm, abs=1e-9)
    assert abs(res.statistic) == pytest.approx(abs(z_sm), abs=1e-9)


def test_chi_square_equals_z_squared():
    """Chi-square (no correction) statistic equals the z-test statistic squared."""
    exp = simulate_binary(5000, 5000, 0.12, 0.15, seed=2)
    z = two_proportion_ztest(exp.control, exp.treatment)
    c = chi_square_test(exp.control, exp.treatment)
    assert c.statistic == pytest.approx(z.statistic**2, rel=1e-6)
    assert c.p_value == pytest.approx(z.p_value, abs=1e-9)


def test_ci_contains_point_estimate_and_matches_significance():
    exp = simulate_binary(6000, 6000, 0.10, 0.135, seed=3)
    res = two_proportion_ztest(exp.control, exp.treatment)
    assert res.ci_low <= res.effect_estimate <= res.ci_high
    # significance and "CI excludes 0" must agree for a two-sided test
    excludes_zero = not (res.ci_low <= 0 <= res.ci_high)
    assert excludes_zero == res.significant


def test_welch_ttest_basic_properties():
    exp = simulate_continuous(3000, 3000, 10.0, 10.4, sigma=2.0, seed=4)
    res = welch_ttest(exp.control, exp.treatment)
    assert res.effect_estimate == pytest.approx(exp.observed_effect, rel=1e-9)
    assert res.ci_low <= res.effect_estimate <= res.ci_high
    assert res.significant  # 0.4 shift on sigma 2 with n=3000 is easily detected
    assert res.extra["df"] > 1000


def test_welch_one_sided_matches_half_two_sided_pvalue_direction():
    exp = simulate_continuous(2000, 2000, 5.0, 5.3, sigma=1.5, seed=8)
    two = welch_ttest(exp.control, exp.treatment, alternative=Alternative.TWO_SIDED)
    larger = welch_ttest(exp.control, exp.treatment, alternative=Alternative.LARGER)
    # For an effect in the 'larger' direction, one-sided p ~ two-sided / 2
    assert larger.p_value == pytest.approx(two.p_value / 2, rel=1e-6)


def test_analyze_dispatch():
    b = simulate_binary(1000, 1000, 0.1, 0.12, seed=1)
    c = simulate_continuous(1000, 1000, 1.0, 1.1, sigma=1.0, seed=1)
    assert analyze(b.control, b.treatment, MetricType.BINARY).test_name.startswith("Two-proportion")
    assert analyze(c.control, c.treatment, MetricType.CONTINUOUS).test_name.startswith("Welch")


def test_null_false_positive_rate_is_controlled():
    """Under H0 (no effect) the z-test should reject ~alpha of the time."""
    alpha = 0.05
    rejects = 0
    n_sims = 400
    for s in range(n_sims):
        exp = simulate_binary(2000, 2000, 0.12, 0.12, seed=1000 + s)
        if two_proportion_ztest(exp.control, exp.treatment, alpha=alpha).significant:
            rejects += 1
    rate = rejects / n_sims
    # binomial noise on 400 sims: 3 sigma ~ 0.03 around 0.05
    assert rate < 0.09

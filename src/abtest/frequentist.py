"""Classic (fixed-horizon) frequentist tests.

These are the tests you run *once*, after the experiment has reached its
pre-computed sample size. Peeking at them repeatedly inflates the false-positive
rate -- which is exactly why the :mod:`abtest.sequential` module exists.

Implemented here:

* Welch's two-sample t-test (unequal variances) for continuous metrics.
* Two-proportion z-test (pooled variance for the test, unpooled Wald interval
  for the CI) for binary metrics.
* Pearson's chi-square test of independence on the 2x2 table.
* Effect sizes: absolute difference, relative lift, Cohen's d and Cohen's h.

Where a reference implementation exists in SciPy / statsmodels we deliberately
delegate to it and only add the confidence interval and tidy packaging, so the
numbers are trustworthy rather than hand-rolled.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from .datamodel import Alternative, MetricType, TestResult


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def _z_crit(alpha: float, alternative: Alternative) -> float:
    if alternative is Alternative.TWO_SIDED:
        return float(stats.norm.ppf(1 - alpha / 2))
    return float(stats.norm.ppf(1 - alpha))


def cohens_d(control: np.ndarray, treatment: np.ndarray) -> float:
    """Standardised mean difference using the pooled standard deviation."""
    n1, n2 = len(control), len(treatment)
    s1, s2 = np.var(control, ddof=1), np.var(treatment, ddof=1)
    pooled = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if pooled == 0:
        return 0.0
    return float((np.mean(treatment) - np.mean(control)) / pooled)


def cohens_h(p1: float, p2: float) -> float:
    """Effect size for the difference between two proportions."""
    return float(2 * np.arcsin(np.sqrt(p2)) - 2 * np.arcsin(np.sqrt(p1)))


# ----------------------------------------------------------------------------
# continuous metric -- Welch's t-test
# ----------------------------------------------------------------------------
def welch_ttest(
    control: np.ndarray,
    treatment: np.ndarray,
    alpha: float = 0.05,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> TestResult:
    """Welch's unequal-variance two-sample t-test with a CI on the mean diff."""
    control = np.asarray(control, dtype=float)
    treatment = np.asarray(treatment, dtype=float)
    n1, n2 = len(control), len(treatment)

    mean_c, mean_t = float(np.mean(control)), float(np.mean(treatment))
    var_c, var_t = np.var(control, ddof=1), np.var(treatment, ddof=1)
    diff = mean_t - mean_c
    se = np.sqrt(var_c / n1 + var_t / n2)

    # Welch-Satterthwaite degrees of freedom.
    df = (var_c / n1 + var_t / n2) ** 2 / (
        (var_c / n1) ** 2 / (n1 - 1) + (var_t / n2) ** 2 / (n2 - 1)
    )

    sp_alt = {
        Alternative.TWO_SIDED: "two-sided",
        Alternative.LARGER: "greater",
        Alternative.SMALLER: "less",
    }[alternative]
    t_stat, p_value = stats.ttest_ind(
        treatment, control, equal_var=False, alternative=sp_alt
    )

    if alternative is Alternative.TWO_SIDED:
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        ci_low, ci_high = diff - t_crit * se, diff + t_crit * se
    elif alternative is Alternative.LARGER:
        t_crit = stats.t.ppf(1 - alpha, df)
        ci_low, ci_high = diff - t_crit * se, np.inf
    else:
        t_crit = stats.t.ppf(1 - alpha, df)
        ci_low, ci_high = -np.inf, diff + t_crit * se

    return TestResult(
        test_name="Welch t-test",
        statistic=float(t_stat),
        p_value=float(p_value),
        effect_estimate=diff,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        alpha=alpha,
        significant=bool(p_value < alpha),
        n_control=n1,
        n_treatment=n2,
        extra={
            "df": float(df),
            "mean_control": mean_c,
            "mean_treatment": mean_t,
            "std_error": float(se),
            "cohens_d": cohens_d(control, treatment),
            "relative_lift": diff / mean_c if mean_c else float("nan"),
        },
    )


# ----------------------------------------------------------------------------
# binary metric -- two-proportion z-test
# ----------------------------------------------------------------------------
def two_proportion_ztest(
    control: np.ndarray,
    treatment: np.ndarray,
    alpha: float = 0.05,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> TestResult:
    """Two-proportion z-test.

    The test statistic uses the *pooled* variance (the standard textbook form,
    equivalent to the chi-square test). The confidence interval uses the
    *unpooled* (Wald) variance, which is the interval you actually report for
    the difference in rates.
    """
    control = np.asarray(control, dtype=float)
    treatment = np.asarray(treatment, dtype=float)
    n1, n2 = len(control), len(treatment)
    x1, x2 = float(control.sum()), float(treatment.sum())
    p1, p2 = x1 / n1, x2 / n2
    diff = p2 - p1

    p_pool = (x1 + x2) / (n1 + n2)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = diff / se_pool if se_pool > 0 else 0.0

    if alternative is Alternative.TWO_SIDED:
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    elif alternative is Alternative.LARGER:
        p_value = 1 - stats.norm.cdf(z)
    else:
        p_value = stats.norm.cdf(z)

    se_unpool = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z_crit = _z_crit(alpha, alternative)
    if alternative is Alternative.TWO_SIDED:
        ci_low, ci_high = diff - z_crit * se_unpool, diff + z_crit * se_unpool
    elif alternative is Alternative.LARGER:
        ci_low, ci_high = diff - z_crit * se_unpool, 1.0
    else:
        ci_low, ci_high = -1.0, diff + z_crit * se_unpool

    return TestResult(
        test_name="Two-proportion z-test",
        statistic=float(z),
        p_value=float(p_value),
        effect_estimate=diff,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        alpha=alpha,
        significant=bool(p_value < alpha),
        n_control=n1,
        n_treatment=n2,
        extra={
            "rate_control": p1,
            "rate_treatment": p2,
            "pooled_rate": p_pool,
            "std_error": float(se_unpool),
            "cohens_h": cohens_h(p1, p2),
            "relative_lift": diff / p1 if p1 else float("nan"),
        },
    )


def chi_square_test(
    control: np.ndarray,
    treatment: np.ndarray,
    alpha: float = 0.05,
) -> TestResult:
    """Pearson chi-square test of independence on the 2x2 conversion table.

    Without the continuity correction this is algebraically identical to the
    two-sided two-proportion z-test (chi2 == z**2), which the test-suite checks.
    """
    control = np.asarray(control, dtype=float)
    treatment = np.asarray(treatment, dtype=float)
    n1, n2 = len(control), len(treatment)
    x1, x2 = float(control.sum()), float(treatment.sum())
    table = np.array([[x1, n1 - x1], [x2, n2 - x2]])
    chi2, p_value, dof, _expected = stats.chi2_contingency(table, correction=False)
    diff = x2 / n2 - x1 / n1
    return TestResult(
        test_name="Chi-square test",
        statistic=float(chi2),
        p_value=float(p_value),
        effect_estimate=float(diff),
        ci_low=float("nan"),
        ci_high=float("nan"),
        alpha=alpha,
        significant=bool(p_value < alpha),
        n_control=n1,
        n_treatment=n2,
        extra={"dof": int(dof), "cramers_v": float(np.sqrt(chi2 / (n1 + n2)))},
    )


def analyze(
    control: np.ndarray,
    treatment: np.ndarray,
    metric_type: MetricType,
    alpha: float = 0.05,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> TestResult:
    """Dispatch to the right primary test for the metric type."""
    if metric_type is MetricType.BINARY:
        return two_proportion_ztest(control, treatment, alpha, alternative)
    return welch_ttest(control, treatment, alpha, alternative)

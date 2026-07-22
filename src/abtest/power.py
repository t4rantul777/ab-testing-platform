"""Power, sample-size and minimum-detectable-effect (MDE) analysis.

Answers the three questions every experiment design starts with:

* "If the true effect is X, how likely am I to detect it?"      -> power
* "How many users do I need to detect effect X?"                 -> sample size
* "With the traffic I have, what is the smallest effect I can    -> MDE
   reliably detect?"

We build on statsmodels' power solvers (``NormalIndPower`` for proportions via
Cohen's h, ``TTestIndPower`` for means via Cohen's d) and add the inversions
and the plotting-ready curves on top.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from statsmodels.stats.power import NormalIndPower, TTestIndPower
from statsmodels.stats.proportion import proportion_effectsize

from .datamodel import Alternative

_ALT = {
    Alternative.TWO_SIDED: "two-sided",
    Alternative.LARGER: "larger",
    Alternative.SMALLER: "smaller",
}


@dataclass
class PowerResult:
    power: float
    n_per_arm: float
    alpha: float
    effect_size: float
    mde_absolute: float
    detail: dict


# ----------------------------------------------------------------------------
# proportions
# ----------------------------------------------------------------------------
def power_proportions(
    p1: float,
    p2: float,
    n_per_arm: float,
    alpha: float = 0.05,
    ratio: float = 1.0,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> float:
    """Statistical power of the two-proportion z-test."""
    h = proportion_effectsize(p2, p1)
    return float(
        NormalIndPower().power(
            effect_size=abs(h),
            nobs1=n_per_arm,
            alpha=alpha,
            ratio=ratio,
            alternative=_ALT[alternative],
        )
    )


def sample_size_proportions(
    p1: float,
    mde_absolute: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> float:
    """Required control-arm sample size to detect ``mde_absolute``."""
    p2 = p1 + mde_absolute
    h = proportion_effectsize(p2, p1)
    n = NormalIndPower().solve_power(
        effect_size=abs(h),
        alpha=alpha,
        power=power,
        ratio=ratio,
        alternative=_ALT[alternative],
    )
    return float(np.ceil(n))


def mde_proportions(
    p1: float,
    n_per_arm: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> float:
    """Smallest absolute lift detectable with the given sample size / power."""
    h = NormalIndPower().solve_power(
        effect_size=None,
        nobs1=n_per_arm,
        alpha=alpha,
        power=power,
        ratio=ratio,
        alternative=_ALT[alternative],
    )
    # Invert Cohen's h (h = 2*asin(sqrt(p2)) - 2*asin(sqrt(p1))) for p2 >= p1.
    phi1 = np.arcsin(np.sqrt(p1))
    p2 = np.sin(phi1 + h / 2) ** 2
    return float(p2 - p1)


# ----------------------------------------------------------------------------
# means
# ----------------------------------------------------------------------------
def power_means(
    mean_diff: float,
    sigma: float,
    n_per_arm: float,
    alpha: float = 0.05,
    ratio: float = 1.0,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> float:
    """Statistical power of the two-sample t-test for a mean difference."""
    d = mean_diff / sigma
    return float(
        TTestIndPower().power(
            effect_size=abs(d),
            nobs1=n_per_arm,
            alpha=alpha,
            ratio=ratio,
            alternative=_ALT[alternative],
        )
    )


def sample_size_means(
    mean_diff: float,
    sigma: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> float:
    """Required control-arm sample size to detect a mean difference."""
    d = mean_diff / sigma
    n = TTestIndPower().solve_power(
        effect_size=abs(d),
        alpha=alpha,
        power=power,
        ratio=ratio,
        alternative=_ALT[alternative],
    )
    return float(np.ceil(n))


def mde_means(
    sigma: float,
    n_per_arm: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> float:
    """Smallest absolute mean difference detectable with given n / power."""
    d = TTestIndPower().solve_power(
        effect_size=None,
        nobs1=n_per_arm,
        alpha=alpha,
        power=power,
        ratio=ratio,
        alternative=_ALT[alternative],
    )
    return float(d * sigma)


# ----------------------------------------------------------------------------
# curves for visualisation
# ----------------------------------------------------------------------------
def power_curve_by_n(
    p1: float,
    effect_absolute: float,
    n_grid: np.ndarray,
    alpha: float = 0.05,
    metric: str = "binary",
    sigma: float = 1.0,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> np.ndarray:
    """Power as a function of per-arm sample size (for the classic S-curve)."""
    out = []
    for n in n_grid:
        if metric == "binary":
            out.append(power_proportions(p1, p1 + effect_absolute, n, alpha, 1.0, alternative))
        else:
            out.append(power_means(effect_absolute, sigma, n, alpha, 1.0, alternative))
    return np.array(out)


def power_curve_by_effect(
    p1: float,
    effect_grid: np.ndarray,
    n_per_arm: float,
    alpha: float = 0.05,
    metric: str = "binary",
    sigma: float = 1.0,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> np.ndarray:
    """Power as a function of the true effect size, holding n fixed."""
    out = []
    for eff in effect_grid:
        if metric == "binary":
            out.append(power_proportions(p1, p1 + eff, n_per_arm, alpha, 1.0, alternative))
        else:
            out.append(power_means(eff, sigma, n_per_arm, alpha, 1.0, alternative))
    return np.array(out)

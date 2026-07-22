"""Sequential / always-valid testing -- stop the experiment early, safely.

The problem this solves: if you run a fixed-horizon test but *peek* at the
p-value every day and stop as soon as p < 0.05, your real false-positive rate is
nowhere near 5% -- with enough looks it approaches 100%. The methods here let
you look as often as you like while keeping the type-I error at the nominal
level, so you can stop winners (and losers) early.

Three complementary approaches are implemented:

1. ``sprt`` -- Wald's Sequential Probability Ratio Test. Tests a simple H0
   effect against a simple H1 effect; decides accept / reject / continue.

2. ``msprt_*`` -- the mixture SPRT (Robbins). Gives an *always-valid p-value*
   and a *confidence sequence* in closed form for a Gaussian effect estimate.
   This is the modern "peek any time" method used by commercial platforms.

3. ``group_sequential_boundaries`` -- Pocock and O'Brien-Fleming group-
   sequential designs. Computes the exact rejection boundaries for K interim
   looks via the Armitage-McPherson-Rowe recursion so the family-wise error
   equals alpha. ``sequential_alpha`` verifies the achieved error of any
   boundary set (used by the test-suite).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import stats


# ============================================================================
# 1. Wald SPRT
# ============================================================================
@dataclass
class SPRTResult:
    decision: str  # "reject_h0", "accept_h0", or "continue"
    stopping_index: int | None
    log_lr: np.ndarray
    upper: float
    lower: float


def sprt_normal(
    stream_values: np.ndarray,
    mean_0: float,
    mean_1: float,
    sigma: float,
    alpha: float = 0.05,
    beta: float = 0.20,
) -> SPRTResult:
    """Wald SPRT for the mean of a Gaussian stream (known sigma).

    Accumulates the log-likelihood ratio of H1 (mean_1) vs H0 (mean_0) and
    stops when it crosses the Wald boundaries ``log(beta/(1-alpha))`` (accept
    H0) or ``log((1-beta)/alpha)`` (reject H0).
    """
    x = np.asarray(stream_values, dtype=float)
    # Per-observation log-LR for two Gaussians with common sigma.
    llr_increment = ((mean_1 - mean_0) * x - (mean_1**2 - mean_0**2) / 2) / sigma**2
    cum = np.cumsum(llr_increment)

    upper = np.log((1 - beta) / alpha)
    lower = np.log(beta / (1 - alpha))

    decision, stop = "continue", None
    for i, val in enumerate(cum):
        if val >= upper:
            decision, stop = "reject_h0", i
            break
        if val <= lower:
            decision, stop = "accept_h0", i
            break
    return SPRTResult(decision, stop, cum, upper, lower)


# ============================================================================
# 2. mixture SPRT -- always-valid p-value and confidence sequence
# ============================================================================
@dataclass
class AlwaysValidResult:
    p_values: np.ndarray          # running always-valid p-value at each look
    effect: np.ndarray            # running effect estimate
    ci_low: np.ndarray            # confidence-sequence lower bound
    ci_high: np.ndarray           # confidence-sequence upper bound
    reject_index: int | None      # first index where p <= alpha, else None


def _msprt_log_lambda(theta_hat, v_n, tau2):
    """log of the mSPRT likelihood ratio against H0: theta = 0.

    Computed in log-space to avoid overflow when the ratio is astronomically
    large (which happens, legitimately, once an effect is obvious).
    """
    return 0.5 * np.log(v_n / (v_n + tau2)) + theta_hat**2 * tau2 / (
        2 * v_n * (v_n + tau2)
    )


def always_valid_test(
    effect_hat: np.ndarray,
    var_hat: np.ndarray,
    tau2: float,
    alpha: float = 0.05,
) -> AlwaysValidResult:
    """Always-valid p-values and confidence sequence from running estimates.

    Parameters
    ----------
    effect_hat : array of the running effect estimate (treatment - control) at
        each look.
    var_hat : array of the variance of that estimate at each look.
    tau2 : mixing variance of the mSPRT (the prior scale on the effect). Larger
        tau2 favours detecting larger effects. A reasonable default is the
        variance of the estimate at a small sample, or ``mde**2``.
    """
    effect_hat = np.asarray(effect_hat, dtype=float)
    var_hat = np.asarray(var_hat, dtype=float)

    log_lam = _msprt_log_lambda(effect_hat, var_hat, tau2)
    # p_raw = min(1, 1/Lambda) = min(1, exp(-log_lam)); computed without overflow.
    p_raw = np.where(log_lam <= 0.0, 1.0, np.exp(-np.minimum(log_lam, 700.0)))
    # Always-valid p-value is the running minimum (once you could reject, you can).
    p_running = np.minimum.accumulate(p_raw)

    # Confidence sequence: {theta0 : Lambda_n(theta0) < 1/alpha}. For the
    # Gaussian mixture this is a symmetric interval around the estimate.
    radius = np.sqrt(
        (2 * var_hat * (var_hat + tau2) / tau2)
        * (0.5 * np.log((var_hat + tau2) / var_hat) + np.log(1.0 / alpha))
    )
    ci_low = effect_hat - radius
    ci_high = effect_hat + radius

    reject_idx = None
    hits = np.where(p_running <= alpha)[0]
    if hits.size:
        reject_idx = int(hits[0])

    return AlwaysValidResult(p_running, effect_hat, ci_low, ci_high, reject_idx)


def always_valid_from_stream(
    stream,
    metric: Literal["binary", "continuous"] = "binary",
    tau2: float | None = None,
    alpha: float = 0.05,
    step: int = 1,
    min_samples: int = 50,
) -> AlwaysValidResult:
    """Convenience wrapper: run the always-valid test over a simulated stream.

    ``stream`` is the structured array produced by
    :func:`abtest.simulation.simulate_stream`. Running per-arm means and the
    variance of the difference estimate are computed cumulatively, then handed
    to :func:`always_valid_test`.

    ``min_samples`` is a warm-up: evaluations start only once each arm has this
    many observations. Peeking at a handful of users gives a degenerate variance
    estimate (for a binary metric ``p(1-p)`` collapses to 0 when every visitor
    so far behaved identically), so in practice sequential monitoring begins
    after a short warm-up.
    """
    arm = stream["arm"]
    val = stream["value"]

    is_t = arm == 1
    # Cumulative counts and sums per arm.
    n_t = np.cumsum(is_t)
    n_c = np.cumsum(~is_t)
    sum_t = np.cumsum(np.where(is_t, val, 0.0))
    sum_c = np.cumsum(np.where(~is_t, val, 0.0))
    sumsq_t = np.cumsum(np.where(is_t, val**2, 0.0))
    sumsq_c = np.cumsum(np.where(~is_t, val**2, 0.0))

    # Only evaluate once both arms are past the warm-up.
    valid = (n_t >= max(2, min_samples)) & (n_c >= max(2, min_samples))
    idx = np.where(valid)[0]
    if step > 1:
        idx = idx[::step]

    mean_t = sum_t[idx] / n_t[idx]
    mean_c = sum_c[idx] / n_c[idx]
    effect = mean_t - mean_c

    if metric == "binary":
        # Laplace-smoothed proportion variance so it never collapses to exactly 0.
        p_t = (sum_t[idx] + 1.0) / (n_t[idx] + 2.0)
        p_c = (sum_c[idx] + 1.0) / (n_c[idx] + 2.0)
        var_t = p_t * (1 - p_t)
        var_c = p_c * (1 - p_c)
    else:
        var_t = (sumsq_t[idx] - sum_t[idx] ** 2 / n_t[idx]) / (n_t[idx] - 1)
        var_c = (sumsq_c[idx] - sum_c[idx] ** 2 / n_c[idx]) / (n_c[idx] - 1)

    v_n = var_t / n_t[idx] + var_c / n_c[idx]
    v_n = np.maximum(v_n, 1e-12)

    if tau2 is None:
        # Default: mixing scale equal to the variance of the estimate at n~100,
        # a common heuristic that tunes the test for moderate effects.
        tau2 = float(np.median(v_n) * len(idx) / 100.0 + 1e-6)

    result = always_valid_test(effect, v_n, tau2, alpha)
    # Remap reject index back to the original stream order.
    if result.reject_index is not None:
        result = AlwaysValidResult(
            result.p_values,
            result.effect,
            result.ci_low,
            result.ci_high,
            int(idx[result.reject_index]),
        )
    return result


# ============================================================================
# 3. Group-sequential boundaries (Pocock / O'Brien-Fleming)
# ============================================================================
def _survival_after_boundaries(a: np.ndarray, grid_half_width: float, n_grid: int):
    """Armitage-McPherson-Rowe recursion.

    Given per-look boundaries ``a`` on the *score* scale S_k (where
    S_k = Z_k * sqrt(k) is a random walk of iid N(0,1) increments), return the
    total probability of ever crossing +/- a_k in K looks under H0. This is the
    achieved two-sided type-I error.

    The continuation density is propagated on a fixed grid and convolved with a
    unit-normal step at each look.
    """
    K = len(a)
    s = np.linspace(-grid_half_width, grid_half_width, n_grid)
    dx = s[1] - s[0]
    # Normal step kernel centred on the grid.
    kernel = stats.norm.pdf(np.arange(-(n_grid // 2), n_grid - n_grid // 2) * dx)
    kernel = kernel * dx  # discretise the density

    # Look 1: density is N(0,1); restrict to |s| < a_0.
    dens = stats.norm.pdf(s) * dx
    inside = np.abs(s) < a[0]
    survive_prev = dens[inside].sum()
    dens = np.where(inside, dens, 0.0)

    for k in range(1, K):
        # Convolve current continuation density with a unit-normal increment.
        conv = np.convolve(dens, kernel, mode="same")
        inside = np.abs(s) < a[k]
        survive = conv[inside].sum()
        dens = np.where(inside, conv, 0.0)
        survive_prev = survive

    total_alpha = 1.0 - survive_prev
    return float(total_alpha)


def sequential_alpha(
    z_boundaries: np.ndarray,
    n_grid: int = 2001,
    grid_scale: float = 8.0,
) -> float:
    """Achieved two-sided family-wise type-I error for given z-boundaries.

    ``z_boundaries[k]`` is the critical value on the standardized Z scale at
    look ``k+1`` (equally-spaced information). Used both to solve for and to
    verify boundaries.
    """
    z_boundaries = np.asarray(z_boundaries, dtype=float)
    K = len(z_boundaries)
    looks = np.arange(1, K + 1)
    a = z_boundaries * np.sqrt(looks)  # boundaries on the score scale S_k
    half_width = grid_scale * np.sqrt(K)
    return _survival_after_boundaries(a, half_width, n_grid)


@dataclass
class GroupSequentialDesign:
    shape: str
    K: int
    alpha: float
    z_boundaries: np.ndarray      # critical Z value at each look
    nominal_alpha: np.ndarray     # equivalent per-look two-sided p-value
    achieved_alpha: float         # family-wise error actually spent


def group_sequential_boundaries(
    K: int,
    alpha: float = 0.05,
    shape: Literal["pocock", "obf"] = "obf",
    n_grid: int = 2001,
    tol: float = 1e-4,
) -> GroupSequentialDesign:
    """Compute Pocock or O'Brien-Fleming boundaries for K equally-spaced looks.

    * Pocock: constant Z boundary at every look (spends alpha evenly -- easy to
      stop early but a stringent final look).
    * O'Brien-Fleming: very stringent early, relaxing to near the fixed-sample
      critical value at the end (spends little alpha early -- the popular
      default because the final analysis is barely penalised).

    The shape fixes the *relative* boundary heights; a single constant ``c`` is
    solved by bisection so the family-wise error equals ``alpha``.
    """
    looks = np.arange(1, K + 1)
    if shape == "pocock":
        shape_factor = np.ones(K)
    elif shape == "obf":
        shape_factor = np.sqrt(K / looks)
    else:  # pragma: no cover - guarded by Literal
        raise ValueError(f"unknown shape: {shape}")

    def achieved(c: float) -> float:
        return sequential_alpha(c * shape_factor, n_grid=n_grid)

    # Bisection on the constant c. Lower bound: fixed-sample critical value is a
    # floor; upper bound grows the boundary until error < alpha.
    lo, hi = 0.5, 8.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if achieved(mid) > alpha:
            lo = mid  # too much error -> raise the boundary
        else:
            hi = mid
        if hi - lo < tol:
            break
    c = 0.5 * (lo + hi)

    z_boundaries = c * shape_factor
    nominal_alpha = 2 * (1 - stats.norm.cdf(z_boundaries))
    achieved_alpha = sequential_alpha(z_boundaries, n_grid=n_grid)
    return GroupSequentialDesign(
        shape=shape,
        K=K,
        alpha=alpha,
        z_boundaries=z_boundaries,
        nominal_alpha=nominal_alpha,
        achieved_alpha=achieved_alpha,
    )

"""Tests for sequential / always-valid methods.

The headline properties:

* group-sequential boundaries spend exactly the requested alpha;
* the computed boundaries match published Pocock / O'Brien-Fleming values;
* naive repeated peeking with a fixed 1.96 cutoff inflates the error (the very
  problem sequential testing exists to fix);
* the always-valid test keeps its error under H0 while catching real effects.
"""

import numpy as np
import pytest

from abtest import (
    ExperimentConfig,
    MetricType,
    always_valid_from_stream,
    group_sequential_boundaries,
    sequential_alpha,
    simulate_stream,
    sprt_normal,
)
from abtest.simulation import simulate_continuous


# --- group sequential -------------------------------------------------------
def test_single_look_is_fixed_sample_critical_value():
    assert sequential_alpha(np.array([1.959964])) == pytest.approx(0.05, abs=1e-3)


@pytest.mark.parametrize("shape", ["pocock", "obf"])
@pytest.mark.parametrize("K", [2, 3, 5])
def test_boundaries_spend_target_alpha(shape, K):
    design = group_sequential_boundaries(K, alpha=0.05, shape=shape)
    assert design.achieved_alpha == pytest.approx(0.05, abs=2e-3)


def test_pocock_matches_reference_values():
    # Published Pocock two-sided boundary (alpha=0.05): constant per look.
    design = group_sequential_boundaries(5, alpha=0.05, shape="pocock")
    assert design.z_boundaries[-1] == pytest.approx(2.413, abs=0.02)
    # all looks share the same boundary
    assert np.allclose(design.z_boundaries, design.z_boundaries[0])


def test_obf_matches_reference_values():
    # O'Brien-Fleming: very high early, ~2.04 at the final look for K=5.
    design = group_sequential_boundaries(5, alpha=0.05, shape="obf")
    assert design.z_boundaries[-1] == pytest.approx(2.04, abs=0.03)
    assert design.z_boundaries[0] > design.z_boundaries[-1]  # stringent early


def test_naive_peeking_inflates_alpha():
    """Using 1.96 at every one of 5 looks blows past 5%."""
    inflated = sequential_alpha(np.array([1.959964] * 5))
    assert inflated > 0.10  # empirically ~0.14


# --- SPRT -------------------------------------------------------------------
def test_sprt_rejects_under_strong_alternative():
    # Data generated under H1 (mean 0.3); SPRT of H0:0 vs H1:0.3 should reject.
    exp = simulate_continuous(1, 4000, 0.0, 0.3, sigma=1.0, seed=1)
    res = sprt_normal(exp.treatment, mean_0=0.0, mean_1=0.3, sigma=1.0)
    assert res.decision == "reject_h0"
    assert res.stopping_index is not None


def test_sprt_accepts_under_null():
    exp = simulate_continuous(1, 4000, 0.0, 0.0, sigma=1.0, seed=2)
    res = sprt_normal(exp.treatment, mean_0=0.0, mean_1=0.3, sigma=1.0)
    assert res.decision == "accept_h0"


# --- always-valid (mSPRT) ---------------------------------------------------
def test_always_valid_ci_covers_and_shrinks():
    cfg = ExperimentConfig(
        metric_type=MetricType.BINARY,
        baseline=0.10,
        absolute_effect=0.03,
        n_control=8000,
        n_treatment=8000,
        seed=4,
    )
    stream = simulate_stream(cfg)
    res = always_valid_from_stream(stream, metric="binary", alpha=0.05, step=50)
    # final interval should contain the true effect 0.03
    assert res.ci_low[-1] <= 0.03 <= res.ci_high[-1]
    # confidence sequence tightens as data accrues
    assert (res.ci_high[-1] - res.ci_low[-1]) < (res.ci_high[0] - res.ci_low[0])


def test_always_valid_error_controlled_under_null():
    """Under H0, the chance of *ever* crossing stays near/below alpha."""
    alpha = 0.05
    false_positives, n_sims = 0, 200
    for s in range(n_sims):
        cfg = ExperimentConfig(
            metric_type=MetricType.BINARY,
            baseline=0.12,
            absolute_effect=0.0,
            n_control=3000,
            n_treatment=3000,
            seed=5000 + s,
        )
        stream = simulate_stream(cfg)
        res = always_valid_from_stream(stream, metric="binary", alpha=alpha, step=25)
        if res.reject_index is not None:
            false_positives += 1
    rate = false_positives / n_sims
    # anytime-valid guarantee: should be at or below alpha (allow noise headroom)
    assert rate <= 0.05 + 0.03

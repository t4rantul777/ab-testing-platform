"""Tests for the data simulator."""

import numpy as np

from abtest import ExperimentConfig, MetricType, simulate_experiment, simulate_stream
from abtest.simulation import simulate_binary, simulate_continuous


def test_binary_shapes_and_seed_reproducible():
    a = simulate_binary(1000, 1200, 0.1, 0.13, seed=1)
    b = simulate_binary(1000, 1200, 0.1, 0.13, seed=1)
    assert a.control.shape == (1000,)
    assert a.treatment.shape == (1200,)
    # same seed -> identical draws
    assert np.array_equal(a.control, b.control)
    assert np.array_equal(a.treatment, b.treatment)
    # values are 0/1 only
    assert set(np.unique(a.control)).issubset({0.0, 1.0})


def test_binary_recovers_rates():
    exp = simulate_binary(50_000, 50_000, 0.10, 0.14, seed=7)
    assert abs(exp.observed_control_mean - 0.10) < 0.005
    assert abs(exp.observed_treatment_mean - 0.14) < 0.005


def test_continuous_recovers_means():
    exp = simulate_continuous(40_000, 40_000, 10.0, 10.5, sigma=2.0, seed=3)
    assert abs(exp.observed_control_mean - 10.0) < 0.05
    assert abs(exp.observed_effect - 0.5) < 0.05


def test_simulate_experiment_relative_effect():
    cfg = ExperimentConfig(
        metric_type=MetricType.BINARY,
        baseline=0.20,
        relative_effect=0.10,  # +10% relative -> 0.22
        n_control=80_000,
        n_treatment=80_000,
        seed=11,
    )
    exp = simulate_experiment(cfg)
    assert abs(cfg.treatment_parameter() - 0.22) < 1e-9
    assert abs(exp.observed_treatment_mean - 0.22) < 0.006


def test_stream_arm_sizes_and_interleave():
    cfg = ExperimentConfig(
        metric_type=MetricType.BINARY,
        baseline=0.1,
        absolute_effect=0.02,
        n_control=3000,
        n_treatment=3000,
        seed=5,
    )
    stream = simulate_stream(cfg)
    assert stream.shape[0] == 6000
    assert int((stream["arm"] == 0).sum()) == 3000
    assert int((stream["arm"] == 1).sum()) == 3000
    # arms should be interleaved, not blocked: the first 3000 are not all one arm
    assert 0 < stream["arm"][:3000].sum() < 3000

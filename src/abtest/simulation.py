"""Synthetic experiment data generation.

Simulating data with a *known* ground truth is what lets us validate the whole
platform: if we inject a 3% lift we can check that the power analysis predicts
how often we detect it, and that the sequential tests keep their error rates.

Two shapes of output are produced:

* :func:`simulate_experiment` -- two fixed-size arrays (control / treatment),
  the classic "wait until the end, then run one test" setting.
* :func:`simulate_stream` -- an ordered stream of one observation at a time,
  each tagged with its arm. This is what sequential / always-valid methods
  consume, because they peek at the data as it accumulates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .datamodel import ExperimentConfig, MetricType


@dataclass
class SimulatedExperiment:
    """Container for a single simulated experiment (batch form)."""

    control: np.ndarray
    treatment: np.ndarray
    config: ExperimentConfig

    @property
    def observed_control_mean(self) -> float:
        return float(np.mean(self.control))

    @property
    def observed_treatment_mean(self) -> float:
        return float(np.mean(self.treatment))

    @property
    def observed_effect(self) -> float:
        return self.observed_treatment_mean - self.observed_control_mean


def _rng(seed: int | None) -> np.random.Generator:
    return np.random.default_rng(seed)


def simulate_binary(
    n_control: int,
    n_treatment: int,
    p_control: float,
    p_treatment: float,
    seed: int | None = None,
) -> SimulatedExperiment:
    """Simulate a conversion experiment as Bernoulli draws."""
    rng = _rng(seed)
    control = rng.binomial(1, p_control, size=n_control).astype(float)
    treatment = rng.binomial(1, p_treatment, size=n_treatment).astype(float)
    cfg = ExperimentConfig(
        metric_type=MetricType.BINARY,
        baseline=p_control,
        absolute_effect=p_treatment - p_control,
        n_control=n_control,
        n_treatment=n_treatment,
        seed=seed,
    )
    return SimulatedExperiment(control, treatment, cfg)


def simulate_continuous(
    n_control: int,
    n_treatment: int,
    mean_control: float,
    mean_treatment: float,
    sigma: float,
    seed: int | None = None,
) -> SimulatedExperiment:
    """Simulate a continuous-metric experiment as Normal draws."""
    rng = _rng(seed)
    control = rng.normal(mean_control, sigma, size=n_control)
    treatment = rng.normal(mean_treatment, sigma, size=n_treatment)
    cfg = ExperimentConfig(
        metric_type=MetricType.CONTINUOUS,
        baseline=mean_control,
        absolute_effect=mean_treatment - mean_control,
        sigma=sigma,
        n_control=n_control,
        n_treatment=n_treatment,
        seed=seed,
    )
    return SimulatedExperiment(control, treatment, cfg)


def simulate_experiment(config: ExperimentConfig) -> SimulatedExperiment:
    """Simulate an experiment straight from an :class:`ExperimentConfig`."""
    p_or_mu_c = config.baseline
    p_or_mu_t = config.treatment_parameter()
    if config.metric_type is MetricType.BINARY:
        return simulate_binary(
            config.n_control, config.n_treatment, p_or_mu_c, p_or_mu_t, config.seed
        )
    return simulate_continuous(
        config.n_control,
        config.n_treatment,
        p_or_mu_c,
        p_or_mu_t,
        config.sigma,
        config.seed,
    )


def simulate_stream(config: ExperimentConfig, seed: int | None = None):
    """Yield an interleaved stream of observations, one visitor at a time.

    Each element is ``(arm, value)`` where ``arm`` is ``"control"`` or
    ``"treatment"``. Visitors are randomised 50/50 into arms in arrival order,
    which mirrors how a real online experiment accumulates data and is exactly
    what a sequential test needs to evaluate at every interim look.

    Returns a structured numpy array with fields ``order``, ``arm`` (0=control,
    1=treatment) and ``value`` so it is cheap to slice cumulatively.
    """
    seed = config.seed if seed is None else seed
    rng = _rng(seed)
    total = config.n_control + config.n_treatment

    # Build the arm-assignment vector with the exact requested arm sizes, then
    # shuffle it so arrivals are interleaved rather than "all control first".
    arms = np.array([0] * config.n_control + [1] * config.n_treatment, dtype=np.int8)
    rng.shuffle(arms)

    p_or_mu_c = config.baseline
    p_or_mu_t = config.treatment_parameter()

    values = np.empty(total, dtype=float)
    is_treatment = arms == 1
    n_t = int(is_treatment.sum())
    n_c = total - n_t

    if config.metric_type is MetricType.BINARY:
        values[~is_treatment] = rng.binomial(1, p_or_mu_c, size=n_c)
        values[is_treatment] = rng.binomial(1, p_or_mu_t, size=n_t)
    else:
        values[~is_treatment] = rng.normal(p_or_mu_c, config.sigma, size=n_c)
        values[is_treatment] = rng.normal(p_or_mu_t, config.sigma, size=n_t)

    stream = np.empty(
        total,
        dtype=[("order", np.int64), ("arm", np.int8), ("value", np.float64)],
    )
    stream["order"] = np.arange(total)
    stream["arm"] = arms
    stream["value"] = values
    return stream

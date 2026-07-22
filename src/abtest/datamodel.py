"""Core data structures shared across the A/B testing platform.

Everything here is intentionally dependency-light (only the standard library)
so the data model can be imported by the statistics modules, the storage layer
and the Streamlit app without creating import cycles.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class MetricType(str, Enum):
    """The kind of metric an experiment measures.

    ``BINARY``     -- a conversion / click / signup flag (0 or 1 per user).
    ``CONTINUOUS`` -- a numeric value per user (revenue, session length, ...).
    """

    BINARY = "binary"
    CONTINUOUS = "continuous"


class Alternative(str, Enum):
    """Direction of the alternative hypothesis."""

    TWO_SIDED = "two-sided"
    LARGER = "larger"
    SMALLER = "smaller"


@dataclass(frozen=True)
class ExperimentConfig:
    """Declarative description of an experiment to simulate / analyse.

    For a binary metric ``baseline`` is the control conversion rate and the
    treatment rate is derived from ``absolute_effect`` / ``relative_effect``.
    For a continuous metric ``baseline`` is the control mean and ``sigma`` is
    the (shared) standard deviation.
    """

    name: str = "experiment"
    metric_type: MetricType = MetricType.BINARY
    baseline: float = 0.10
    # Exactly one of the two effect specifications is used. ``relative_effect``
    # takes precedence when it is non-zero (it is the more common way an analyst
    # thinks: "a 5% uplift"). ``absolute_effect`` is an additive shift.
    relative_effect: float = 0.0
    absolute_effect: float = 0.0
    sigma: float = 1.0  # only used for continuous metrics
    n_control: int = 5_000
    n_treatment: int = 5_000
    alpha: float = 0.05
    power: float = 0.80
    alternative: Alternative = Alternative.TWO_SIDED
    seed: Optional[int] = 42

    # ------------------------------------------------------------------
    def treatment_parameter(self) -> float:
        """Return the treatment-arm parameter (rate or mean).

        Relative effect is applied multiplicatively, absolute effect additively.
        """
        value = self.baseline
        if self.relative_effect:
            value = self.baseline * (1.0 + self.relative_effect)
        value = value + self.absolute_effect
        return value

    def true_absolute_effect(self) -> float:
        """The ground-truth absolute difference (treatment - control)."""
        return self.treatment_parameter() - self.baseline

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["metric_type"] = self.metric_type.value
        d["alternative"] = self.alternative.value
        return d


@dataclass
class TestResult:
    """Outcome of a single statistical test in a tidy, serialisable form."""

    test_name: str
    statistic: float
    p_value: float
    effect_estimate: float
    ci_low: float
    ci_high: float
    alpha: float
    significant: bool
    n_control: int
    n_treatment: int
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        verdict = "SIGNIFICANT" if self.significant else "not significant"
        return (
            f"{self.test_name}: effect={self.effect_estimate:+.4g} "
            f"[{self.ci_low:+.4g}, {self.ci_high:+.4g}], "
            f"p={self.p_value:.4g} -> {verdict} at alpha={self.alpha:g}"
        )

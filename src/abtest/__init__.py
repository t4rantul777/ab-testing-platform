"""abtest -- a self-contained A/B testing statistical-significance platform.

Public API is intentionally flat so notebooks and the Streamlit app can do::

    from abtest import (
        ExperimentConfig, MetricType, simulate_experiment,
        analyze, group_sequential_boundaries, always_valid_from_stream,
    )
"""

from __future__ import annotations

from .datamodel import (
    Alternative,
    ExperimentConfig,
    MetricType,
    TestResult,
)
from .simulation import (
    SimulatedExperiment,
    simulate_binary,
    simulate_continuous,
    simulate_experiment,
    simulate_stream,
)
from .frequentist import (
    analyze,
    chi_square_test,
    cohens_d,
    cohens_h,
    two_proportion_ztest,
    welch_ttest,
)
from .power import (
    PowerResult,
    mde_means,
    mde_proportions,
    power_curve_by_effect,
    power_curve_by_n,
    power_means,
    power_proportions,
    sample_size_means,
    sample_size_proportions,
)
from .sequential import (
    AlwaysValidResult,
    GroupSequentialDesign,
    SPRTResult,
    always_valid_from_stream,
    always_valid_test,
    group_sequential_boundaries,
    sequential_alpha,
    sprt_normal,
)
from .storage import ABTestStore

__version__ = "0.1.0"

__all__ = [
    "Alternative",
    "ExperimentConfig",
    "MetricType",
    "TestResult",
    "SimulatedExperiment",
    "simulate_binary",
    "simulate_continuous",
    "simulate_experiment",
    "simulate_stream",
    "analyze",
    "chi_square_test",
    "cohens_d",
    "cohens_h",
    "two_proportion_ztest",
    "welch_ttest",
    "PowerResult",
    "mde_means",
    "mde_proportions",
    "power_curve_by_effect",
    "power_curve_by_n",
    "power_means",
    "power_proportions",
    "sample_size_means",
    "sample_size_proportions",
    "AlwaysValidResult",
    "GroupSequentialDesign",
    "SPRTResult",
    "always_valid_from_stream",
    "always_valid_test",
    "group_sequential_boundaries",
    "sequential_alpha",
    "sprt_normal",
    "ABTestStore",
    "__version__",
]

"""End-to-end tour of the abtest API in ~40 lines.

    python examples/quickstart.py
"""

from abtest import (
    ExperimentConfig,
    MetricType,
    always_valid_from_stream,
    analyze,
    group_sequential_boundaries,
    sample_size_proportions,
    sequential_alpha,
    simulate_experiment,
    simulate_stream,
)

# 1) Design: how many users to detect a +2pp lift on a 10% baseline at 80% power?
n = sample_size_proportions(p1=0.10, mde_absolute=0.02, alpha=0.05, power=0.80)
print(f"1. Sample size for +2pp @ 80% power: {int(n):,} per arm")

# 2) Simulate an experiment with that design and a real +2pp effect.
cfg = ExperimentConfig(
    name="quickstart", metric_type=MetricType.BINARY,
    baseline=0.10, absolute_effect=0.02,
    n_control=int(n), n_treatment=int(n), seed=7,
)
exp = simulate_experiment(cfg)

# 3) Fixed-horizon significance test.
res = analyze(exp.control, exp.treatment, MetricType.BINARY)
print("2. Fixed-horizon test:", res.summary())

# 4) The peeking problem, and the group-sequential fix.
naive = sequential_alpha([1.96] * 5)
obf = group_sequential_boundaries(K=5, alpha=0.05, shape="obf")
print(f"3. Peeking 5x with 1.96 -> real error {naive:.1%} (not 5%!)")
print(f"   O'Brien-Fleming boundaries {obf.z_boundaries.round(2)} "
      f"spend exactly {obf.achieved_alpha:.3f}")

# 5) Always-valid inference over a live stream: stop as early as data allows.
#    (We provision generous traffic to show how much earlier we can stop.)
stream_cfg = ExperimentConfig(
    metric_type=MetricType.BINARY, baseline=0.10, absolute_effect=0.02,
    n_control=25_000, n_treatment=25_000, seed=7,
)
stream = simulate_stream(stream_cfg)
av = always_valid_from_stream(stream, metric="binary", alpha=0.05, step=50)
total = stream_cfg.n_control + stream_cfg.n_treatment
if av.reject_index is not None:
    print(f"4. Always-valid: significant after {av.reject_index:,} obs "
          f"({1 - av.reject_index / total:.0%} fewer than the full {total:,})")
else:
    print("4. Always-valid: not significant within the horizon")

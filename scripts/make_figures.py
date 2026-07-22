"""Render the figures used in the README straight from the library.

Running this file is itself a smoke-test: every chart is produced by calling the
public API, so if the figures render, the pipeline works. A colourblind-safe
palette (Okabe-Ito) is used throughout.

    python scripts/make_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from abtest import (
    ExperimentConfig,
    MetricType,
    always_valid_from_stream,
    group_sequential_boundaries,
    power_curve_by_n,
    sample_size_proportions,
    simulate_binary,
    simulate_stream,
    two_proportion_ztest,
)

# --- Okabe-Ito colourblind-safe palette -------------------------------------
OKABE = {
    "black": "#000000",
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
}
GRID = "#D9D9D9"

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)

IMG = Path(__file__).resolve().parent.parent / "docs" / "img"
IMG.mkdir(parents=True, exist_ok=True)


def fig_power_curves():
    """Power vs sample size for several true effects, with the MDE marker."""
    p1 = 0.10
    n_grid = np.linspace(200, 40_000, 120)
    effects = [0.005, 0.01, 0.02, 0.03]
    colors = [OKABE["sky"], OKABE["green"], OKABE["blue"], OKABE["vermillion"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    for eff, c in zip(effects, colors):
        power = power_curve_by_n(p1, eff, n_grid, alpha=0.05, metric="binary")
        ax.plot(n_grid, power, color=c, lw=2.4, label=f"+{eff*100:.1f} pp lift")

    ax.axhline(0.80, color=OKABE["black"], ls="--", lw=1.2)
    ax.text(40_000, 0.815, "80% power", ha="right", va="bottom", fontsize=10)

    n80 = sample_size_proportions(p1, 0.02, alpha=0.05, power=0.80)
    ax.axvline(n80, color=OKABE["orange"], ls=":", lw=1.6)
    ax.text(n80 + 400, 0.15, f"n={int(n80):,}/arm\nfor +2pp @ 80%",
            fontsize=9, color=OKABE["orange"])

    ax.set_xlabel("Sample size per arm")
    ax.set_ylabel("Power (P detect true effect)")
    ax.set_title("Power vs sample size  (baseline rate = 10%)")
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(IMG / "power_curves.png")
    plt.close(fig)


def fig_sequential_boundaries():
    """Pocock vs O'Brien-Fleming z-boundaries against the naive 1.96 line."""
    K = 8
    pocock = group_sequential_boundaries(K, alpha=0.05, shape="pocock")
    obf = group_sequential_boundaries(K, alpha=0.05, shape="obf")
    looks = np.arange(1, K + 1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(looks, obf.z_boundaries, "o-", color=OKABE["blue"], lw=2.4,
            label=f"O'Brien-Fleming (spends {obf.achieved_alpha:.3f})")
    ax.plot(looks, pocock.z_boundaries, "s-", color=OKABE["vermillion"], lw=2.4,
            label=f"Pocock (spends {pocock.achieved_alpha:.3f})")
    ax.axhline(1.96, color=OKABE["black"], ls="--", lw=1.4,
               label="Naive 1.96 (true error 14%)")

    ax.set_xlabel("Interim look number (of 8)")
    ax.set_ylabel("Rejection boundary on the Z scale")
    ax.set_title("Group-sequential boundaries keep family-wise error at 5%")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(IMG / "sequential_boundaries.png")
    plt.close(fig)


def fig_always_valid():
    """Always-valid confidence sequence over a live experiment stream."""
    cfg = ExperimentConfig(
        metric_type=MetricType.BINARY, baseline=0.10, absolute_effect=0.02,
        n_control=30_000, n_treatment=30_000, seed=20,
    )
    stream = simulate_stream(cfg)
    res = always_valid_from_stream(stream, metric="binary", alpha=0.05, step=100)

    n_axis = np.arange(len(res.effect)) * 100 + 100
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.fill_between(n_axis, res.ci_low, res.ci_high, color=OKABE["sky"],
                    alpha=0.35, label="95% confidence sequence")
    ax.plot(n_axis, res.effect, color=OKABE["blue"], lw=2.0, label="Effect estimate")
    ax.axhline(0.02, color=OKABE["green"], ls="-", lw=1.6, label="True effect (+2pp)")
    ax.axhline(0.0, color=OKABE["black"], ls="--", lw=1.0)

    if res.reject_index is not None:
        ax.axvline(res.reject_index, color=OKABE["vermillion"], ls=":", lw=1.8)
        ax.text(res.reject_index, 0.055,
                f"stop early\n(n={res.reject_index:,})",
                color=OKABE["vermillion"], fontsize=9, ha="left")

    ax.set_xlabel("Total observations seen")
    ax.set_ylabel("Treatment - control conversion rate")
    ax.set_title("Always-valid inference: peek any time, stop when the band clears 0")
    ax.legend(frameon=False, loc="upper right")
    ax.set_ylim(-0.02, 0.07)
    fig.tight_layout()
    fig.savefig(IMG / "always_valid.png")
    plt.close(fig)


def fig_experiment_result():
    """A single simulated experiment: rates with CIs on the difference."""
    exp = simulate_binary(8000, 8000, 0.10, 0.123, seed=42)
    res = two_proportion_ztest(exp.control, exp.treatment)
    p_c = res.extra["rate_control"]
    p_t = res.extra["rate_treatment"]

    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))

    axes[0].bar(["Control", "Treatment"], [p_c, p_t],
                color=[OKABE["sky"], OKABE["vermillion"]], width=0.6)
    axes[0].set_ylabel("Conversion rate")
    axes[0].set_title("Observed conversion by arm")
    for i, v in enumerate([p_c, p_t]):
        axes[0].text(i, v + 0.002, f"{v*100:.2f}%", ha="center", fontsize=10)
    axes[0].set_ylim(0, max(p_c, p_t) * 1.25)

    axes[1].errorbar([res.effect_estimate], [0],
                     xerr=[[res.effect_estimate - res.ci_low],
                           [res.ci_high - res.effect_estimate]],
                     fmt="o", color=OKABE["blue"], capsize=6, markersize=9, lw=2)
    axes[1].axvline(0, color=OKABE["black"], ls="--", lw=1.2)
    axes[1].set_yticks([])
    axes[1].set_xlabel("Difference in rates (treatment - control)")
    verdict = "significant" if res.significant else "not significant"
    axes[1].set_title(f"95% CI on the lift  (p={res.p_value:.4f}, {verdict})")

    fig.tight_layout()
    fig.savefig(IMG / "experiment_result.png")
    plt.close(fig)


def main():
    fig_power_curves()
    fig_sequential_boundaries()
    fig_always_valid()
    fig_experiment_result()
    print("figures written to", IMG)


if __name__ == "__main__":
    main()

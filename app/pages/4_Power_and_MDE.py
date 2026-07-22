"""Power & MDE page -- experiment design and planning."""

from __future__ import annotations

import theme
import numpy as np
import plotly.graph_objects as go
import streamlit as st

theme.page_config("Power & MDE", "⚡")

from abtest import (  # noqa: E402
    mde_means,
    mde_proportions,
    power_curve_by_effect,
    power_curve_by_n,
    power_means,
    power_proportions,
    sample_size_means,
    sample_size_proportions,
)

st.title("⚡ Power & Minimum Detectable Effect")
st.caption("Plan the experiment: how many users, how much power, what is detectable.")

metric = st.sidebar.radio("Metric", ["Binary", "Continuous"])
is_binary = metric == "Binary"
alpha = st.sidebar.select_slider("α", [0.01, 0.05, 0.10], value=0.05)
power_target = st.sidebar.slider("Target power", 0.5, 0.99, 0.80, 0.01)

if is_binary:
    baseline = st.sidebar.slider("Baseline rate", 0.01, 0.6, 0.10, 0.01)
    mde_input = st.sidebar.slider("Effect to detect (pp)", 0.005, 0.10, 0.02, 0.005)
    sigma = 1.0
else:
    baseline = 0.0
    mde_input = st.sidebar.number_input("Mean difference to detect", 0.01, 10.0, 0.4, 0.05)
    sigma = st.sidebar.number_input("Std. deviation", 0.1, 20.0, 2.0, 0.1)

st.subheader("Design summary")
if is_binary:
    n_needed = sample_size_proportions(baseline, mde_input, alpha, power_target)
    achieved = power_proportions(baseline, baseline + mde_input, n_needed, alpha)
    mde_at_n = mde_proportions(baseline, n_needed, alpha, power_target)
else:
    n_needed = sample_size_means(mde_input, sigma, alpha, power_target)
    achieved = power_means(mde_input, sigma, n_needed, alpha)
    mde_at_n = mde_means(sigma, n_needed, alpha, power_target)

c1, c2, c3 = st.columns(3)
c1.metric("Users per arm", f"{int(n_needed):,}")
c2.metric("Power at that n", f"{achieved*100:.1f}%")
c3.metric("Total users", f"{2*int(n_needed):,}")

st.divider()

left, right = st.columns(2)

with left:
    st.markdown("**Power vs sample size** (fixed effect)")
    n_grid = np.linspace(200, max(4 * n_needed, 5000), 120)
    curve = power_curve_by_n(baseline, mde_input, n_grid, alpha,
                             "binary" if is_binary else "continuous", sigma)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=n_grid, y=curve, line=dict(color=theme.ACCENT, width=3),
                             name="power"))
    fig.add_hline(y=power_target, line_dash="dash", line_color="black",
                  annotation_text=f"{power_target*100:.0f}% power")
    fig.add_vline(x=n_needed, line_dash="dot", line_color=theme.OKABE["orange"],
                  annotation_text=f"n={int(n_needed):,}")
    fig.update_xaxes(title="Users per arm")
    fig.update_yaxes(title="Power", range=[0, 1.02])
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("**Power vs true effect** (fixed n)")
    if is_binary:
        eff_grid = np.linspace(0.002, 0.08, 100)
    else:
        eff_grid = np.linspace(0.05, 2 * mde_input + 0.5, 100)
    curve2 = power_curve_by_effect(baseline, eff_grid, n_needed, alpha,
                                   "binary" if is_binary else "continuous", sigma)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=eff_grid, y=curve2, line=dict(color=theme.OKABE["green"], width=3),
                              name="power"))
    fig2.add_hline(y=power_target, line_dash="dash", line_color="black")
    fig2.add_vline(x=mde_at_n, line_dash="dot", line_color=theme.TREATMENT,
                   annotation_text=f"MDE={mde_at_n:.4g}")
    fig2.update_xaxes(title="True effect size")
    fig2.update_yaxes(title="Power", range=[0, 1.02])
    theme.apply_plotly_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

st.info(
    f"With **{int(n_needed):,}** users per arm at α={alpha} and "
    f"{power_target*100:.0f}% power, the smallest reliably detectable effect "
    f"is **{mde_at_n:.4g}**."
)

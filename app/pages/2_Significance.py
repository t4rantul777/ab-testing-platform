"""Significance page -- fixed-horizon tests with CIs and effect sizes."""

from __future__ import annotations

import theme
import numpy as np
import plotly.graph_objects as go
import streamlit as st

theme.page_config("Significance", "📊")

from abtest import (  # noqa: E402
    MetricType,
    chi_square_test,
    two_proportion_ztest,
    welch_ttest,
)
from abtest.datamodel import Alternative

st.title("📊 Significance Calculator")
st.caption("The classic fixed-horizon analysis you run once, at the planned sample size.")

alt_label = st.sidebar.selectbox("Alternative hypothesis",
                                 ["two-sided", "larger", "smaller"])
alt = Alternative(alt_label)
alpha = st.sidebar.select_slider("Significance level α", [0.01, 0.05, 0.10], value=0.05)

mode = st.radio("Input", ["Use simulated experiment", "Enter summary numbers"],
                horizontal=True)

if mode == "Use simulated experiment":
    exp = st.session_state.get("experiment")
    if not exp:
        st.warning("No experiment in memory yet — open the **Simulator** page first.")
        st.stop()
    cfg = exp["config"]
    control, treatment = exp["control"], exp["treatment"]
    is_binary = cfg.metric_type is MetricType.BINARY
    st.caption(f"Using **{cfg.name}** — {cfg.metric_type.value}, "
               f"{cfg.n_control:,} users/arm.")
else:
    is_binary = st.radio("Metric", ["Binary", "Continuous"], horizontal=True) == "Binary"
    if is_binary:
        colc, colt = st.columns(2)
        n_c = colc.number_input("Control users", 1, 10_000_000, 8000)
        x_c = colc.number_input("Control conversions", 0, 10_000_000, 800)
        n_t = colt.number_input("Treatment users", 1, 10_000_000, 8000)
        x_t = colt.number_input("Treatment conversions", 0, 10_000_000, 920)
        control = np.array([1] * int(x_c) + [0] * int(n_c - x_c), dtype=float)
        treatment = np.array([1] * int(x_t) + [0] * int(n_t - x_t), dtype=float)
    else:
        st.info("For continuous input from summary stats, use the Simulator page "
                "(raw samples are needed for a t-test).")
        st.stop()

if is_binary:
    z = two_proportion_ztest(control, treatment, alpha=alpha, alternative=alt)
    chi = chi_square_test(control, treatment, alpha=alpha)

    st.subheader("Two-proportion z-test")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Control rate", f"{z.extra['rate_control']*100:.2f}%")
    c2.metric("Treatment rate", f"{z.extra['rate_treatment']*100:.2f}%")
    c3.metric("Absolute lift", f"{z.effect_estimate*100:+.2f} pp")
    c4.metric("Relative lift", f"{z.extra['relative_lift']*100:+.1f}%")

    d1, d2, d3 = st.columns(3)
    d1.metric("z-statistic", f"{z.statistic:.3f}")
    d2.metric("p-value", f"{z.p_value:.4g}")
    d3.metric("Significant?", "✅ yes" if z.significant else "❌ no")
    st.caption(f"95% CI on the lift: [{z.ci_low:+.4g}, {z.ci_high:+.4g}] · "
               f"Cohen's h = {z.extra['cohens_h']:.3f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[z.effect_estimate], y=[0], mode="markers", marker=dict(size=14, color=theme.ACCENT),
        error_x=dict(type="data",
                     array=[z.ci_high - z.effect_estimate],
                     arrayminus=[z.effect_estimate - z.ci_low], color=theme.ACCENT),
        name="Effect ± 95% CI"))
    fig.add_vline(x=0, line_dash="dash", line_color="black")
    fig.update_yaxes(showticklabels=False)
    fig.update_xaxes(title="Difference in conversion rate")
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Chi-square test (equivalent to the two-sided z-test)"):
        st.write(f"χ² = {chi.statistic:.4f}, dof = {chi.extra['dof']}, "
                 f"p = {chi.p_value:.4g}")
        st.caption("Without a continuity correction, χ² equals z² exactly — a "
                   "useful cross-check that the implementation is correct.")
else:
    t = welch_ttest(control, treatment, alpha=alpha, alternative=alt)
    st.subheader("Welch's t-test (unequal variances)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean difference", f"{t.effect_estimate:+.4g}")
    c2.metric("t-statistic", f"{t.statistic:.3f}")
    c3.metric("p-value", f"{t.p_value:.4g}")
    st.caption(f"95% CI: [{t.ci_low:+.4g}, {t.ci_high:+.4g}] · "
               f"df = {t.extra['df']:.1f} · Cohen's d = {t.extra['cohens_d']:.3f}")
    st.metric("Significant?", "✅ yes" if t.significant else "❌ no")

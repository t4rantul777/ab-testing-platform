"""Simulator page -- create an experiment with a known ground truth."""

from __future__ import annotations

import theme
import numpy as np
import plotly.graph_objects as go
import streamlit as st

theme.page_config("Simulator", "🧪")

from abtest import (  # noqa: E402
    ABTestStore,
    ExperimentConfig,
    MetricType,
    analyze,
    simulate_experiment,
)

st.title("🧪 Experiment Simulator")
st.caption("Generate data with a known effect so every downstream method can be checked.")

with st.sidebar:
    st.header("Design")
    name = st.text_input("Experiment name", "checkout-cta")
    metric = st.radio("Metric type", ["Binary (conversion)", "Continuous (revenue)"])
    is_binary = metric.startswith("Binary")

    if is_binary:
        baseline = st.slider("Baseline conversion rate", 0.01, 0.6, 0.10, 0.01)
        effect_mode = st.radio("Effect as", ["Absolute (pp)", "Relative (%)"])
        if effect_mode.startswith("Absolute"):
            abs_eff = st.slider("Absolute lift (pp)", -0.10, 0.10, 0.02, 0.005)
            rel_eff = 0.0
        else:
            rel_eff = st.slider("Relative lift", -0.5, 0.5, 0.10, 0.01)
            abs_eff = 0.0
        sigma = 1.0
    else:
        baseline = st.number_input("Control mean", value=10.0, step=0.5)
        abs_eff = st.number_input("Absolute mean lift", value=0.4, step=0.1)
        rel_eff = 0.0
        sigma = st.number_input("Std. deviation (shared)", value=2.0, min_value=0.1, step=0.1)

    n_control = st.number_input("Users per arm", 100, 500_000, 8_000, step=500)
    seed = st.number_input("Random seed", 0, 10_000, 42, step=1)
    alpha = st.select_slider("Significance level α", [0.01, 0.05, 0.10], value=0.05)

cfg = ExperimentConfig(
    name=name,
    metric_type=MetricType.BINARY if is_binary else MetricType.CONTINUOUS,
    baseline=baseline,
    absolute_effect=abs_eff,
    relative_effect=rel_eff,
    sigma=sigma,
    n_control=int(n_control),
    n_treatment=int(n_control),
    alpha=alpha,
    seed=int(seed),
)

exp = simulate_experiment(cfg)
result = analyze(exp.control, exp.treatment, cfg.metric_type, alpha=alpha)

# Persist to session for other pages.
st.session_state["experiment"] = {
    "config": cfg,
    "control": exp.control,
    "treatment": exp.treatment,
}

st.subheader("Ground truth vs observed")
c1, c2, c3, c4 = st.columns(4)
c1.metric("True effect", f"{cfg.true_absolute_effect():+.4g}")
c2.metric("Observed effect", f"{exp.observed_effect:+.4g}")
c3.metric("Control (obs.)", f"{exp.observed_control_mean:.4g}")
c4.metric("Treatment (obs.)", f"{exp.observed_treatment_mean:.4g}")

st.subheader("Distribution by arm")
fig = go.Figure()
if is_binary:
    rates = [exp.observed_control_mean, exp.observed_treatment_mean]
    fig.add_bar(x=["Control", "Treatment"], y=rates,
                marker_color=[theme.CONTROL, theme.TREATMENT],
                text=[f"{r*100:.2f}%" for r in rates], textposition="outside")
    fig.update_yaxes(title="Conversion rate")
else:
    fig.add_histogram(x=exp.control, name="Control", opacity=0.6,
                      marker_color=theme.CONTROL, nbinsx=60)
    fig.add_histogram(x=exp.treatment, name="Treatment", opacity=0.6,
                      marker_color=theme.TREATMENT, nbinsx=60)
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title="Metric value")
theme.apply_plotly_theme(fig)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Primary test result")
st.code(result.summary(), language="text")
r1, r2, r3 = st.columns(3)
r1.metric("p-value", f"{result.p_value:.4g}")
r2.metric("Effect estimate", f"{result.effect_estimate:+.4g}")
r3.metric("Significant?", "✅ yes" if result.significant else "❌ no")

if not np.isnan(result.ci_low):
    st.caption(
        f"95% CI on the effect: [{result.ci_low:+.4g}, {result.ci_high:+.4g}]"
    )

if st.button("💾 Save this experiment to history"):
    with ABTestStore(theme.DB_PATH) as store:
        eid = store.save_experiment(cfg)
        store.save_result(eid, result)
    st.success(f"Saved experiment #{eid} to the local database.")

st.info("Now open **Sequential** or **Power & MDE** — they reuse this experiment.")

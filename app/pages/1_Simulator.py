"""Simulator page -- create an experiment with a known ground truth."""

from __future__ import annotations

import theme
import numpy as np
import plotly.graph_objects as go
import streamlit as st

theme.page_config("Simulator", "🧪")

from i18n import language_selector, t  # noqa: E402
from abtest import (  # noqa: E402
    ABTestStore,
    ExperimentConfig,
    MetricType,
    analyze,
    simulate_experiment,
)

language_selector()

st.title(t("sim_title"))
st.caption(t("sim_caption"))

with st.sidebar:
    st.header(t("sim_design"))
    name = st.text_input(t("sim_name"), "checkout-cta")
    metric_opts = [t("metric_binary"), t("metric_continuous")]
    metric = st.radio(t("sim_metric_type"), metric_opts)
    is_binary = metric == metric_opts[0]

    if is_binary:
        baseline = st.slider(t("sim_baseline_rate"), 0.01, 0.6, 0.10, 0.01)
        eff_opts = [t("sim_effect_abs"), t("sim_effect_rel")]
        effect_mode = st.radio(t("sim_effect_as"), eff_opts)
        if effect_mode == eff_opts[0]:
            abs_eff = st.slider(t("sim_abs_lift"), -0.10, 0.10, 0.02, 0.005)
            rel_eff = 0.0
        else:
            rel_eff = st.slider(t("sim_rel_lift"), -0.5, 0.5, 0.10, 0.01)
            abs_eff = 0.0
        sigma = 1.0
    else:
        baseline = st.number_input(t("sim_control_mean"), value=10.0, step=0.5)
        abs_eff = st.number_input(t("sim_abs_mean_lift"), value=0.4, step=0.1)
        rel_eff = 0.0
        sigma = st.number_input(t("sim_sigma"), value=2.0, min_value=0.1, step=0.1)

    n_control = st.number_input(t("sim_users"), 100, 500_000, 8_000, step=500)
    seed = st.number_input(t("sim_seed"), 0, 10_000, 42, step=1)
    alpha = st.select_slider(t("alpha"), [0.01, 0.05, 0.10], value=0.05)

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

st.subheader(t("sim_sub_truth"))
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("sim_true_effect"), f"{cfg.true_absolute_effect():+.4g}")
c2.metric(t("sim_obs_effect"), f"{exp.observed_effect:+.4g}")
c3.metric(t("sim_control_obs"), f"{exp.observed_control_mean:.4g}")
c4.metric(t("sim_treatment_obs"), f"{exp.observed_treatment_mean:.4g}")

st.subheader(t("sim_sub_dist"))
fig = go.Figure()
if is_binary:
    rates = [exp.observed_control_mean, exp.observed_treatment_mean]
    fig.add_bar(x=[t("control"), t("treatment")], y=rates,
                marker_color=[theme.CONTROL, theme.TREATMENT],
                text=[f"{r*100:.2f}%" for r in rates], textposition="outside")
    fig.update_yaxes(title=t("sim_conv_rate"))
else:
    fig.add_histogram(x=exp.control, name=t("control"), opacity=0.6,
                      marker_color=theme.CONTROL, nbinsx=60)
    fig.add_histogram(x=exp.treatment, name=t("treatment"), opacity=0.6,
                      marker_color=theme.TREATMENT, nbinsx=60)
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title=t("sim_metric_value"))
theme.apply_plotly_theme(fig)
st.plotly_chart(fig, width='stretch')

st.subheader(t("sim_sub_result"))
st.code(result.summary(), language="text")
r1, r2, r3 = st.columns(3)
r1.metric(t("p_value"), f"{result.p_value:.4g}")
r2.metric(t("sim_effect_est"), f"{result.effect_estimate:+.4g}")
r3.metric(t("significant_q"), t("yes") if result.significant else t("no"))

if not np.isnan(result.ci_low):
    st.caption(t("sim_ci_effect", lo=f"{result.ci_low:+.4g}", hi=f"{result.ci_high:+.4g}"))

if st.button(t("sim_save_btn")):
    with ABTestStore(theme.DB_PATH) as store:
        eid = store.save_experiment(cfg)
        store.save_result(eid, result)
    st.success(t("sim_saved", eid=eid))

st.info(t("sim_next"))

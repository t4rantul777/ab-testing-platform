"""Sequential testing page -- the headline feature."""

from __future__ import annotations

import theme
import numpy as np
import plotly.graph_objects as go
import streamlit as st

theme.page_config("Sequential", "⏱️")

from i18n import language_selector, t  # noqa: E402
from abtest import (  # noqa: E402
    ExperimentConfig,
    MetricType,
    always_valid_from_stream,
    group_sequential_boundaries,
    sequential_alpha,
    simulate_stream,
    sprt_normal,
)

language_selector()

st.title(t("seq_title"))
st.caption(t("seq_caption"))

tab1, tab2, tab3 = st.tabs([t("seq_tab_group"), t("seq_tab_av"), t("seq_tab_sprt")])

# ---------------------------------------------------------------- group seq.
with tab1:
    st.markdown(t("seq_group_md"))
    c1, c2, c3 = st.columns(3)
    K = c1.slider(t("seq_K"), 2, 12, 5)
    alpha = c2.select_slider("α", [0.01, 0.05, 0.10], value=0.05)
    shape = c3.radio(t("seq_shape"), ["obf", "pocock"],
                     format_func=lambda s: "O'Brien-Fleming" if s == "obf" else "Pocock")

    design = group_sequential_boundaries(K, alpha=alpha, shape=shape)
    naive = sequential_alpha(np.array([1.959964] * K)) if alpha == 0.05 else None

    looks = np.arange(1, K + 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=looks, y=design.z_boundaries, mode="lines+markers",
                             line=dict(color=theme.ACCENT, width=3), name=t("seq_bound_name")))
    fig.add_hline(y=1.959964, line_dash="dash", line_color="black",
                  annotation_text=t("seq_naive196"))
    fig.update_xaxes(title=t("seq_look_axis"))
    fig.update_yaxes(title=t("seq_bound_axis"))
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, width='stretch')

    m1, m2 = st.columns(2)
    m1.metric(t("seq_spent"), f"{design.achieved_alpha:.4f}", help=t("seq_spent_help"))
    if naive is not None:
        m2.metric(t("seq_naive_metric"), f"{naive:.3f}",
                  delta=t("seq_over_target", d=f"{(naive-alpha):.3f}"),
                  delta_color="inverse")

    st.dataframe(
        {
            t("seq_col_look"): looks,
            t("seq_col_bound"): np.round(design.z_boundaries, 4),
            t("seq_col_nominal"): np.round(design.nominal_alpha, 5),
        },
        width='stretch', hide_index=True,
    )

# ---------------------------------------------------------------- always-valid
with tab2:
    st.markdown(t("seq_av_md"))
    exp = st.session_state.get("experiment")
    cola, colb, colc = st.columns(3)
    base = cola.number_input(t("seq_av_baseline"), 0.01, 0.6,
                             float(exp["config"].baseline) if exp else 0.10, 0.01)
    eff = colb.number_input(t("seq_av_lift"), -0.1, 0.1, 0.02, 0.005)
    n_each = colc.number_input(t("seq_av_maxusers"), 500, 200_000, 30_000, step=1000)
    av_alpha = st.select_slider("α ", [0.01, 0.05, 0.10], value=0.05)

    cfg = ExperimentConfig(metric_type=MetricType.BINARY, baseline=base,
                           absolute_effect=eff, n_control=int(n_each),
                           n_treatment=int(n_each), seed=20)
    stream = simulate_stream(cfg)
    res = always_valid_from_stream(stream, metric="binary", alpha=av_alpha, step=100)
    n_axis = np.arange(len(res.effect)) * 100 + 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.concatenate([n_axis, n_axis[::-1]]),
                             y=np.concatenate([res.ci_high, res.ci_low[::-1]]),
                             fill="toself", fillcolor="rgba(86,180,233,0.3)",
                             line=dict(width=0), name=t("seq_av_ciname"),
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=n_axis, y=res.effect, line=dict(color=theme.ACCENT, width=2.5),
                             name=t("seq_av_effname")))
    fig.add_hline(y=eff, line_color=theme.OKABE["green"], annotation_text=t("seq_av_true"))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    if res.reject_index is not None:
        fig.add_vline(x=res.reject_index, line_dash="dot", line_color=theme.TREATMENT,
                      annotation_text=t("seq_av_stop", n=f"{res.reject_index:,}"))
    fig.update_xaxes(title=t("seq_av_totobs"))
    fig.update_yaxes(title=t("seq_av_diffaxis"))
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, width='stretch')

    total = 2 * int(n_each)
    if res.reject_index is not None:
        saved = 1 - res.reject_index / total
        st.success(t("seq_av_success", n=f"{res.reject_index:,}",
                     pct=f"{saved*100:.0f}", total=f"{total:,}"))
    else:
        st.info(t("seq_av_fail"))

# ---------------------------------------------------------------- SPRT
with tab3:
    st.markdown(t("seq_sprt_md"))
    c1, c2, c3, c4 = st.columns(4)
    mu1 = c1.number_input(t("seq_sprt_mu1"), 0.05, 2.0, 0.3, 0.05)
    sigma = c2.number_input("σ", 0.1, 5.0, 1.0, 0.1)
    true_mu = c3.number_input(t("seq_sprt_truemu"), -1.0, 2.0, 0.3, 0.05)
    n = c4.number_input(t("seq_sprt_len"), 100, 20_000, 3000, step=100)

    rng = np.random.default_rng(1)
    data = rng.normal(true_mu, sigma, size=int(n))
    res = sprt_normal(data, mean_0=0.0, mean_1=mu1, sigma=sigma)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=res.log_lr, line=dict(color=theme.ACCENT, width=2),
                             name=t("seq_sprt_llr")))
    fig.add_hline(y=res.upper, line_color=theme.TREATMENT, annotation_text=t("seq_sprt_reject"))
    fig.add_hline(y=res.lower, line_color=theme.OKABE["green"], annotation_text=t("seq_sprt_accept"))
    if res.stopping_index is not None:
        fig.add_vline(x=res.stopping_index, line_dash="dot", line_color="black")
    fig.update_xaxes(title=t("seq_sprt_obs_axis"))
    fig.update_yaxes(title=t("seq_sprt_llr_axis"))
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, width='stretch')

    verdict = {"reject_h0": t("seq_sprt_v_reject"),
               "accept_h0": t("seq_sprt_v_accept"),
               "continue": t("seq_sprt_v_cont")}[res.decision]
    if res.stopping_index is not None:
        st.metric(t("seq_sprt_decision"), verdict,
                  delta=t("seq_sprt_after", n=f"{res.stopping_index:,}"))
    else:
        st.metric(t("seq_sprt_decision"), verdict)

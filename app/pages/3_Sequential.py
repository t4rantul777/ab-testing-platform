"""Sequential testing page -- the headline feature."""

from __future__ import annotations

import theme
import numpy as np
import plotly.graph_objects as go
import streamlit as st

theme.page_config("Sequential", "⏱️")

from abtest import (  # noqa: E402
    ExperimentConfig,
    MetricType,
    always_valid_from_stream,
    group_sequential_boundaries,
    sequential_alpha,
    simulate_stream,
    sprt_normal,
)

st.title("⏱️ Sequential & Always-Valid Testing")
st.caption("Look at your experiment as often as you like — without inflating the error rate.")

tab1, tab2, tab3 = st.tabs(
    ["Group-sequential boundaries", "Always-valid (mSPRT)", "Wald SPRT"]
)

# ---------------------------------------------------------------- group seq.
with tab1:
    st.markdown(
        "Pre-plan **K** interim looks. The boundaries below keep the overall "
        "false-positive rate at α even though you test K times."
    )
    c1, c2, c3 = st.columns(3)
    K = c1.slider("Number of looks (K)", 2, 12, 5)
    alpha = c2.select_slider("α", [0.01, 0.05, 0.10], value=0.05)
    shape = c3.radio("Spending shape", ["obf", "pocock"],
                     format_func=lambda s: "O'Brien-Fleming" if s == "obf" else "Pocock")

    design = group_sequential_boundaries(K, alpha=alpha, shape=shape)
    naive = sequential_alpha(np.array([1.959964] * K)) if alpha == 0.05 else None

    looks = np.arange(1, K + 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=looks, y=design.z_boundaries, mode="lines+markers",
                             line=dict(color=theme.ACCENT, width=3), name="Boundary (Z)"))
    fig.add_hline(y=1.959964, line_dash="dash", line_color="black",
                  annotation_text="naive 1.96")
    fig.update_xaxes(title="Interim look")
    fig.update_yaxes(title="Rejection boundary (Z)")
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    m1, m2 = st.columns(2)
    m1.metric("Family-wise error actually spent", f"{design.achieved_alpha:.4f}",
              help="Should match the target α — verified by the AGS recursion.")
    if naive is not None:
        m2.metric("If you naively used 1.96 at every look", f"{naive:.3f}",
                  delta=f"{(naive-alpha):.3f} over target", delta_color="inverse")

    st.dataframe(
        {
            "Look": looks,
            "Z boundary": np.round(design.z_boundaries, 4),
            "Nominal p at this look": np.round(design.nominal_alpha, 5),
        },
        use_container_width=True, hide_index=True,
    )

# ---------------------------------------------------------------- always-valid
with tab2:
    st.markdown(
        "The **always-valid** confidence sequence can be checked at every "
        "observation. Stop as soon as the band clears zero — the guarantee holds "
        "no matter when you stop."
    )
    exp = st.session_state.get("experiment")
    cola, colb, colc = st.columns(3)
    base = cola.number_input("Baseline rate", 0.01, 0.6,
                             float(exp["config"].baseline) if exp else 0.10, 0.01)
    eff = colb.number_input("True absolute lift", -0.1, 0.1, 0.02, 0.005)
    n_each = colc.number_input("Max users per arm", 500, 200_000, 30_000, step=1000)
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
                             line=dict(width=0), name="95% confidence sequence",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=n_axis, y=res.effect, line=dict(color=theme.ACCENT, width=2.5),
                             name="Effect estimate"))
    fig.add_hline(y=eff, line_color=theme.OKABE["green"], annotation_text="true effect")
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    if res.reject_index is not None:
        fig.add_vline(x=res.reject_index, line_dash="dot", line_color=theme.TREATMENT,
                      annotation_text=f"stop @ {res.reject_index:,}")
    fig.update_xaxes(title="Total observations")
    fig.update_yaxes(title="Treatment − control rate")
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    total = 2 * int(n_each)
    if res.reject_index is not None:
        saved = 1 - res.reject_index / total
        st.success(
            f"Significant after **{res.reject_index:,}** observations — about "
            f"**{saved*100:.0f}%** fewer than running the full {total:,}."
        )
    else:
        st.info("Did not reach significance within the simulated horizon.")

# ---------------------------------------------------------------- SPRT
with tab3:
    st.markdown(
        "Wald's SPRT accumulates the log-likelihood ratio of H1 vs H0 and stops "
        "when it crosses either boundary — accept H0, reject H0, or keep going."
    )
    c1, c2, c3, c4 = st.columns(4)
    mu1 = c1.number_input("H1 mean effect", 0.05, 2.0, 0.3, 0.05)
    sigma = c2.number_input("σ", 0.1, 5.0, 1.0, 0.1)
    true_mu = c3.number_input("True mean (data)", -1.0, 2.0, 0.3, 0.05)
    n = c4.number_input("Stream length", 100, 20_000, 3000, step=100)

    rng = np.random.default_rng(1)
    data = rng.normal(true_mu, sigma, size=int(n))
    res = sprt_normal(data, mean_0=0.0, mean_1=mu1, sigma=sigma)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=res.log_lr, line=dict(color=theme.ACCENT, width=2),
                             name="cumulative log-LR"))
    fig.add_hline(y=res.upper, line_color=theme.TREATMENT, annotation_text="reject H0")
    fig.add_hline(y=res.lower, line_color=theme.OKABE["green"], annotation_text="accept H0")
    if res.stopping_index is not None:
        fig.add_vline(x=res.stopping_index, line_dash="dot", line_color="black")
    fig.update_xaxes(title="Observation")
    fig.update_yaxes(title="Cumulative log-likelihood ratio")
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    verdict = {"reject_h0": "✅ Reject H0 (effect detected)",
               "accept_h0": "❌ Accept H0 (no effect)",
               "continue": "… inconclusive within the stream"}[res.decision]
    if res.stopping_index is not None:
        st.metric("Decision", verdict, delta=f"after {res.stopping_index:,} obs")
    else:
        st.metric("Decision", verdict)

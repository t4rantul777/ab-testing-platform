"""Significance page -- fixed-horizon tests with CIs and effect sizes."""

from __future__ import annotations

import theme
import numpy as np
import plotly.graph_objects as go
import streamlit as st

theme.page_config("Significance", "📊")

from i18n import language_selector, t  # noqa: E402
from abtest import (  # noqa: E402
    MetricType,
    chi_square_test,
    two_proportion_ztest,
    welch_ttest,
)
from abtest.datamodel import Alternative

language_selector()

st.title(t("sig_title"))
st.caption(t("sig_caption"))

# Alternative: translated labels but the enum code is the underlying value.
alt_labels = {
    "two-sided": t("sig_alt_two"),
    "larger": t("sig_alt_larger"),
    "smaller": t("sig_alt_smaller"),
}
alt_code = st.sidebar.selectbox(t("sig_alt"), list(alt_labels.keys()),
                                format_func=lambda k: alt_labels[k])
alt = Alternative(alt_code)
alpha = st.sidebar.select_slider(t("alpha"), [0.01, 0.05, 0.10], value=0.05)

mode_opts = [t("sig_input_sim"), t("sig_input_manual")]
mode = st.radio(t("sig_input"), mode_opts, horizontal=True)

if mode == mode_opts[0]:
    exp = st.session_state.get("experiment")
    if not exp:
        st.warning(t("sig_no_exp"))
        st.stop()
    cfg = exp["config"]
    control, treatment = exp["control"], exp["treatment"]
    is_binary = cfg.metric_type is MetricType.BINARY
    st.caption(t("sig_using", name=cfg.name, metric=cfg.metric_type.value,
                 n=f"{cfg.n_control:,}"))
else:
    metric_opts = [t("sig_binary"), t("sig_continuous")]
    is_binary = st.radio(t("sig_metric"), metric_opts, horizontal=True) == metric_opts[0]
    if is_binary:
        colc, colt = st.columns(2)
        n_c = colc.number_input(t("sig_control_users"), 1, 10_000_000, 8000)
        x_c = colc.number_input(t("sig_control_conv"), 0, 10_000_000, 800)
        n_t = colt.number_input(t("sig_treat_users"), 1, 10_000_000, 8000)
        x_t = colt.number_input(t("sig_treat_conv"), 0, 10_000_000, 920)
        control = np.array([1] * int(x_c) + [0] * int(n_c - x_c), dtype=float)
        treatment = np.array([1] * int(x_t) + [0] * int(n_t - x_t), dtype=float)
    else:
        st.info(t("sig_cont_info"))
        st.stop()

if is_binary:
    z = two_proportion_ztest(control, treatment, alpha=alpha, alternative=alt)
    chi = chi_square_test(control, treatment, alpha=alpha)

    st.subheader(t("sig_sub_ztest"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("sig_control_rate"), f"{z.extra['rate_control']*100:.2f}%")
    c2.metric(t("sig_treat_rate"), f"{z.extra['rate_treatment']*100:.2f}%")
    c3.metric(t("sig_abs_lift"), f"{z.effect_estimate*100:+.2f} pp")
    c4.metric(t("sig_rel_lift"), f"{z.extra['relative_lift']*100:+.1f}%")

    d1, d2, d3 = st.columns(3)
    d1.metric(t("sig_zstat"), f"{z.statistic:.3f}")
    d2.metric(t("p_value"), f"{z.p_value:.4g}")
    d3.metric(t("significant_q"), t("yes") if z.significant else t("no"))
    st.caption(t("sig_ci_h", lo=f"{z.ci_low:+.4g}", hi=f"{z.ci_high:+.4g}",
                 h=f"{z.extra['cohens_h']:.3f}"))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[z.effect_estimate], y=[0], mode="markers", marker=dict(size=14, color=theme.ACCENT),
        error_x=dict(type="data",
                     array=[z.ci_high - z.effect_estimate],
                     arrayminus=[z.effect_estimate - z.ci_low], color=theme.ACCENT),
        name=t("sig_effect_ci_name")))
    fig.add_vline(x=0, line_dash="dash", line_color="black")
    fig.update_yaxes(showticklabels=False)
    fig.update_xaxes(title=t("sig_diff_axis"))
    theme.apply_plotly_theme(fig)
    st.plotly_chart(fig, width='stretch')

    with st.expander(t("sig_chi_exp")):
        st.write(t("sig_chi_line", chi=f"{chi.statistic:.4f}",
                   dof=chi.extra['dof'], p=f"{chi.p_value:.4g}"))
        st.caption(t("sig_chi_note"))
else:
    ttest = welch_ttest(control, treatment, alpha=alpha, alternative=alt)
    st.subheader(t("sig_sub_ttest"))
    c1, c2, c3 = st.columns(3)
    c1.metric(t("sig_mean_diff"), f"{ttest.effect_estimate:+.4g}")
    c2.metric(t("sig_tstat"), f"{ttest.statistic:.3f}")
    c3.metric(t("p_value"), f"{ttest.p_value:.4g}")
    st.caption(t("sig_ci_d", lo=f"{ttest.ci_low:+.4g}", hi=f"{ttest.ci_high:+.4g}",
                 df=f"{ttest.extra['df']:.1f}", d=f"{ttest.extra['cohens_d']:.3f}"))
    st.metric(t("significant_q"), t("yes") if ttest.significant else t("no"))

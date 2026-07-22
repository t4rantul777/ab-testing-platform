"""A/B Testing Statistical Significance Platform -- Streamlit entry point.

Run with::

    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import theme  # noqa: F401  (adds src/ to sys.path and holds shared helpers)
import streamlit as st

theme.page_config("Home", "🧪")

from i18n import language_selector, t  # noqa: E402

language_selector()

st.title(t("home_title"))
st.caption(t("home_caption"))

st.markdown(t("home_body"))

col1, col2, col3 = st.columns(3)
col1.metric(t("home_m_tests"), "4", help=t("home_m_tests_help"))
col2.metric(t("home_m_seq"), "3", help=t("home_m_seq_help"))
col3.metric(t("home_m_ext"), "0", help=t("home_m_ext_help"))

st.divider()

st.subheader(t("home_sub_why"))
st.markdown(t("home_why_body"))

st.info(t("home_info"))

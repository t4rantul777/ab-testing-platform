"""A/B Testing Statistical Significance Platform -- Streamlit entry point.

Run with::

    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import theme  # noqa: F401  (adds src/ to sys.path and holds shared helpers)
import streamlit as st

theme.page_config("Home", "🧪")

st.title("🧪 A/B Testing Statistical Significance Platform")
st.caption(
    "Симулируй эксперименты, считай значимость, останавливай тесты раньше срока "
    "без раздувания ошибки I рода · Simulate, test, and stop experiments early."
)

st.markdown(
    """
This platform goes beyond a single t-test. It is a small but complete
experimentation toolkit:

- **🧪 Simulator** — generate binary or continuous experiments with a *known*
  ground-truth effect, so every method can be validated.
- **📊 Significance** — Welch's t-test, two-proportion z-test, chi-square, with
  confidence intervals and effect sizes.
- **⏱️ Sequential** — peek at your experiment as often as you like: SPRT,
  always-valid confidence sequences (mSPRT), and Pocock / O'Brien-Fleming
  group-sequential boundaries.
- **⚡ Power & MDE** — sample-size planning, power curves and the minimum
  detectable effect.
- **🗂️ History** — every run is logged to a local SQLite database.

Use the sidebar to navigate. A good first step is the **Simulator**: create an
experiment, then carry it into the other pages.
"""
)

col1, col2, col3 = st.columns(3)
col1.metric("Statistical tests", "4", help="t-test, z-test, chi-square, sequential")
col2.metric("Sequential methods", "3", help="SPRT, mSPRT, group-sequential")
col3.metric("External services required", "0", help="Fully self-contained")

st.divider()

st.subheader("Why sequential testing matters")
st.markdown(
    """
If you run a classic fixed-horizon test but check the p-value every day and stop
the moment it dips below 0.05, your real false-positive rate is **not 5%** — with
five looks it is about **14%**, and it keeps climbing with every peek. The
Sequential page shows the boundaries that fix this, and lets you watch an
always-valid confidence interval tighten in real time.
"""
)

st.info(
    "Everything here runs locally on simulated data — no API keys, no database "
    "server, no cloud. Open the **Sequential** page to see the headline feature."
)

"""History page -- experiments logged to the local SQLite database."""

from __future__ import annotations

import theme
import pandas as pd
import streamlit as st

theme.page_config("History", "🗂️")

from i18n import language_selector, t  # noqa: E402
from abtest import ABTestStore  # noqa: E402

language_selector()

st.title(t("hist_title"))
st.caption(t("hist_caption"))

with ABTestStore(theme.DB_PATH) as store:
    board = store.experiment_scoreboard()
    experiments = store.list_experiments()

if not board:
    st.info(t("hist_empty"))
    st.stop()

df = pd.DataFrame(board)
if not df.empty:
    df["verdict"] = df["significant"].map({1: t("hist_v_sig"), 0: t("hist_v_nsig"),
                                           None: t("hist_v_none")})
    show = df[["id", "name", "metric_type", "baseline", "effect",
               "n_control", "test_name", "p_value", "verdict", "created_at"]]
    show = show.rename(columns={
        "id": t("hist_c_id"), "name": t("hist_c_name"), "metric_type": t("hist_c_metric"),
        "baseline": t("hist_c_baseline"), "effect": t("hist_c_effect"),
        "n_control": t("hist_c_narm"), "test_name": t("hist_c_test"),
        "p_value": t("hist_c_p"), "verdict": t("hist_c_verdict"),
        "created_at": t("hist_c_saved"),
    })
    st.dataframe(show, width='stretch', hide_index=True)

st.metric(t("hist_logged"), len(experiments))

st.divider()
st.subheader(t("hist_sub_sql"))
st.code(
    """-- one row per experiment, joined to its most recent test result
SELECT e.id, e.name, e.metric_type, e.baseline, e.effect,
       r.test_name, r.p_value, r.significant
FROM experiments e
LEFT JOIN (
    SELECT r1.* FROM results r1
    JOIN (SELECT experiment_id, MAX(id) AS max_id
          FROM results GROUP BY experiment_id) last
      ON r1.id = last.max_id
) r ON r.experiment_id = e.id
ORDER BY e.id DESC;""",
    language="sql",
)

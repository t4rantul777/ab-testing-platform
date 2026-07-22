"""History page -- experiments logged to the local SQLite database."""

from __future__ import annotations

import theme
import pandas as pd
import streamlit as st

theme.page_config("History", "🗂️")

from abtest import ABTestStore  # noqa: E402

st.title("🗂️ Experiment History")
st.caption("Every saved run is stored in a local SQLite database (real SQL, no server).")

with ABTestStore(theme.DB_PATH) as store:
    board = store.experiment_scoreboard()
    experiments = store.list_experiments()

if not board:
    st.info("No experiments saved yet. Open the **Simulator** and click "
            "*Save this experiment to history*.")
    st.stop()

df = pd.DataFrame(board)
if not df.empty:
    df["verdict"] = df["significant"].map({1: "✅ significant", 0: "❌ not sig.",
                                           None: "—"})
    show = df[["id", "name", "metric_type", "baseline", "effect",
               "n_control", "test_name", "p_value", "verdict", "created_at"]]
    show = show.rename(columns={
        "id": "ID", "name": "Experiment", "metric_type": "Metric",
        "baseline": "Baseline", "effect": "True effect", "n_control": "n/arm",
        "test_name": "Last test", "p_value": "p-value", "verdict": "Verdict",
        "created_at": "Saved at",
    })
    st.dataframe(show, use_container_width=True, hide_index=True)

st.metric("Experiments logged", len(experiments))

st.divider()
st.subheader("Underlying SQL")
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

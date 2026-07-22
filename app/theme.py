"""Shared styling and helpers for the Streamlit app.

Kept separate from the ``abtest`` library so the package stays UI-agnostic.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the ``src`` layout importable even when the package is not pip-installed
# (e.g. someone clones the repo and just runs ``streamlit run``).
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Okabe-Ito colourblind-safe palette.
OKABE = {
    "black": "#000000",
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
}
CONTROL = OKABE["sky"]
TREATMENT = OKABE["vermillion"]
ACCENT = OKABE["blue"]

DB_PATH = str(Path(__file__).resolve().parent.parent / "experiments.db")


def apply_plotly_theme(fig):
    """Apply a clean, consistent layout to a Plotly figure."""
    fig.update_layout(
        template="plotly_white",
        font=dict(size=14),
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#ECECEC")
    fig.update_yaxes(showgrid=True, gridcolor="#ECECEC")
    return fig


def page_config(title: str, icon: str = "🧪"):
    import streamlit as st

    st.set_page_config(page_title=f"{title} · A/B Platform", page_icon=icon,
                       layout="wide")

"""Smoke tests for the Streamlit app using Streamlit's AppTest harness.

These actually execute each page's script (widgets, computation, charts) in a
simulated runtime and assert that no uncaught exception is raised. They double
as CI protection against a page importing something that no longer exists.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"
# Pages do ``import theme`` from the app directory; in real multipage usage that
# dir is the main-script dir. Put it on the path so AppTest can resolve it.
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


def _make_session_experiment():
    from abtest import ExperimentConfig, MetricType, simulate_experiment

    cfg = ExperimentConfig(
        name="smoke", metric_type=MetricType.BINARY, baseline=0.10,
        absolute_effect=0.02, n_control=2000, n_treatment=2000, seed=1,
    )
    exp = simulate_experiment(cfg)
    return {"config": cfg, "control": exp.control, "treatment": exp.treatment}


def test_home_runs():
    at = AppTest.from_file(str(APP_DIR / "streamlit_app.py")).run(timeout=30)
    assert not at.exception


def test_simulator_runs():
    at = AppTest.from_file(str(APP_DIR / "pages" / "1_Simulator.py")).run(timeout=30)
    assert not at.exception


def test_significance_runs_with_session():
    at = AppTest.from_file(str(APP_DIR / "pages" / "2_Significance.py"))
    at.session_state["experiment"] = _make_session_experiment()
    at.run(timeout=30)
    assert not at.exception


def test_sequential_runs():
    at = AppTest.from_file(str(APP_DIR / "pages" / "3_Sequential.py")).run(timeout=60)
    assert not at.exception


def test_power_runs():
    at = AppTest.from_file(str(APP_DIR / "pages" / "4_Power_and_MDE.py")).run(timeout=30)
    assert not at.exception


def test_history_runs():
    at = AppTest.from_file(str(APP_DIR / "pages" / "5_History.py")).run(timeout=30)
    assert not at.exception

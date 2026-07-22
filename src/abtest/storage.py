"""Lightweight SQL persistence layer (SQLite).

The tech-stack for this project lists SQL, and there is a genuine analytics use
for it: an experimentation platform needs a *registry* of experiments and their
results so you can audit what was tested, re-open past analyses and avoid
re-running the same thing. SQLite keeps the project zero-configuration (no
server) while still being real SQL you could point at Postgres later.

Two tables:

* ``experiments`` -- one row per experiment configuration.
* ``results``     -- one row per statistical test run against an experiment.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from .datamodel import ExperimentConfig, TestResult

_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    metric_type  TEXT    NOT NULL,
    baseline     REAL    NOT NULL,
    effect       REAL    NOT NULL,
    n_control    INTEGER NOT NULL,
    n_treatment  INTEGER NOT NULL,
    config_json  TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS results (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id  INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    test_name      TEXT    NOT NULL,
    statistic      REAL,
    p_value        REAL,
    effect         REAL,
    ci_low         REAL,
    ci_high        REAL,
    significant    INTEGER,
    extra_json     TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


class ABTestStore:
    """A tiny repository over a SQLite database.

    Usable as a context manager::

        with ABTestStore("experiments.db") as store:
            exp_id = store.save_experiment(config)
            store.save_result(exp_id, result)
    """

    def __init__(self, path: str | Path = "experiments.db"):
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        with closing(self._conn.cursor()) as cur:
            cur.executescript(_SCHEMA)
        self._conn.commit()

    # -- lifecycle --------------------------------------------------------
    def __enter__(self) -> "ABTestStore":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    # -- writes -----------------------------------------------------------
    def save_experiment(self, config: ExperimentConfig) -> int:
        cur = self._conn.execute(
            """INSERT INTO experiments
                   (name, metric_type, baseline, effect, n_control, n_treatment, config_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                config.name,
                config.metric_type.value,
                config.baseline,
                config.true_absolute_effect(),
                config.n_control,
                config.n_treatment,
                json.dumps(config.to_dict()),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def save_result(self, experiment_id: int, result: TestResult) -> int:
        cur = self._conn.execute(
            """INSERT INTO results
                   (experiment_id, test_name, statistic, p_value, effect,
                    ci_low, ci_high, significant, extra_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                experiment_id,
                result.test_name,
                result.statistic,
                result.p_value,
                result.effect_estimate,
                result.ci_low,
                result.ci_high,
                int(result.significant),
                json.dumps(result.extra),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    # -- reads ------------------------------------------------------------
    def list_experiments(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM experiments ORDER BY created_at DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_results(self, experiment_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM results WHERE experiment_id = ? ORDER BY id",
            (experiment_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def experiment_scoreboard(self) -> list[dict[str, Any]]:
        """A joined summary: each experiment with its latest test verdict.

        Demonstrates a non-trivial SQL query (window function + join) that the
        dashboard uses for its history view.
        """
        rows = self._conn.execute(
            """
            SELECT e.id, e.name, e.metric_type, e.baseline, e.effect,
                   e.n_control, e.n_treatment, r.test_name, r.p_value,
                   r.significant, r.created_at
            FROM experiments e
            LEFT JOIN (
                SELECT r1.*
                FROM results r1
                JOIN (
                    SELECT experiment_id, MAX(id) AS max_id
                    FROM results GROUP BY experiment_id
                ) last ON r1.id = last.max_id
            ) r ON r.experiment_id = e.id
            ORDER BY e.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

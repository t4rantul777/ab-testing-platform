"""Tests for the SQLite persistence layer."""

from abtest import (
    ABTestStore,
    ExperimentConfig,
    MetricType,
    analyze,
    simulate_experiment,
)


def test_save_and_read_roundtrip(tmp_path):
    cfg = ExperimentConfig(
        name="checkout-cta",
        metric_type=MetricType.BINARY,
        baseline=0.10,
        absolute_effect=0.02,
        n_control=2000,
        n_treatment=2000,
        seed=1,
    )
    exp = simulate_experiment(cfg)
    result = analyze(exp.control, exp.treatment, MetricType.BINARY)

    db = tmp_path / "test.db"
    with ABTestStore(db) as store:
        exp_id = store.save_experiment(cfg)
        store.save_result(exp_id, result)

        experiments = store.list_experiments()
        assert len(experiments) == 1
        assert experiments[0]["name"] == "checkout-cta"

        results = store.get_results(exp_id)
        assert len(results) == 1
        assert results[0]["test_name"].startswith("Two-proportion")

        board = store.experiment_scoreboard()
        assert len(board) == 1
        assert board[0]["name"] == "checkout-cta"
        assert board[0]["test_name"].startswith("Two-proportion")


def test_scoreboard_returns_latest_result(tmp_path):
    cfg = ExperimentConfig(name="exp", metric_type=MetricType.BINARY, seed=1)
    exp = simulate_experiment(cfg)
    r1 = analyze(exp.control, exp.treatment, MetricType.BINARY)
    r2 = analyze(exp.control, exp.treatment, MetricType.BINARY)

    with ABTestStore(tmp_path / "s.db") as store:
        eid = store.save_experiment(cfg)
        store.save_result(eid, r1)
        last_id = store.save_result(eid, r2)
        board = store.experiment_scoreboard()
        assert len(board) == 1  # one row per experiment, latest result joined

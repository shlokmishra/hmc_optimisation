import json

import numpy as np
import pytest

from power_reset_spectral_comparison.core import Oracle, ar_step
from stat605.agd import (
    logistic_oracle,
    momentum,
    next_theta,
    quadratic_oracle,
    run_agd,
)
from stat605.agd_experiments import crossings, run_config

STIFF = np.diag([0.5, 5.0, 500.0])
ETA = 1.0 / 500.0


def test_theta_recursion_special_cases():
    # q = 0 is the FISTA t-sequence with theta = 1 / t.
    theta, t = 1.0, 1.0
    for _ in range(50):
        theta_new = next_theta(theta, 0.0)
        t_new = (1 + np.sqrt(1 + 4 * t * t)) / 2
        assert theta_new == pytest.approx(1 / t_new, rel=1e-12)
        assert momentum(theta, theta_new) == pytest.approx((t - 1) / t_new, rel=1e-10, abs=1e-15)
        theta, t = theta_new, t_new
    # q = 1 keeps theta = 1 and zero momentum: plain gradient descent.
    assert next_theta(1.0, 1.0) == 1.0 and momentum(1.0, 1.0) == 0.0
    # 0 < q < 1: theta -> sqrt(q) and beta -> (1 - sqrt(q)) / (1 + sqrt(q)).
    q, theta = 0.01, 1.0
    for _ in range(2000):
        previous, theta = theta, next_theta(theta, q)
    assert theta == pytest.approx(0.1, rel=1e-10)
    assert momentum(previous, theta) == pytest.approx(0.9 / 1.1, rel=1e-8)


def test_hand_computed_first_two_updates():
    out, meta = run_agd(
        quadratic_oracle(np.array([[1.0]])), np.array([1.0]), 0.1, 2, keep_states=True
    )
    theta1 = (np.sqrt(5) - 1) / 2
    theta2 = next_theta(theta1, 0.0)
    beta2 = theta1 * (1 - theta1) / (theta1**2 + theta2)
    np.testing.assert_array_equal(out["x"][1], [0.9])
    np.testing.assert_array_equal(out["y"][1], [0.9])  # beta_1 = 0 because theta_0 = 1
    np.testing.assert_allclose(out["x"][2], [0.81], rtol=1e-15)
    np.testing.assert_allclose(out["y"][2], out["x"][2] + beta2 * (out["x"][2] - 0.9), rtol=1e-15)
    assert meta["gradients"] == 2 and meta["objectives"] == 3 and meta["restarts"] == 0


def test_q_one_is_gradient_descent():
    x0 = np.ones(3)
    out, _ = run_agd(quadratic_oracle(STIFF), x0, ETA, 25, q=1.0)
    x = x0.copy()
    for _ in range(25):
        x = x - ETA * (STIFF @ x)
    np.testing.assert_allclose(out["x_final"], x, rtol=1e-13)


def test_gradient_restart_agrees_with_existing_recurrence():
    x0 = np.ones(3)
    n = 400
    out, _ = run_agd(quadratic_oracle(STIFF), x0, ETA, n, restart="gradient")
    oracle = Oracle(STIFF)
    x, u, t = x0.copy(), x0.copy(), 1.0
    f, events = [oracle.loss(x)], []
    for _ in range(n):
        oracle.begin()
        x, u, t, event, _ = ar_step(oracle, x, u, t, ETA)
        f.append(oracle.loss(x))
        events.append(event)
    assert any(events)
    np.testing.assert_array_equal(out["restart"], events)
    np.testing.assert_allclose(out["f"], f, rtol=1e-8, atol=0)


@pytest.mark.parametrize("restart", ["function", "gradient"])
def test_restart_fires_exactly_on_strict_inequality_and_resets_state(restart):
    out, meta = run_agd(
        quadratic_oracle(STIFF), np.ones(3), ETA, 400, restart=restart, keep_states=True
    )
    fired = out["restart"]
    assert fired.any() and not fired[0]  # no spurious first-update restart at eta = 1/L
    if restart == "function":
        np.testing.assert_array_equal(fired, out["f"][1:] > out["f"][:-1])
        assert meta["controller_objectives"] == 400 and meta["controller_dots"] == 0
        assert meta["diagnostic_objectives"] == 1
    else:
        np.testing.assert_array_equal(fired, out["statistic"] > 0)
        assert meta["controller_objectives"] == 0 and meta["controller_dots"] == 400
    for k in np.flatnonzero(fired):
        # New endpoint retained, y reset to it, and the next update is a plain gradient step.
        np.testing.assert_array_equal(out["y"][k + 1], out["x"][k + 1])
        if k + 2 <= 400:
            expected = out["x"][k + 1] - ETA * (STIFF @ out["x"][k + 1])
            np.testing.assert_array_equal(out["x"][k + 2], expected)
            if not fired[k + 1]:
                np.testing.assert_array_equal(out["y"][k + 2], out["x"][k + 2])
    assert meta["gradients"] == 400 and meta["restarts"] == fired.sum()


@pytest.mark.parametrize("restart", ["function", "gradient"])
def test_equality_does_not_restart(restart):
    # Zero objective and zero gradient: both statistics are exactly zero.
    out, _ = run_agd(quadratic_oracle(np.zeros((2, 2))), np.ones(2), 0.1, 20, restart=restart)
    assert not out["restart"].any()
    np.testing.assert_array_equal(out["statistic"], np.zeros(20))


def test_function_restart_retains_increased_endpoint():
    # eta > 2/L in one dimension makes the first update increase f.
    out, meta = run_agd(
        quadratic_oracle(np.array([[1.0]])), np.array([1.0]), 2.5, 1, restart="function"
    )
    assert out["restart"][0] and meta["restarts"] == 1
    np.testing.assert_array_equal(out["x_final"], [-1.5])
    np.testing.assert_array_equal(out["y_final"], [-1.5])


def test_fixed_interval_clock_restarts_after_each_segment():
    out, _ = run_agd(quadratic_oracle(STIFF), np.ones(3), ETA, 17, restart="fixed", interval=5)
    np.testing.assert_array_equal(np.flatnonzero(out["restart"]), [4, 9, 14])


def test_nonfinite_failure_keeps_paid_work():
    oracle = quadratic_oracle(np.array([[1e200]]))
    out, meta = run_agd(oracle, np.array([1.0]), 1e200, 10, restart="gradient")
    assert meta["status"] == "failure" and meta["updates"] == 0
    assert meta["gradients"] == 1 and meta["charged_unfinished_gradients"] == 1
    assert len(out["f"]) == 1 and len(out["restart"]) == 0


def test_invalid_arguments():
    oracle = quadratic_oracle(np.eye(1))
    x = np.ones(1)
    with pytest.raises(ValueError):
        run_agd(oracle, x, 0.1, 1, q=1.5)
    with pytest.raises(ValueError):
        run_agd(oracle, x, 0.1, 1, restart="speed")
    with pytest.raises(ValueError):
        run_agd(oracle, x, 0.1, 1, restart="fixed")
    with pytest.raises(ValueError):
        run_agd(oracle, x, 0.1, 1, restart="gradient", interval=3)


def test_logistic_gradient_matches_finite_differences():
    rng = np.random.default_rng(0)
    A = rng.standard_normal((30, 4))
    b = np.where(rng.random(30) < 0.5, -1.0, 1.0)
    x = rng.standard_normal(4)
    oracle = logistic_oracle(A, b, 1e-2)
    g = oracle.grad(x)
    for i in range(4):
        e = np.zeros(4)
        e[i] = 1e-6
        numeric = (oracle.loss(x + e) - oracle.loss(x - e)) / 2e-6
        assert g[i] == pytest.approx(numeric, rel=1e-6, abs=1e-9)


def test_first_and_sustained_crossings_differ_and_censor():
    gap = np.array([1.0, 0.05, 0.5, 0.05, 0.01])
    assert crossings(gap, 0.1) == (1, 3)
    assert crossings(gap, 1e-3) == (None, None)
    assert crossings(np.array([1.0, 0.05, 0.5]), 0.1) == (1, None)
    assert crossings(np.array([0.01, 0.01]), 0.1) == (0, 0)


def test_run_config_writes_fresh_reproducible_summary(tmp_path):
    config = {
        "purpose": "test",
        "cases": [
            {
                "name": "tiny",
                "problem": {
                    "generate": {"n": 6, "kappa": 100.0, "L": 1.0, "spectrum": "log", "seed": 1}
                },
                "iterations": 600,
                "targets": [1e-6, 1e-300],
                "methods": [
                    {"label": "optimal_q", "q_factor": 1.0, "restart": "none"},
                    {"label": "function", "q_factor": None, "restart": "function"},
                    {"label": "gradient", "q_factor": None, "restart": "gradient"},
                    {
                        "label": "fixed",
                        "q_factor": None,
                        "restart": "fixed",
                        "interval": "e_sqrt_8_kappa",
                    },
                ],
            }
        ],
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    first = run_config(path, tmp_path / "a")
    second = run_config(path, tmp_path / "b")
    assert first["status"] == "passed" and len(first["runs"]) == 4
    for one, two in zip(first["runs"], second["runs"], strict=True):
        assert one["targets"] == two["targets"] and one["final_loss"] == two["final_loss"]
        assert one["gradients"] == 600
        assert one["targets"]["1e-06"]["sustained"] is not None
        assert one["targets"]["1e-300"] == {"first": None, "sustained": None}  # censored
    by_label = {r["label"]: r for r in first["runs"]}
    assert by_label["fixed"]["interval"] == round(np.e * np.sqrt(800.0))
    assert by_label["function"]["targets"]["1e-06"]["first"]["controller_objectives"] > 0
    assert by_label["gradient"]["targets"]["1e-06"]["first"]["controller_objectives"] == 0
    assert (tmp_path / "a/tiny.png").exists() and (tmp_path / "a/summary.json").exists()
    with pytest.raises(FileExistsError):
        run_config(path, tmp_path / "a")

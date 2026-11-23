import json

import numpy as np
import pytest

from power_reset_spectral_comparison.core import CONFIG, FROZEN_B, run
from stat605.rhgd import run_fixed_time_quadratic
from stat605.smoke import fixed_time_smoke


def test_two_step_period_matches_hand_computed_rational_states():
    arrays, meta = run_fixed_time_quadratic(
        np.ones((1, 1)),
        np.ones(1),
        h=0.5,
        period_steps=2,
        gradient_budget=8,
        keep_states=True,
    )
    # Two exact binary-rational segments, with endpoint retention at steps 2/4.
    x = np.array([1, 3 / 4, 27 / 64, 81 / 256, 729 / 4096])
    v = np.array([0, -3 / 8, 0, -81 / 512, 0])
    np.testing.assert_array_equal(arrays["x"][:, 0], x)
    np.testing.assert_array_equal(arrays["velocity"][:, 0], v)
    np.testing.assert_array_equal(
        arrays["velocity_pre_reset"][:, 0], [-3 / 8, -75 / 128, -81 / 512, -2025 / 8192]
    )
    np.testing.assert_array_equal(arrays["f"], 0.5 * x * x)
    np.testing.assert_array_equal(arrays["reset"], [False, True, False, True])
    np.testing.assert_array_equal(arrays["age"], [1, 2, 1, 2])
    np.testing.assert_array_equal(arrays["gradients"], [0, 2, 4, 6, 8])
    assert meta["resets"] == 2 and meta["period_time"] == 1.0
    assert meta["numerical_gradients"] == meta["literal_gradient_requests"] == 8
    assert meta["objectives"] == 5 and meta["final_segment_age"] == 0


def test_period_one_equals_gradient_descent_but_pays_both_rhgd_gradients():
    A, x0 = np.diag([1.0, 4.0]), np.array([1.0, -2.0])
    arrays, meta = run_fixed_time_quadratic(
        A,
        x0,
        h=0.25,
        period_steps=1,
        gradient_budget=14,
        keep_states=True,
    )
    points = [x0.copy()]
    for _ in range(7):
        points.append(points[-1] - 0.0625 * (A @ points[-1]))
    np.testing.assert_array_equal(arrays["x"], points)
    np.testing.assert_array_equal(arrays["velocity"], np.zeros((8, 2)))
    assert np.all(arrays["reset"]) and meta["resets"] == 7
    assert meta["numerical_gradients"] == 14 and meta["objectives"] == 8


def test_long_period_is_bitwise_equal_to_existing_rhgd_without_a_reset():
    A, x0 = np.diag([0.5, 5.0, 500.0]), np.ones(3)
    h, seed, n = np.sqrt(CONFIG["eta"]), 41001, 32
    # Explicitly establish that this independent existing-RHGD reference has no reset.
    assert np.all(np.random.default_rng(seed).random(n) >= np.sqrt(CONFIG["alpha"]) * h)
    reference, _ = run(A, x0, "RHGD", budget=2 * n, seed=seed)
    arrays, meta = run_fixed_time_quadratic(
        A,
        x0,
        h=h,
        period_steps=n + 1,
        gradient_budget=2 * n,
    )
    for key in ("f", "x_final", "aux_final", "gradients", "literal_gradients"):
        np.testing.assert_array_equal(arrays[key], reference[key])
    assert meta["resets"] == 0 and meta["final_segment_age"] == n
    assert np.any(arrays["aux_final"] != 0)  # No artificial reset at budget exhaustion.
    assert meta["uniform_draws"] == meta["exponential_draws"] == meta["controller_dots"] == 0


def test_periodic_path_matches_frozen_b_when_only_its_cap_fires():
    A, x0, period = np.diag([1.0, 500.0]), np.array([1.0, 0.0]), 4
    prior, _ = FROZEN_B.run(
        FROZEN_B.Problem(A, x0),
        "exact",
        "B",
        40,
        cap=period,
        diagnostic=True,
    )
    assert not np.any(prior["event"])  # No power-triggered reset in this fixture.
    arrays, meta = run_fixed_time_quadratic(
        A,
        x0,
        h=np.sqrt(0.002),
        period_steps=period,
        gradient_budget=40,
    )
    for key in ("f", "x_final", "reset", "age"):
        np.testing.assert_array_equal(arrays[key], prior[key])
    assert meta["resets"] == 5


@pytest.mark.parametrize("budget", [0, 1, 7, 8, 9])
def test_budget_never_splits_a_step_or_adds_a_terminal_reset(budget):
    arrays, meta = run_fixed_time_quadratic(
        np.ones((1, 1)),
        np.ones(1),
        h=0.1,
        period_steps=4,
        gradient_budget=budget,
    )
    n = budget // 2
    assert len(arrays["f"]) == n + 1 and len(arrays["reset"]) == n
    assert meta["numerical_gradients"] == 2 * n
    assert meta["unused_gradient_budget"] == budget % 2
    assert meta["objectives"] == n + 1
    assert meta["resets"] == n // 4 and meta["final_segment_age"] == n % 4


def test_clock_has_no_float_threshold_drift_and_zero_states_still_pay():
    arrays, meta = run_fixed_time_quadratic(
        np.eye(2),
        np.zeros(2),
        h=0.1,
        period_steps=3,
        gradient_budget=20,
    )
    np.testing.assert_array_equal(np.flatnonzero(arrays["reset"]) + 1, [3, 6, 9])
    np.testing.assert_array_equal(arrays["age"], [1, 2, 3, 1, 2, 3, 1, 2, 3, 1])
    assert meta["period_time"] == pytest.approx(0.3)
    assert meta["numerical_gradients"] == 20 and meta["cache_hits"] == 0
    np.testing.assert_array_equal(arrays["f"], np.zeros(11))


def test_objective_increase_does_not_add_a_reset_or_roll_back_position():
    arrays, meta = run_fixed_time_quadratic(
        np.ones((1, 1)),
        np.ones(1),
        h=0.1,
        period_steps=100,
        gradient_budget=50,
    )
    assert np.any(np.diff(arrays["f"]) > 0)
    assert meta["resets"] == 0 and not np.any(arrays["reset"])
    assert arrays["f"][-1] > np.min(arrays["f"])


def test_nonfinite_trial_retains_paid_work_and_raw_failed_state():
    arrays, meta = run_fixed_time_quadratic(
        np.ones((1, 1)),
        np.ones(1),
        h=1e200,
        period_steps=1,
        gradient_budget=8,
    )
    assert meta["status"] == "failure" and meta["updates"] == 0
    assert meta["attempted_updates"] == 1 and meta["resets"] == 0
    assert meta["numerical_gradients"] == meta["charged_unfinished_gradients"] == 2
    assert meta["objectives"] == 2 and meta["unused_gradient_budget"] == 6
    np.testing.assert_array_equal(arrays["f"], [0.5])
    assert not np.all(np.isfinite(arrays["failed_x"]))
    assert not np.isfinite(arrays["failed_f"])


def test_reset_does_not_hide_nonfinite_pre_reset_velocity(monkeypatch):
    original = FROZEN_B.rhgd_step

    def bad_velocity(*args):
        x, v, g, h, accepted = original(*args)
        return x, np.full_like(v, np.inf), g, h, accepted

    monkeypatch.setattr(FROZEN_B, "rhgd_step", bad_velocity)
    arrays, meta = run_fixed_time_quadratic(
        np.ones((1, 1)),
        np.ones(1),
        h=0.5,
        period_steps=1,
        gradient_budget=2,
    )
    assert meta["status"] == "failure" and meta["resets"] == 0
    assert np.all(np.isfinite(arrays["failed_x"])) and np.isfinite(arrays["failed_f"])
    assert not np.all(np.isfinite(arrays["failed_velocity_pre_reset"]))


def test_initial_objective_overflow_fails_before_any_gradient():
    arrays, meta = run_fixed_time_quadratic(
        np.array([[1e308]]),
        np.array([2.0]),
        h=0.1,
        period_steps=2,
        gradient_budget=10,
    )
    assert meta["failure"] == "nonfinite_initial_objective"
    assert meta["attempted_updates"] == meta["numerical_gradients"] == 0
    assert meta["objectives"] == 1 and not np.isfinite(arrays["f"][0])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"period_steps": 0},
        {"period_steps": -1},
        {"period_steps": 2.5},
        {"period_steps": True},
        {"gradient_budget": -1},
        {"gradient_budget": False},
        {"h": 0},
        {"h": -0.1},
        {"h": np.nan},
        {"h": np.inf},
        {"h": True},
    ],
)
def test_invalid_clock_or_budget_is_rejected(kwargs):
    args = dict(h=0.1, period_steps=2, gradient_budget=4)
    args.update(kwargs)
    with pytest.raises((ValueError, TypeError)):
        run_fixed_time_quadratic(np.eye(2), np.ones(2), **args)


def test_fixed_time_smoke_records_schedule_provenance_and_refuses_overwrite(tmp_path):
    output = tmp_path / "smoke"
    meta = fixed_time_smoke(output)
    assert meta["status"] == "passed" and len(meta["runs"]) == 2
    assert meta["purpose"] == "software_smoke_not_research_evidence"
    assert len(meta["input_sha256"]) == 2 and meta["source_sha256"]
    for record in meta["runs"]:
        assert record["numerical_gradients"] == 200 and record["resets"] == 12
        assert record["final_segment_age"] == 4 and record["period_steps"] == 8
        with np.load(output / record["fixture"], allow_pickle=False) as z:
            indices = np.flatnonzero(z["reset"]) + 1
            np.testing.assert_array_equal(indices, np.arange(8, 101, 8))
            np.testing.assert_array_equal(z["velocity"][indices], np.zeros((12, 100)))
    assert (output / "fixed_time_smoke.png").is_file()
    saved = json.loads((output / "summary.json").read_text())
    assert saved["config_sha256"] == meta["config_sha256"]
    with pytest.raises(FileExistsError):
        fixed_time_smoke(output)

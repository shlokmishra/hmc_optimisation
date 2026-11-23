from dataclasses import replace

import numpy as np
import pytest

from power_reset_spectral_comparison.core import CONFIG, run
from stat605.benchmark import RANDOMIZED_METHODS, Method, Step, run_benchmark
from stat605.problems import make_problem


@pytest.mark.parametrize("method", ("AGD", "AR_AGD", "CAGD", "RHGD", "B"))
def test_historical_paths_and_measured_work(method):
    problem = make_problem("linear", "common")
    budget = 129
    seed = 723 if method in RANDOMIZED_METHODS else None
    frozen, old = run(
        problem.A,
        problem.x0,
        method,
        budget,
        seed=seed,
        detailed=True,
        basis=problem.basis,
        eigenvalues=problem.eigenvalues,
    )
    trace, record = run_benchmark(
        problem,
        method,
        gradient_budget=budget,
        seed=seed,
        eta=CONFIG["eta"],
        supplied_mu=CONFIG["alpha"],
        diagnostic_steps=23,
    )
    np.testing.assert_array_equal(trace["x_final"], frozen["x_final"])
    np.testing.assert_array_equal(trace["loss"], frozen["f"])
    np.testing.assert_array_equal(trace["best_loss"], np.minimum.accumulate(frozen["f"]))
    np.testing.assert_array_equal(trace["reset"][1:], frozen["reset"])
    for key in ("gradients", "literal_gradients"):
        np.testing.assert_array_equal(trace[key], frozen[key])
    np.testing.assert_array_equal(trace["objectives"], 1 + trace["iteration"])
    for key in (
        "status",
        "numerical_gradients",
        "literal_gradient_requests",
        "cache_hits",
        "objectives",
        "uniform_draws",
        "exponential_draws",
        "controller_dots",
    ):
        assert record[key] == old[key]
    assert (record["charged_unfinished_gradients"], record["charged_unfinished_objectives"]) == (
        0,
        0,
    )
    assert record["attempted_updates"] == record["updates"] == len(trace["loss"]) - 1
    assert record["reset_count"] == np.count_nonzero(frozen["reset"])
    assert record["rejected_updates"] == 0
    assert np.all(np.diff(trace["optimizer_seconds"]) >= 0)
    assert record["wall_seconds"] >= sum(
        record[k] for k in ("optimizer_seconds", "setup_seconds", "diagnostic_seconds")
    )
    if method == "B":
        np.testing.assert_array_equal(trace["power_iteration"], np.arange(1, 24))
        expected = (frozen["endpoint_gradient"][:23] @ problem.basis) * (
            frozen["velocity_pre_reset"][:23] @ problem.basis
        )
        np.testing.assert_allclose(trace["modal_power"], expected, atol=1e-11, rtol=1e-10)
        np.testing.assert_allclose(
            trace["modal_power"].sum(axis=1), frozen["power"][:23], rtol=1e-11
        )
        np.testing.assert_array_equal(trace["global_power"], frozen["power"][:23])
    else:
        assert trace["modal_power"].shape == (0, 100)


def test_power_cap_and_step_scale_use_configured_values():
    problem = make_problem("log", "equal", source="generated", dimension=5, mu=0.4, L=10)
    eta = 0.04
    trace, record = run_benchmark(
        problem, "B", gradient_budget=9, eta=eta, supplied_mu=None, cap=1, diagnostic_steps=4
    )
    x = problem.x0.copy()
    # A cap of one clears the velocity after every update, reducing to gradient descent.
    for _ in range(4):
        x = x - np.sqrt(eta) ** 2 * (problem.A @ x)
    np.testing.assert_array_equal(trace["x_final"], x)
    np.testing.assert_array_equal(trace["reset"], [False, True, True, True, True])
    np.testing.assert_array_equal(trace["cap"], trace["reset"])
    assert np.all(trace["global_power"] < 0)  # measured before the velocity was zeroed
    assert record["settings"]["h"] == np.sqrt(eta)
    assert record["numerical_gradients"] == 8


def test_parameterized_momentum_and_random_resets():
    problem = make_problem("linear", "common", source="generated", dimension=4, mu=0.1, L=3.0)
    eta, mu, seed = 0.15, 1.45, 489
    trace, _ = run_benchmark(problem, "AGD", gradient_budget=2, eta=eta, supplied_mu=mu)
    first = problem.x0 - eta * (problem.A @ problem.x0)
    theta = (1 - np.sqrt(eta * mu)) / (1 + np.sqrt(eta * mu))
    y = first + theta * (first - problem.x0)
    np.testing.assert_array_equal(trace["x_final"], y - eta * (problem.A @ y))
    trace, _ = run_benchmark(
        problem, "RHGD", gradient_budget=30, eta=eta, supplied_mu=mu, seed=seed
    )
    expected = np.random.default_rng(seed).random(15) < np.sqrt(mu) * np.sqrt(eta)
    np.testing.assert_array_equal(trace["reset"][1:], expected)
    assert expected.any() and not expected.all()


def test_first_sustained_rejected_and_failed_work():
    problem = make_problem("linear", "common", source="generated", dimension=2, mu=1.0, L=1.0)
    problem = replace(problem, A=np.eye(2), x0=np.array([2.0, 0.0]))

    def prepare(oracle, start, settings):
        def step(x, k):
            oracle.grad(x)
            oracle.loss(x)
            if k == 4:
                raise FloatingPointError("trial failed")
            trial = np.array([(0.5, 2.0, 0.5, 0.5)[k], 0.0])
            return Step(trial, trial, accepted=k != 3)

        return step

    method = Method("test adapter", prepare, 1)
    settings = dict(eta=1.0, supplied_mu=None, targets=[1.0, 0.1])
    trace, complete = run_benchmark(problem, method, gradient_budget=4, **settings)
    np.testing.assert_array_equal(trace["loss"], [2, 0.125, 2, 0.125, 0.125])
    np.testing.assert_array_equal(trace["best_loss"], [2, 0.125, 0.125, 0.125, 0.125])
    np.testing.assert_array_equal(trace["objectives"], [1, 3, 5, 7, 9])
    assert complete["crossings"] == [
        {
            "target": 1.0,
            "first": {"iteration": 1, "gradients": 1},
            "sustained": {"iteration": 3, "gradients": 3},
        },
        {"target": 0.1, "first": None, "sustained": None},
    ]
    assert complete["rejected_updates"] == 1
    trace, failed = run_benchmark(problem, method, gradient_budget=5, **settings)
    assert failed["status"] == "failure" and failed["failure"] == "trial failed"
    assert failed["attempted_updates"] == 5 and failed["updates"] == 4
    assert failed["crossings"][0]["first"] == complete["crossings"][0]["first"]
    assert failed["crossings"][0]["sustained"] is None
    assert failed["numerical_gradients"] == 5 and failed["literal_gradient_requests"] == 5
    assert failed["objectives"] == 10 and failed["diagnostic_objectives"] == 5
    assert (failed["charged_unfinished_gradients"], failed["charged_unfinished_objectives"]) == (
        1,
        1,
    )


def test_zero_update_and_nonfinite_endpoint():
    problem = make_problem("linear", "equal", source="generated", dimension=2, mu=1.0, L=2.0)
    kwargs = dict(eta=1e250, supplied_mu=1.0, targets=[2.0])
    trace, record = run_benchmark(problem, "RHGD", seed=1, gradient_budget=1, **kwargs)
    np.testing.assert_array_equal(trace["gradients"], [0])
    assert record["crossings"][0]["sustained"] == {"iteration": 0, "gradients": 0}
    trace, record = run_benchmark(problem, "AGD", gradient_budget=8, **kwargs)
    assert record["status"] == "failure" and len(trace["loss"]) == 1
    assert record["charged_unfinished_gradients"] == record["charged_unfinished_objectives"] == 1
    assert record["crossings"][0]["sustained"] is None


def test_randomized_methods_require_seed():
    problem = make_problem("linear", "common")
    with pytest.raises(ValueError, match="seed"):
        run_benchmark(problem, "CAGD", gradient_budget=2, eta=0.002, supplied_mu=5e-5)

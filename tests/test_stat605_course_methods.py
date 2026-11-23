"""Adapter parity and evaluation-boundary checks for the approved final study."""

import numpy as np
import pytest

from stat605.agd import quadratic_oracle, run_agd
from stat605.benchmark import run_benchmark
from stat605.course_methods import NormalizedReset
from stat605.problems import make_problem
from stat605.rcm import rcm


@pytest.fixture
def case():
    return make_problem("log", "scaled_common", source="generated", dimension=4, mu=0.1, L=5)


@pytest.mark.parametrize(
    "name,rule", [("FREE_AGD", "none"), ("FUNCTION_AGD", "function"), ("GRADIENT_AGD", "gradient")]
)
def test_agd_parity(case, name, rule):
    actual, rec = run_benchmark(case, name, gradient_budget=80, eta=0.2, supplied_mu=None)
    expected, _ = run_agd(quadratic_oracle(case.A), case.x0, 0.2, 80, restart=rule)
    np.testing.assert_array_equal(actual["loss"], expected["f"])
    np.testing.assert_array_equal(actual["x_final"], expected["x_final"])
    assert rec["objectives"] == rec["controller_objectives"] + rec["diagnostic_objectives"]


@pytest.mark.parametrize("rule", ["kin", "mmd-r", "mmd-dr"])
def test_rcm_parity_and_budget(case, rule):
    expected = list(rcm(lambda x: case.A @ x, case.x0, np.sqrt(0.2), 80, rule))
    budget = expected[-1].gradient_calls
    actual, rec = run_benchmark(
        case, "RCM_" + rule, gradient_budget=budget, eta=0.2, supplied_mu=None
    )
    np.testing.assert_array_equal(actual["x_final"], expected[-1].x)
    assert rec["numerical_gradients"] == budget
    assert rec["updates"] == 80
    for budget in range(5):
        _, rec = run_benchmark(
            case, "RCM_" + rule, gradient_budget=budget, eta=0.2, supplied_mu=None
        )
        assert rec["numerical_gradients"] <= budget
        assert rec["status"] == "budget_complete"


def test_zero_beta_is_power(case):
    a, ra = run_benchmark(case, "B", gradient_budget=200, eta=0.2, supplied_mu=None, cap=7)
    b, rb = run_benchmark(
        case,
        "ENDPOINT_RHGD",
        gradient_budget=200,
        eta=0.2,
        supplied_mu=None,
        cap=7,
        parameters={"beta": 0},
    )
    for key in ("loss", "reset", "event", "cap", "x_final"):
        np.testing.assert_array_equal(a[key], b[key])
    assert ra["numerical_gradients"] == rb["numerical_gradients"]


def test_normalization_boundaries():
    c = NormalizedReset("endpoint", 1, 5)
    assert not c.observe(0, 0, 1)[0]
    assert not c.observe(-1, 0, 1)[0]
    assert c.observe(0, 0, 1)[0]
    assert c.age == 0 and not c.armed
    c = NormalizedReset("kinetic", 0, 5)
    assert not c.observe(0, 0, 1)[0]
    assert not c.observe(0, 1, 1)[0]
    assert not c.observe(0, 1, 1)[0]
    assert c.observe(0, 0.5, 1)[0]
    with pytest.raises(FloatingPointError):
        c.observe(np.inf, 1, 1)


def test_scalar_formulations_differ():
    # Actual scalar RHGD map, not an invented sequence of signals.
    from stat605.problems import QuadraticProblem

    p = QuadraticProblem(np.eye(1), np.ones(1), np.eye(1), np.ones(1), 1, 1)
    resets = []
    for method in ("ENDPOINT_RHGD", "KINETIC_RHGD"):
        trace, _ = run_benchmark(
            p, method, gradient_budget=100, eta=0.002, supplied_mu=None, parameters={"beta": 1}
        )
        resets.append(np.flatnonzero(trace["reset"])[0])
    assert resets[0] != resets[1]


@pytest.mark.parametrize("name", ["ENDPOINT_RHGD", "KINETIC_RHGD"])
def test_stationary_cap(case, name):
    from dataclasses import replace

    trace, rec = run_benchmark(
        replace(case, x0=np.zeros(4)), name, gradient_budget=20, eta=0.2, supplied_mu=None, cap=3
    )
    assert rec["reset_count"] == 3
    assert trace["cap"][[3, 6, 9]].all()
    assert not trace["event"].any()


def test_rcm_discarded_trial_at_budget_boundary(case):
    trace, rec = run_benchmark(case, "RCM_mmd-dr", gradient_budget=3, eta=0.2, supplied_mu=None)
    assert rec["numerical_gradients"] == 3
    assert rec["budget_exhausted_during_trial"]
    assert rec["charged_unfinished_gradients"] == 1
    assert rec["rejected_trials"] == 1
    assert trace["gradients"][0] == 1  # Initialization is paid.


@pytest.mark.parametrize("name", ["ENDPOINT_RHGD", "KINETIC_RHGD"])
def test_nonfinite_velocity_cannot_be_hidden_by_reset(case, name, monkeypatch):
    from stat605.course_methods import FROZEN_B

    def trial(oracle, x, v, h):
        oracle.grad(x)
        endpoint = x.copy()
        g = oracle.grad(endpoint)
        return endpoint, np.full_like(v, np.inf), g, h, True

    monkeypatch.setattr(FROZEN_B, "rhgd_step", trial)
    _, rec = run_benchmark(case, name, gradient_budget=20, eta=0.2, supplied_mu=None, cap=1)
    assert rec["status"] == "failure"
    assert rec["reset_count"] == 0


@pytest.mark.parametrize("period", [1, 7])
def test_fixed_adapter_matches_public_runner(case, period):
    from stat605.rhgd import run_fixed_time_quadratic

    trace, rec = run_benchmark(
        case,
        "FIXED_RHGD",
        gradient_budget=129,
        eta=0.2,
        supplied_mu=None,
        parameters={"period_steps": period},
    )
    expected, old = run_fixed_time_quadratic(
        case.A, case.x0, h=np.sqrt(0.2), period_steps=period, gradient_budget=129
    )
    np.testing.assert_array_equal(trace["loss"], expected["f"])
    np.testing.assert_array_equal(trace["reset"][1:], expected["reset"])
    np.testing.assert_array_equal(trace["x_final"], expected["x_final"])
    assert rec["numerical_gradients"] == old["numerical_gradients"] == 128

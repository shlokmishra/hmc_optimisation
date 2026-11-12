import inspect

import numpy as np
import pytest

from power_reset_spectral_comparison.core import FROZEN_B, Oracle, ar_step, run


def test_uniform_cache_counts_and_reset():
    o = Oracle(np.eye(2))
    x = np.array([1.0, 2.0])
    o.begin()
    g = o.grad(x)
    assert o.grad(x) is g
    assert (o.literal, o.numerical, o.hits) == (2, 1, 1)
    o.begin()
    o.grad(x)
    assert o.numerical == 2
    # Distinct stage arguments stay charged, even if they coincide at the floor.
    o.grad(x.copy())
    assert o.numerical == 3


def test_ar_first_two_steps_and_strict_boundary():
    o = Oracle(np.array([[1.0]]))
    x = np.array([1.0])
    u = x.copy()
    t = 1.0
    xp, up, tp, event, P = ar_step(o, x, u, t, 0.1)
    np.testing.assert_array_equal(xp, np.array([0.9]))
    np.testing.assert_array_equal(up, xp)
    assert tp == pytest.approx((1 + np.sqrt(5)) / 2) and not event and P < 0
    xp2, up2, tp2, event2, _ = ar_step(o, xp, up, tp, 0.1)
    np.testing.assert_allclose(up2, xp2 + (tp - 1) / tp2 * (xp2 - xp), rtol=0, atol=0)
    assert not event2
    zero = np.zeros(1)
    _, _, tzero, eventzero, pzero = ar_step(o, zero, zero, 3.0, 0.1)
    assert pzero == 0 and not eventzero and tzero > 3
    assert "alpha" not in inspect.signature(ar_step).parameters


def test_ar_positive_test_retains_new_endpoint():
    o = Oracle(np.array([[1.0]]))
    xp, up, t, event, P = ar_step(o, np.zeros(1), np.ones(1), 4.0, 0.1)
    assert event and P > 0 and t == 1
    np.testing.assert_array_equal(xp, np.array([0.9]))
    np.testing.assert_array_equal(up, xp)


@pytest.mark.parametrize("method", ["B", "AR_AGD", "AGD", "CAGD", "RHGD"])
def test_hand_counters_repeat_and_cache_equivalence(method):
    A = np.diag([0.5, 5.0, 500.0])
    x = np.ones(3)
    seed = 31 if method in ("CAGD", "RHGD") else None
    args = dict(
        A=A,
        x0=x,
        method=method,
        budget=80,
        seed=seed,
        max_updates=20,
        detailed=True,
        basis=np.eye(3),
        eigenvalues=np.diag(A),
        keep_states=True,
    )
    out, m = run(**args)
    literal, literal_meta = run(**args, cached=False)
    np.testing.assert_array_equal(out["x"], literal["x"])
    assert m["numerical_gradients"] == 20 * (2 if method in ("B", "RHGD") else 1)
    assert literal_meta["literal_gradient_requests"] == 20 * (
        2 if method in ("B", "RHGD", "CAGD") else 1
    )
    assert m["objectives"] == 21
    assert m["controller_dots"] == (20 if method in ("B", "AR_AGD") else 0)
    repeated, _ = run(**args)
    np.testing.assert_array_equal(out["f"], repeated["f"])


def test_frozen_b_event_and_budget():
    A = np.diag([1.0, 500.0])
    x = np.array([1.0, 0.0])
    out, m = run(A, x, "B", budget=301, detailed=True, basis=np.eye(2), eigenvalues=np.diag(A))
    prior, _ = FROZEN_B.run(FROZEN_B.Problem(A, x), "exact", "B", 301, diagnostic=True)
    np.testing.assert_array_equal(out["f"], prior["f"])
    np.testing.assert_array_equal(out["event"], prior["event"])
    assert m["numerical_gradients"] == 300
    assert np.any(out["event"])


def test_nonfinite_is_explicit_failure():
    out, m = run(np.array([[np.inf]]), np.ones(1), "B", budget=10)
    assert m["status"] == "failure" and m["updates"] == 0
    assert m["numerical_gradients"] == 2
    assert len(out["f"]) == 1


def test_current_sustained_and_censoring():
    from power_reset_spectral_comparison.analysis import crossings, margin_check

    f = np.array([4.0, 0.4, 2.0, 0.2, 0.1])
    assert crossings(f, 1.0) == {"first": 1, "sustained": 3}
    assert crossings(f, 1.0, successful=False) == {"first": 1, "sustained": None}
    assert crossings(f, 0.01) == {"first": None, "sustained": None}
    assert margin_check(100, None, 200, 0.8)["pass"]
    assert not margin_check(180, None, 200, 0.8)["pass"]
    assert not margin_check(None, 200, 200, 0.8)["pass"]


@pytest.mark.parametrize("s", [1e-4, 0.01, 0.1, 0.25])
def test_theory_modal_formula_and_crossing(s):
    # Checks support the written algebra; these are not new optimizer comparisons.
    a = 1 - s
    matrix = np.array([[a, np.sqrt(s) * a], [-np.sqrt(s) * a, 1 - s * a]])
    dissipation = np.array([[s * (1 + s - s * s), s**2.5 * a], [s**2.5 * a, s * a * (1 + s * s)]])
    np.testing.assert_allclose(np.eye(2) - matrix.T @ matrix, dissipation, atol=2e-16)
    theta = np.arccos((2 * a + s * s) / (2 * np.sqrt(a)))
    beta = s * s / (2 * np.sqrt(a) * np.sin(theta))
    k = int(np.ceil((np.pi / 2 - np.arctan(beta)) / theta))
    for j in (1, k - 1, k):
        qp = np.linalg.matrix_power(matrix, j) @ np.array([1.0, 0.0])
        exact = a ** (j / 2) * (np.cos(j * theta) - beta * np.sin(j * theta))
        np.testing.assert_allclose(qp[0], exact, atol=5e-12)
        assert (qp[0] * qp[1] < 0) if j < k else (qp[0] * qp[1] >= 0)
    assert qp[0] ** 2 <= s * a
    assert k <= np.pi / np.sqrt(2 * s) + 1

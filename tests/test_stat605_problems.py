import numpy as np
import pytest

from stat605.problems import FIXTURES, SPECTRA, make_problem


@pytest.mark.parametrize("spectrum,fixture", [("linear", "paper"), ("log", "log")])
def test_exact_historical_matrix_and_start(spectrum, fixture):
    problem = make_problem(spectrum, "common")
    with np.load(FIXTURES / f"quadratic_{fixture}.npz", allow_pickle=False) as original:
        for key, actual in [
            ("A", problem.A),
            ("x0", problem.x0),
            ("eigenvalues", problem.eigenvalues),
        ]:
            assert actual.dtype == np.dtype("float64")
            np.testing.assert_array_equal(actual, original[key])
    with np.load(FIXTURES / "quadratic_paper.npz", allow_pickle=False) as paper:
        np.testing.assert_array_equal(problem.basis, paper["basis"])
    checks = problem.spectral_checks()
    assert abs(checks["represented_min_minus_mu"]) < 1e-12
    assert abs(checks["represented_max_minus_L"]) < 5e-12
    assert checks["reconstruction_max_abs"] < 2e-12
    assert checks["orthogonality_max_abs"] < 1e-13


def test_seeded_case_matches_basis_and_start_across_spectra():
    options = dict(source="generated", dimension=7, mu=0.01, L=np.float32(5), problem_seed=413)
    linear, log, clusters = [make_problem(s, "common", **options) for s in SPECTRA]
    for p in (linear, log, clusters):
        assert all(a.dtype == np.float64 for a in (p.A, p.x0, p.basis, p.eigenvalues))
        np.testing.assert_array_equal(p.basis, linear.basis)
        np.testing.assert_array_equal(p.x0, linear.x0)
        np.testing.assert_array_equal(p.eigenvalues[[0, -1]], [options["mu"], options["L"]])
        np.testing.assert_allclose(np.linalg.eigvalsh(p.A), p.eigenvalues)
    np.testing.assert_allclose(np.diff(linear.eigenvalues), (5.0 - 0.01) / 6)
    np.testing.assert_allclose(np.diff(np.log(log.eigenvalues)), np.log(500) / 6)
    log_positions = np.log(clusters.eigenvalues / 0.01) / np.log(500.0)
    np.testing.assert_allclose(log_positions, [0, 1 / 30, 2 / 30, 0.1, 0.9, 0.95, 1])
    different_seed = make_problem("linear", "common", **(options | {"problem_seed": 414}))
    assert not np.array_equal(different_seed.basis, linear.basis)
    assert not np.array_equal(different_seed.x0, linear.x0)


@pytest.mark.parametrize("dimension,positions", [(2, [0, 1]), (3, [0, 0.1, 1])])
def test_cluster_singletons_preserve_both_endpoints(dimension, positions):
    p = make_problem("clustered", "common", source="generated", dimension=dimension, mu=1, L=10)
    np.testing.assert_allclose(np.log10(p.eigenvalues), positions)


@pytest.mark.parametrize("spectrum", SPECTRA)
def test_energy_control_total_distribution_and_signs(spectrum):
    common = make_problem(spectrum, "common")
    equal = make_problem(spectrum, "equal", total_energy=3.5)
    scaled = make_problem(spectrum, "scaled_common", total_energy=3.5)
    initial_allocation = common.modal_energy(common.x0)
    for p in (equal, scaled):
        assert 0.5 * p.x0 @ p.A @ p.x0 == pytest.approx(3.5, rel=1e-9)
        np.testing.assert_array_equal(
            np.sign(p.basis.T @ p.x0), np.sign(common.basis.T @ common.x0)
        )
    np.testing.assert_allclose(equal.modal_energy(equal.x0), np.full(100, 3.5 / 100), rtol=1e-9)
    np.testing.assert_allclose(
        scaled.modal_energy(scaled.x0) / 3.5, initial_allocation / initial_allocation.sum()
    )


def test_actual_modal_power_and_energy_reconstruct_endpoint_quantities():
    p = make_problem("log", "common", dimension=8, source="generated", problem_seed=17)
    x = np.linspace(-2, 3, 8)
    v = np.arange(-4, 4, dtype=np.float64)
    g = p.A @ x
    np.testing.assert_allclose(p.modal_energy(x).sum(), 0.5 * x @ p.A @ x)
    contributions = p.modal_power(g, v)
    np.testing.assert_allclose(contributions.sum(), np.dot(g, v))
    np.testing.assert_allclose(contributions, [np.dot(q, g) * np.dot(q, v) for q in p.basis.T])


@pytest.mark.parametrize(
    "options",
    [
        {"spectrum": "dense"},
        {"start": "ones"},
        {"source": "random"},
        {"dimension": 6},  # Fixture dimensions cannot be changed.
        {"problem_seed": 1},
        {"source": "generated", "dimension": 1},
        {"source": "generated", "dimension": 2.5},
        {"source": "generated", "problem_seed": None},
        {"source": "generated", "problem_seed": -3},
        {"source": "generated", "mu": 0},
        {"source": "generated", "mu": 501},
        {"source": "generated", "L": np.inf},
        {"total_energy": np.nan},
        {"total_energy": 0},
    ],
)
def test_invalid_design_raises(options):
    with pytest.raises(ValueError):
        make_problem(**({"spectrum": "linear", "start": "equal"} | options))

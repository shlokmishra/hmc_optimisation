"""Matched positive-definite quadratics for the STAT 605 spectral study."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

FIXTURES = Path(__file__).resolve().parents[2] / "configs/stat605/fixtures"
SPECTRA = ("linear", "log", "clustered")
STARTS = ("common", "scaled_common", "equal")


@dataclass(frozen=True)
class QuadraticProblem:
    """Columns of basis are ordered by increasing curvature. The minimum is zero."""

    A: np.ndarray
    x0: np.ndarray
    basis: np.ndarray
    eigenvalues: np.ndarray
    mu: float
    L: float

    def modal_energy(self, x):
        """Potential energy carried by each mode at position x."""
        return 0.5 * self.eigenvalues * (self.basis.T @ x) ** 2

    def modal_power(self, endpoint_gradient, pre_reset_velocity):
        """Decompose the actual endpoint restart dot product without another gradient."""
        return (self.basis.T @ endpoint_gradient) * (self.basis.T @ pre_reset_velocity)

    def spectral_checks(self):
        """Measure roundoff on the optimization matrix without modifying it."""
        represented = np.linalg.eigvalsh((self.A + self.A.T) / 2)
        reconstruction = (self.basis * self.eigenvalues) @ self.basis.T
        return {
            "represented_min": float(represented[0]),
            "represented_max": float(represented[-1]),
            "represented_min_minus_mu": float(represented[0] - self.mu),
            "represented_max_minus_L": float(represented[-1] - self.L),
            "symmetry_max_abs": float(np.max(np.abs(self.A - self.A.T))),
            "orthogonality_max_abs": float(
                np.max(np.abs(self.basis.T @ self.basis - np.eye(len(represented))))
            ),
            "reconstruction_max_abs": float(np.max(np.abs(reconstruction - self.A))),
        }


def _spectrum(name, dimension, mu, L):
    if name == "linear":
        return np.linspace(mu, L, dimension)
    if name == "log":
        return np.geomspace(mu, L, dimension)
    # Place the lower ceil(d/2) modes and upper floor(d/2) modes in the outer
    # tenths of the log-curvature interval. A singleton keeps its exterior endpoint.
    boundaries = np.geomspace(mu, L, 11)
    fast_count = dimension // 2
    slow = np.geomspace(mu, boundaries[1], dimension - fast_count)
    fast = np.geomspace(L, boundaries[-2], fast_count)[::-1]
    return np.concatenate((slow, fast))


def make_problem(
    spectrum,
    start,
    *,
    source="fixture",
    dimension=100,
    mu=5e-5,
    L=500.0,
    problem_seed=0,
    total_energy=1.0,
):
    """Build one case with the same basis and common start across all spectra.

    For source="fixture", linear and log use the archived optimization matrices
    byte for byte. The linear fixture's basis was the construction basis of the
    archived log matrix. For source="generated", reuse the same problem_seed
    across cases to match a Gaussian QR basis and a Gaussian starting point.

    "common" leaves that point unchanged. "scaled_common" preserves its modal
    proportions and "equal" preserves its modal signs and allocates energy equally.
    Both controlled starts have initial objective total_energy up to roundoff.
    """
    if spectrum not in SPECTRA or start not in STARTS:
        raise ValueError(f"Choose a spectrum in {SPECTRA} and a start in {STARTS}")
    if isinstance(dimension, bool) or not isinstance(dimension, (int, np.integer)) or dimension < 2:
        raise ValueError("dimension must be an integer of at least two")
    mu, L, total_energy = float(mu), float(L), float(total_energy)
    if not np.isfinite([mu, L, total_energy]).all() or not 0 < mu <= L or total_energy <= 0:
        raise ValueError("Require finite 0 < mu <= L and positive finite total_energy")
    if source == "fixture":
        if (dimension, mu, L) != (100, 5e-5, 500.0) or problem_seed not in (None, 0):
            raise ValueError("Fixture cases use d=100, mu=5e-5, L=500 and no problem randomness")
        with np.load(FIXTURES / "quadratic_paper.npz", allow_pickle=False) as paper:
            basis, common = paper["basis"], paper["x0"]
            if spectrum == "linear":
                A, eigenvalues = paper["A"], paper["eigenvalues"]
        if spectrum == "log":
            with np.load(FIXTURES / "quadratic_log.npz", allow_pickle=False) as log:
                A, eigenvalues = log["A"], log["eigenvalues"]
    elif source == "generated":
        if (
            isinstance(problem_seed, bool)
            or not isinstance(problem_seed, (int, np.integer))
            or problem_seed < 0
        ):
            raise ValueError("Generated cases require a nonnegative integer problem_seed")
        rng = np.random.default_rng(problem_seed)
        basis, upper = np.linalg.qr(rng.standard_normal((dimension, dimension)))
        basis *= np.where(np.diag(upper) < 0, -1.0, 1.0)
        common = rng.standard_normal(dimension)
    else:
        raise ValueError("source must be 'fixture' or 'generated'")

    if source == "generated" or spectrum == "clustered":
        eigenvalues = _spectrum(spectrum, dimension, mu, L)
        A = (basis * eigenvalues) @ basis.T

    x0 = common
    if start == "scaled_common":
        x0 = common * np.sqrt(total_energy / (0.5 * common @ A @ common))
    elif start == "equal":
        signs = np.where(basis.T @ common < 0, -1.0, 1.0)
        x0 = basis @ (signs * np.sqrt((2.0 * total_energy / dimension) / eigenvalues))
    return QuadraticProblem(A, x0, basis, eigenvalues, mu, L)

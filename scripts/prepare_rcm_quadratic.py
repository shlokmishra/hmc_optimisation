"""Prepare the quadratic problem from Scagliotti & Colli Franzone, Section 5.1."""

import argparse
from pathlib import Path

import numpy as np

SEED = 605
DIMENSION = 1000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New input .npz file")
    output = parser.parse_args().output
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing fixture: {output}")
    rng = np.random.default_rng(SEED)

    # Work in the eigenbasis of A. Then A @ x equals eigenvalues * x.
    eigenvalues = rng.uniform(0.03, 15.0, size=DIMENSION)
    b = rng.standard_normal(DIMENSION)

    x0 = np.zeros(DIMENSION)
    v0 = np.zeros(DIMENSION)
    h = 1.0 / np.sqrt(eigenvalues.max())

    # f(x) = 0.5 * x.T @ A @ x + b.T @ x
    # At the minimizer, A @ x_star + b = 0.
    x_star = -b / eigenvalues
    f_star = 0.5 * np.dot(b, x_star)

    grad_at_start = eigenvalues * x0 + b
    grad_at_minimum = eigenvalues * x_star + b
    np.testing.assert_allclose(grad_at_start, b)
    np.testing.assert_allclose(grad_at_minimum, 0.0, atol=1e-12)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        np.savez_compressed(
            stream,
            eigenvalues=eigenvalues,
            b=b,
            x0=x0,
            v0=v0,
            h=h,
            x_star=x_star,
            f_star=f_star,
            seed=SEED,
        )

    print(f"Saved: {output}")
    print(f"Dimension: {DIMENSION}")
    print(f"Sampled eigenvalue range: [{eigenvalues.min():.6f}, {eigenvalues.max():.6f}]")
    print(f"RCM time step h: {h:.10f}")
    print(f"Initial gradient norm: {np.linalg.norm(grad_at_start):.8f}")
    print(f"Gradient norm at the exact minimizer: {np.linalg.norm(grad_at_minimum):.3e}")


if __name__ == "__main__":
    main()

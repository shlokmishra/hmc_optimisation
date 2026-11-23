"""Prepare the quadratic problem from Scagliotti & Colli Franzone, Section 5.1."""

'''

We selected the smooth quadratic experiment in Scagliotti and Colli Franzone, §5.1, Figure 2 (upper-right panel). Following the paper, we used \(f(x)=\tfrac12x^\top A x+b^\top x\) in dimension 1,000, sampled the eigenvalues uniformly on \([0.03,15]\), drew \(b\sim\mathcal N(0,I)\), and set \(h=1/\sqrt{\lambda_{\max}(A)}\). For our replication, we used NumPy seed 605, represented \(A\) in its eigenbasis, and chose \(x_0=0\), with the paper’s zero initial velocity. The sampled eigenvalues ranged from 0.033267 to 14.947854, giving \(h=0.2586488664\). The script scripts/prepare_rcm_quadratic.py generated configs/stat605/fixtures/rcm_section5_1_seed605.npz. Our replication target is the gradient norm versus iteration for RCM-kin, RCM-mmd-r, and RCM-mmd-dr over 300 iterations.

'''

from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = PROJECT_ROOT / "configs" / "stat605" / "fixtures"
SEED = 605
DIMENSION = 1000


def main():
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

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    output = FIXTURE_DIR / f"rcm_section5_1_seed{SEED}.npz"
    np.savez_compressed(
        output,
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
    print(f"Sampled eigenvalue range: [{eigenvalues.min():.6f}, "
          f"{eigenvalues.max():.6f}]")
    print(f"RCM time step h: {h:.10f}")
    print(f"Initial gradient norm: {np.linalg.norm(grad_at_start):.8f}")
    print(f"Gradient norm at the exact minimizer: "
          f"{np.linalg.norm(grad_at_minimum):.3e}")


if __name__ == "__main__":
    main()
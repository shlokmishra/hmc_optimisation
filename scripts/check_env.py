"""Check the actual numerical runtime and save a small environment snapshot."""

import importlib
import importlib.metadata
import json
import os
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import solve
from scipy.optimize import minimize
from threadpoolctl import threadpool_info


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    if Path(sys.prefix).resolve() != root / ".venv":
        raise RuntimeError("Activate this project's .venv before running this check.")
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError(f"Expected Python 3.13, found {platform.python_version()}.")

    # Exercise compiled NumPy/SciPy code and an optimizer with a known solution.
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float64)
    rhs = np.array([1.0, 2.0], dtype=np.float64)
    optimum = solve(matrix, rhs, assume_a="pos")
    np.testing.assert_allclose(matrix @ optimum, rhs, atol=1e-14, rtol=1e-14)
    result = minimize(
        lambda x: 0.5 * x @ matrix @ x - rhs @ x,
        np.zeros(2, dtype=np.float64),
        jac=lambda x: matrix @ x - rhs,
        method="BFGS",
        options={"gtol": 1e-10},
    )
    if not result.success:
        raise RuntimeError(result.message)
    np.testing.assert_allclose(result.x, optimum, atol=1e-9, rtol=1e-9)

    for module in ("pandas", "yaml", "tqdm", "pytest", "ipykernel"):
        importlib.import_module(module)
    pools = threadpool_info()
    if not pools or any(pool["num_threads"] != 1 for pool in pools):
        raise RuntimeError(f"Expected one thread per numerical runtime: {pools}")

    output = root / "tmp"
    output.mkdir(exist_ok=True)
    figure, axes = plt.subplots(figsize=(4, 3))
    axes.plot([0, 1, 2], [1, 0.25, 0.0625], marker="o")
    axes.set(xlabel="Smoke-check index", ylabel="Example value", title="Environment check")
    figure.tight_layout()
    figure.savefig(output / "environment-check.png", dpi=100)
    plt.close(figure)

    distributions = (
        "pip",
        "numpy",
        "scipy",
        "matplotlib",
        "pandas",
        "PyYAML",
        "tqdm",
        "threadpoolctl",
        "pytest",
        "ruff",
        "ipykernel",
    )
    snapshot = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "executable": sys.executable,
        "platform": platform.platform(),
        "modules": os.environ.get("LOADEDMODULES", "").split(":"),
        "packages": {name: importlib.metadata.version(name) for name in distributions},
        "threadpools": pools,
        "checks": ["float64 linear solve", "quadratic optimizer", "imports", "plot rendering"],
    }
    (output / "environment.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    print("Environment checks passed: float64 solve, optimizer, imports, plot, one BLAS thread.")
    print(f"Snapshot: {output / 'environment.json'}")


if __name__ == "__main__":
    main()
